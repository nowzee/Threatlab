"""
Module de gestion des agents honeypot et des données d'attaques.

Ce module fournit les fonctions pour créer et gérer les agents honeypot,
enregistrer les attaques, gérer les IPs malveillantes et générer des rapports.
"""
from typing import Optional, Tuple, Dict, List, Any
from module.database.db_manager import DatabaseManagerHoneypot
from datetime import datetime
import jwt
import os
import hashlib
from flask import current_app

def generate_jwt(agent_id: int) -> str:
    """
    Génère un JWT unique pour un agent spécifique.

    Args:
        agent_id (int): Identifiant de l'agent honeypot.

    Returns:
        str: Token JWT signé contenant l'ID de l'agent et un nonce.
    """
    secret_key = current_app.config.get('AGENT_SECRET_KEY') or current_app.config['SECRET_KEY']
    payload_to_encode = {
        'agent_id': agent_id,
        'nonce': os.urandom(16).hex()  # Add random nonce for uniqueness and replay protection
    }
    # Sign token with HS256 algorithm for agent authentication
    token = jwt.encode(payload_to_encode, secret_key, algorithm='HS256')
    return token


def create_agent_token(agent_name: str,
                       ip_address: str = "0.0.0.0",
                       country_name: Optional[str] = None,
                       service_type: str = "ssh",
                       banner: Optional[str] = None) -> Tuple[Optional[int], Optional[str]]:
    """
    Crée un enregistrement pour un nouvel agent honeypot et génère un token unique.

    Args:
        agent_name (str): Nom de l'agent honeypot.
        ip_address (str, optional): Adresse IP de l'agent. Par défaut "0.0.0.0".
        country_name (Optional[str], optional): Nom du pays où l'agent est déployé. Par défaut None.
        service_type (str, optional): Type de service simulé (ssh, smtp, ftp, etc.). Par défaut "ssh".
        banner (Optional[str], optional): Banner du service simulé. Par défaut None.

    Returns:
        Tuple[Optional[int], Optional[str]]: (agent_id, secret_token) si succès, sinon (None, None).
    """
    try:
        print(f"[DEBUG] Starting create_agent_token for: {agent_name}")
        with DatabaseManagerHoneypot() as db:
            db.execute("""
                INSERT INTO honey_agents (agent_name, ip_address, country_name, service_type, banner)
                VALUES (%s, %s, %s, %s, %s)
            """, (agent_name, ip_address, country_name, service_type, banner))

            # Step 2: Get the auto-generated ID of the newly inserted agent
            agent_id = db.cursor.lastrowid
            # Step 3: Generate JWT token using agent_id and hash it with SHA-256
            # We store the hash only for security, return plaintext token to agent
            secret_token = generate_jwt(agent_id)
            secret_token_sha256 = hashlib.sha256(secret_token.encode()).hexdigest()

            # Step 4: Update agent record with token hash for future authentication
            db.execute("""
                UPDATE honey_agents
                SET secret_token_sha256 = %s
                WHERE id = %s
            """, (secret_token_sha256, agent_id))

            print(f"Agent {agent_id} created with token {secret_token}")

            return agent_id, secret_token

    except Exception as e:
        import traceback
        print(f"[ERROR] Error creating agent token: {e}")
        print(f"[ERROR] Full traceback:")
        print(traceback.format_exc())
        return None, None

def add_malicious_ip_address(agent_id: int,
                            ip_address: str,
                            service_type: str,
                            country_name: Optional[str] = None,
                            country_code: Optional[str] = None,
                            classification: Optional[str] = None) -> bool:
    """
    Ajoute ou met à jour une IP malveillante avec ses relations normalisées.

    Gère l'enregistrement de l'IP, la relation IP-Agent et le compteur d'attaques IP-Service.

    Args:
        agent_id (int): Identifiant de l'agent honeypot.
        ip_address (str): Adresse IP malveillante.
        service_type (str): Type de service ciblé (ssh, smtp, ftp, etc.).
        country_name (Optional[str], optional): Nom du pays d'origine. Par défaut None.
        country_code (Optional[str], optional): Code pays (ISO). Par défaut None.
        classification (Optional[str], optional): Classification de la menace. Par défaut None.

    Returns:
        bool: True si l'opération a réussi, False sinon.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # Step 1: Check if IP already exists in malicious_ips table
            db.execute("SELECT id, total_attack_count FROM malicious_ips WHERE ip_address = %s", (ip_address,))
            existing_ip = db.fetchone()

            if existing_ip:
                ip_id = existing_ip['id']
                total_attack_count = existing_ip['total_attack_count']
                new_total_count = total_attack_count + 1

                db.execute("""UPDATE malicious_ips
                              SET last_seen          = CURRENT_TIMESTAMP,
                                  total_attack_count = %s,
                                  country_name       = COALESCE(%s, country_name),
                                  country_code       = COALESCE(%s, country_code),
                                  classification     = COALESCE(%s, classification)
                              WHERE id = %s""",
                           (new_total_count, country_name, country_code, classification, ip_id))
            else:
                # Insert nouvelle IP
                db.execute("""INSERT INTO malicious_ips
                                  (ip_address, country_name, country_code, classification)
                              VALUES (%s, %s, %s, %s)""",
                           (ip_address, country_name, country_code, classification))

                # Récupérer l'ID auto-généré
                db.execute("SELECT id FROM malicious_ips WHERE ip_address = %s", (ip_address,))
                ip_id = db.fetchone()['id']

            # Step 2: Update many-to-many relationship between IP and Agent
            _update_ip_agent_relation(db, ip_id, agent_id)

            # Step 3: Update attack counter for this IP-Service combination
            _update_ip_service_attacks(db, ip_id, service_type)

            return True
    except Exception as e:
        print(f"Error adding malicious IP address: {e}")
        return False

def _update_ip_agent_relation(db: DatabaseManagerHoneypot, ip_id: int, agent_id: int) -> None:
    """
    Met à jour la relation entre une IP et un agent (fonction helper).

    Args:
        db (DatabaseManagerHoneypot): Instance du gestionnaire de base de données.
        ip_id (int): Identifiant de l'IP malveillante.
        agent_id (int): Identifiant de l'agent honeypot.

    Raises:
        Exception: Si une erreur survient lors de la mise à jour.
    """
    try:
        # Check if this IP has already been seen by this specific agent
        db.execute("SELECT id, report_count FROM ip_agent_relations WHERE ip_id = %s AND agent_id = %s",
                  (ip_id, agent_id))
        existing_relation = db.fetchone()

        if existing_relation:
            # Relationship exists - increment counter to track frequency
            relation_id = existing_relation['id']
            report_count = existing_relation['report_count']
            new_report_count = report_count + 1
            db.execute("""UPDATE ip_agent_relations
                         SET last_seen = CURRENT_TIMESTAMP, report_count = %s
                         WHERE id = %s""",
                      (new_report_count, relation_id))
        else:
            # First time this IP has attacked this agent - create new relation
            db.execute("""INSERT INTO ip_agent_relations (ip_id, agent_id)
                         VALUES (%s, %s)""", (ip_id, agent_id))
    except Exception as e:
        print(f"Error updating IP-Agent relationship: {e}")
        raise

def _update_ip_service_attacks(db: DatabaseManagerHoneypot, ip_id: int, service_type: str) -> None:
    """
    Met à jour le compteur d'attaques IP-Service (fonction helper).

    Args:
        db (DatabaseManagerHoneypot): Instance du gestionnaire de base de données.
        ip_id (int): Identifiant de l'IP malveillante.
        service_type (str): Type de service ciblé.

    Raises:
        Exception: Si une erreur survient lors de la mise à jour.
    """
    try:
        # Check if this IP has targeted this service type before
        db.execute("SELECT id, attack_count FROM ip_service_attacks WHERE ip_id = %s AND service_type = %s",
                  (ip_id, service_type))
        existing_service = db.fetchone()

        if existing_service:
            # IP has attacked this service before - increment counter
            service_id = existing_service['id']
            attack_count = existing_service['attack_count']
            new_attack_count = attack_count + 1
            db.execute("""UPDATE ip_service_attacks
                         SET last_seen = CURRENT_TIMESTAMP, attack_count = %s
                         WHERE id = %s""",
                      (new_attack_count, service_id))
        else:
            # First time this IP targets this service type - create new record
            db.execute("""INSERT INTO ip_service_attacks (ip_id, service_type)
                         VALUES (%s, %s)""", (ip_id, service_type))
    except Exception as e:
        print(f"Error updating IP-Service attacks: {e}")
        raise

def add_compromised_credential(malicious_ip: str,
                              username: str,
                              password: str,
                              service_type: str) -> bool:
    """
    Ajoute ou met à jour des credentials compromis.

    Met également à jour les statistiques globales des usernames et passwords observés.

    Args:
        malicious_ip (str): Adresse IP malveillante.
        username (str): Nom d'utilisateur tenté.
        password (str): Mot de passe tenté.
        service_type (str): Type de service ciblé.

    Returns:
        bool: True si l'opération a réussi, False sinon.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # Lookup the IP ID from the malicious_ips table
            db.execute("SELECT id FROM malicious_ips WHERE ip_address = %s", (malicious_ip,))
            ip_record = db.fetchone()

            if not ip_record:
                print(f"Malicious IP {malicious_ip} not found in database")
                return False

            malicious_ip_id = ip_record['id']

            # Check if this exact credential pair has been tried by this IP before
            db.execute("""SELECT id, attempt_count FROM compromised_credentials
                         WHERE malicious_ip_id = %s AND service_type = %s AND username = %s AND password = %s""",
                      (malicious_ip_id, service_type, username, password))
            existing_credential = db.fetchone()

            if existing_credential:
                # Credential combination exists - increment attempt counter
                credential_id = existing_credential['id']
                attempt_count = existing_credential['attempt_count']
                new_attempt_count = attempt_count + 1
                db.execute("""UPDATE compromised_credentials
                             SET last_seen = CURRENT_TIMESTAMP, attempt_count = %s
                             WHERE id = %s""",
                          (new_attempt_count, credential_id))
            else:
                # New credential combination - insert with initial count of 1
                db.execute("""INSERT INTO compromised_credentials
                             (malicious_ip_id, service_type, username, password)
                             VALUES (%s, %s, %s, %s)""",
                          (malicious_ip_id, service_type, username, password))

            # Update global username statistics for analytics
            db.execute("SELECT id, count FROM username_viewed WHERE username = %s", (username,))
            username_record = db.fetchone()

            if username_record:
                username_id = username_record['id']
                count = username_record['count']
                db.execute("UPDATE username_viewed SET count = %s, last_seen = CURRENT_TIMESTAMP WHERE id = %s",
                          (count + 1, username_id))
            else:
                # First time seeing this username globally
                db.execute("INSERT INTO username_viewed (username) VALUES (%s)", (username,))

            # Update global password statistics for analytics
            db.execute("SELECT id, count FROM password_attempted WHERE password = %s", (password,))
            password_record = db.fetchone()

            if password_record:
                password_id = password_record['id']
                count = password_record['count']
                db.execute("UPDATE password_attempted SET count = %s, last_seen = CURRENT_TIMESTAMP WHERE id = %s",
                          (count + 1, password_id))
            else:
                # First time seeing this password globally
                db.execute("INSERT INTO password_attempted (password) VALUES (%s)", (password,))

            return True
    except Exception as e:
        print(f"Error adding compromised credential: {e}")
        return False

def add_attack_log(attack_data: Dict[str, Any]) -> bool:
    """
    Insère un log d'attaque dans la base de données avec l'horodatage actuel.

    Args:
        attack_data (Dict[str, Any]): Dictionnaire contenant les données de l'attaque:
            - agent_id: Identifiant de l'agent
            - source_ip: IP source de l'attaque
            - source_port: Port source
            - target_port: Port ciblé
            - service_type: Type de service
            - username_attempt: Tentative de username (optionnel)
            - password_attempt: Tentative de password (optionnel)
            - payload: Payload capturé (optionnel)
            - malware_hash: Hash du malware (optionnel)
            - classification: Type d'attaque (optionnel)
            - country_code: Code pays (optionnel)
            - country_name: Nom du pays (optionnel)

    Returns:
        bool: True si l'insertion a réussi, False sinon.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            now = datetime.now()

            db.execute("""INSERT INTO attack_logs
                         (created_at, agent_id, source_ip, source_port, target_port, service_type,
                          username_attempt, password_attempt, payload, malware_hash,
                          attack_type, country_code, country_name)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                      (now,
                       attack_data.get('agent_id'),
                       attack_data.get('source_ip'),
                       attack_data.get('source_port'),
                       attack_data.get('target_port'),
                       attack_data.get('service_type'),
                       attack_data.get('username_attempt'),
                       attack_data.get('password_attempt'),
                       attack_data.get('payload'),
                       attack_data.get('malware_hash'),
                       attack_data.get('classification'),
                       attack_data.get('country_code'),
                       attack_data.get('country_name')))
            return True
    except Exception as e:
        print(f"Error adding attack log: {e}")
        return False

def add_smtp_interaction(malicious_ip: str,
                        sender_email: str,
                        recipient_email: str,
                        subject: str,
                        message_content: str,
                        attachments: Optional[List[str]] = None) -> bool:
    """
    Insère une interaction SMTP dans la base de données.

    Args:
        malicious_ip (str): Adresse IP du serveur malveillant.
        sender_email (str): Email de l'expéditeur.
        recipient_email (str): Email du destinataire.
        subject (str): Sujet de l'email.
        message_content (str): Contenu du message.
        attachments (Optional[List[str]], optional): Liste des pièces jointes. Par défaut None.

    Returns:
        bool: True si l'insertion a réussi, False sinon.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # Get malicious IP ID
            db.execute("SELECT id FROM malicious_ips WHERE ip_address = %s", (malicious_ip,))
            ip_record = db.fetchone()

            if not ip_record:
                print(f"Malicious IP {malicious_ip} not found in database")
                return False

            malicious_ip_id = ip_record['id']

            # Insert SMTP interaction
            import json
            attachments_json = json.dumps(attachments) if attachments else None

            db.execute("""INSERT INTO smtp_interactions
                         (malicious_server_ip_id, sender_email, recipient_email, subject,
                          message_content, attachments)
                         VALUES (%s, %s, %s, %s, %s, %s)""",
                      (malicious_ip_id, sender_email, recipient_email, subject,
                       message_content, attachments_json))
            return True
    except Exception as e:
        print(f"Error adding SMTP interaction: {e}")
        return False

def get_default_metric_data() -> Dict[str, int]:
    """
    Récupère les métriques par défaut du dashboard.

    Returns:
        Dict[str, int]: Dictionnaire contenant:
            - ip_count: Nombre d'IPs malveillantes uniques
            - Sample_downloaded: Nombre de samples/payloads uniques
            - tentative_access: Nombre total de tentatives d'accès
            - number_agents: Nombre d'agents honeypot actifs
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT (SELECT COUNT(id) FROM malicious_ips) AS ip_count,
                          (SELECT COUNT(id) FROM payloads)      AS Sample_downloaded,
                          (SELECT COUNT(id) FROM honey_agents)  AS number_honeypot,
                          (SELECT COUNT(id) FROM attack_logs)   AS tentative_access
                   ''')

        result = db.fetchone()
        return result


def get_agent_details() -> List[Dict[str, Any]]:
    """
    Récupère les détails des 5 derniers logs d'attaques avec informations des agents.

    Returns:
        List[Dict[str, Any]]: Liste de dictionnaires contenant les informations des logs.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT al.country_name,
                          al.source_ip,
                          al.target_port,
                          al.service_type,
                          al.agent_id,
                          ha.agent_name,
                          al.created_at,
                          al.id
                   FROM attack_logs al
                            LEFT JOIN honey_agents ha ON al.agent_id = ha.id
                   ORDER BY al.id DESC
                   LIMIT 5
                   ''')

        return db.fetchall()


def get_country_ranking() -> List[Dict[str, Any]]:
    """
    Récupère le classement des pays par nombre d'attaques pour le dashboard.

    Returns:
        List[Dict[str, Any]]: Liste des 10 pays avec le plus d'attaques, triés par ordre décroissant.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT country_name AS country_name,
                          COUNT(*)     AS attack_count
                   FROM attack_logs
                   WHERE country_name IS NOT NULL
                     AND country_name != ''
                   GROUP BY country_name
                   ORDER BY attack_count DESC
                   LIMIT 10
                   ''')

        return db.fetchall()


def get_password_ranking() -> List[Dict[str, Any]]:
    """
    Récupère le classement des 5 mots de passe les plus tentés.

    Returns:
        List[Dict[str, Any]]: Liste des 5 mots de passe les plus populaires.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT
                password,
                MAX(count) AS count
            FROM password_attempted
            GROUP BY password
            ORDER BY count DESC
            LIMIT 5
        ''')

        return db.fetchall()



class ManagerAgent:
    """
    Classe pour gérer les opérations CRUD sur les agents honeypot.
    """

    @staticmethod
    def get_agent_by_id(agent_id: int) -> bool:
        with DatabaseManagerHoneypot() as db:

            db.execute('''SELECT id FROM honey_agents WHERE id = %s''', (int(agent_id),))
            agent = db.fetchone()
            if agent:
                return True
            return False

    @staticmethod
    def remove(agent_id: int) -> bool:
        """
        Supprime un agent honeypot de la base de données.

        Args:
            agent_id (int): Identifiant de l'agent à supprimer.

        Returns:
            bool: True si l'agent a été supprimé, False s'il n'existe pas.
        """
        with DatabaseManagerHoneypot() as db:

            db.execute('''SELECT id FROM honey_agents WHERE id = %s''', (int(agent_id),))
            agent = db.fetchone()
            if agent:
                db.execute("DELETE FROM honey_agents WHERE id = %s", (int(agent_id),))
                return True
            return False

    @staticmethod
    def list() -> List[Dict[str, Any]]:
        """
        Récupère la liste complète de tous les agents honeypot.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant les informations des agents.
        """
        with DatabaseManagerHoneypot() as db:
            db.execute("""
                       SELECT id,
                              agent_name,
                              ip_address,
                              service_type,
                              updated_at,
                              alert_generated,
                              created_at
                       FROM honey_agents
                       """)

            agents = db.fetchall()
            return agents



# ============= FUNCTIONS FOR REPORT GENERATION =============

def get_top_passwords(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Récupère les mots de passe les plus tentés.

    Args:
        limit (int, optional): Nombre maximum de résultats. Par défaut 20.

    Returns:
        List[Dict[str, Any]]: Liste des mots de passe avec leur nombre d'occurrences.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT password, count
                   FROM password_attempted
                   WHERE password IS NOT NULL
                   ORDER BY count DESC
                   LIMIT %s
                   ''', (limit,))

        return db.fetchall()


def get_top_usernames(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Récupère les noms d'utilisateur les plus tentés.

    Args:
        limit (int, optional): Nombre maximum de résultats. Par défaut 20.

    Returns:
        List[Dict[str, Any]]: Liste des usernames avec leur nombre d'occurrences.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT username, count
                   FROM username_viewed
                   WHERE username IS NOT NULL
                   ORDER BY count DESC
                   LIMIT %s
                   ''', (limit,))

        return db.fetchall()


def get_service_distribution() -> List[Dict[str, Any]]:
    """
    Récupère la distribution des attaques par type de service.

    Returns:
        List[Dict[str, Any]]: Liste des services ciblés avec le nombre d'attaques.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT service_type, COUNT(*) as count
                   FROM attack_logs
                   WHERE service_type IS NOT NULL
                   GROUP BY service_type
                   ORDER BY count DESC
                   ''')

        return db.fetchall()


def get_top_malicious_ips(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Récupère les IPs malveillantes les plus agressives.

    Args:
        limit (int, optional): Nombre maximum de résultats. Par défaut 20.

    Returns:
        List[Dict[str, Any]]: Liste des IPs avec leurs détails et statistiques.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT m.ip_address                               AS ip,
                          COALESCE(m.country_name, 'Unknown')        AS country,
                          m.total_attack_count                       AS attacks,
                          COALESCE(m.classification, 'Unclassified') AS classification,
                          m.first_seen,
                          m.last_seen
                   FROM malicious_ips m
                   ORDER BY m.total_attack_count DESC
                   LIMIT %s
                   ''', (limit,))

        return db.fetchall()


def get_attacks_by_day(days: int = 7) -> List[Dict[str, Any]]:
    """
    Récupère le nombre d'attaques pour les N derniers jours.

    Args:
        days (int, optional): Nombre de jours à analyser. Par défaut 7.

    Returns:
        List[Dict[str, Any]]: Liste des dates avec le nombre d'attaques par jour.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT DATE(created_at) AS date,
                          COUNT(*)         AS count
                   FROM attack_logs
                   WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                   GROUP BY DATE(created_at)
                   ORDER BY date ASC
                   ''', (days,))

        return db.fetchall()


def get_attacks_by_hour() -> List[Dict[str, Any]]:
    """
    Récupère le nombre d'attaques par heure pour les dernières 24 heures.

    Returns:
        List[Dict[str, Any]]: Liste des heures avec le nombre d'attaques.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT HOUR(created_at) AS hour,
                          COUNT(*)         AS count
                   FROM attack_logs
                   WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                   GROUP BY HOUR(created_at)
                   ORDER BY hour ASC
                   ''')

        results = db.fetchall()

        data = [
            {
                'hour': f"{row['hour']:02d}:00",
                'count': row['count']
            }
            for row in results
        ]

        return data


def get_agent_statistics() -> List[Dict[str, Any]]:
    """
    Récupère les statistiques pour tous les agents honeypot.

    Returns:
        List[Dict[str, Any]]: Liste des agents avec leurs statistiques détaillées.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT ha.id                                AS id,
                          ha.agent_name                        AS name,
                          COALESCE(ha.country_name, 'Unknown') AS country,
                          ha.service_type                      AS service,
                          ha.alert_generated                   AS alerts,
                          ha.created_at                        AS created_at,
                          COUNT(al.id)                         AS total_logs
                   FROM honey_agents ha
                            LEFT JOIN attack_logs al ON ha.id = al.agent_id
                   GROUP BY ha.id
                   ORDER BY total_logs DESC
                   ''')

        return db.fetchall()


def get_payload_statistics() -> List[Dict[str, Any]]:
    """
    Récupère les statistiques sur les payloads/malwares capturés.

    Returns:
        List[Dict[str, Any]]: Liste des types de payloads avec leur compteur.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT COALESCE(payload_type, 'Unknown')   AS type,
                          COALESCE(malware_family, 'Unknown') AS family,
                          COUNT(*)                            AS count
                   FROM payloads
                   WHERE payload_type IS NOT NULL
                      OR malware_family IS NOT NULL
                   GROUP BY payload_type, malware_family
                   ORDER BY count DESC
                   LIMIT 20
                   ''')

        return db.fetchall()


def get_port_distribution() -> List[Dict[str, Any]]:
    """
    Récupère la distribution des ports ciblés.

    Returns:
        List[Dict[str, Any]]: Liste des 10 ports les plus ciblés avec leur compteur.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT target_port AS port,
                          COUNT(*)    AS count
                   FROM attack_logs
                   WHERE target_port IS NOT NULL
                   GROUP BY target_port
                   ORDER BY count DESC
                   LIMIT 10
                   ''')

        return db.fetchall()


def get_credential_combinations() -> List[Dict[str, Any]]:
    """
    Récupère les 15 combinaisons username/password les plus observées.

    Returns:
        List[Dict[str, Any]]: Liste des combinaisons de credentials avec leur compteur.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT username,
                          password,
                          SUM(attempt_count) AS count
                   FROM compromised_credentials
                   GROUP BY username, password
                   ORDER BY count DESC
                   LIMIT 15
                   ''')

        return db.fetchall()


def get_agent_about(agent_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère toutes les informations détaillées d'un agent honeypot spécifique.

    Args:
        agent_id (int): Identifiant de l'agent.

    Returns:
        Optional[Dict[str, Any]]: Dictionnaire avec les détails de l'agent, ou None si non trouvé.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # 1. Agent base info
            db.execute("""
                SELECT id, agent_name, ip_address, country_name, service_type,
                       banner, alert_generated, created_at, updated_at
                FROM honey_agents
                WHERE id = %s
            """, (agent_id,))
            agent = db.fetchone()

            if not agent:
                return None

            # 2. Attack stats
            db.execute("""
                SELECT
                    COUNT(*) AS total_attacks,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) AS attacks_today,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) AS attacks_week,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) AS attacks_month
                FROM attack_logs
                WHERE agent_id = %s
            """, (agent_id,))
            stats = db.fetchone()

            # 3. Unique IPs count
            db.execute("""
                SELECT COUNT(DISTINCT ip_id) AS unique_ips
                FROM ip_agent_relations
                WHERE agent_id = %s
            """, (agent_id,))
            ip_stats = db.fetchone()

            # 4. Top countries for this agent
            db.execute("""
                SELECT country_name, COUNT(*) AS count
                FROM attack_logs
                WHERE agent_id = %s AND country_name IS NOT NULL AND country_name != ''
                GROUP BY country_name
                ORDER BY count DESC
                LIMIT 10
            """, (agent_id,))
            top_countries_raw = db.fetchall()

            total_with_country = sum(c['count'] for c in top_countries_raw) if top_countries_raw else 1
            top_countries = [
                {
                    'country': c['country_name'],
                    'count': c['count'],
                    'percentage': round(c['count'] / total_with_country * 100, 1)
                }
                for c in top_countries_raw
            ]

            # 5. Recent attacks
            db.execute("""
                SELECT id, created_at, source_ip, country_code, country_name,
                       attack_type, service_type, source_port, target_port,
                       username_attempt, password_attempt
                FROM attack_logs
                WHERE agent_id = %s
                ORDER BY id DESC
                LIMIT 20
            """, (agent_id,))
            recent_attacks = db.fetchall()

            # Format attacks for frontend
            formatted_attacks = []
            for a in recent_attacks:
                formatted_attacks.append({
                    'id': a['id'],
                    'timestamp': a['created_at'].isoformat() if a['created_at'] else None,
                    'source_ip': a['source_ip'],
                    'country': a['country_code'] or a['country_name'] or 'N/A',
                    'type': a['attack_type'] or a['service_type'] or 'Unknown',
                    'service_type': a['service_type'],
                    'source_port': a['source_port'],
                    'target_port': a['target_port'],
                    'username': a['username_attempt'],
                    'password': a['password_attempt']
                })

            return {
                'id': agent['id'],
                'name': agent['agent_name'],
                'type': agent['service_type'],
                'status': 'active',
                'ip': agent['ip_address'],
                'country': agent['country_name'],
                'banner': agent['banner'],
                'alert_generated': agent['alert_generated'],
                'created_at': agent['created_at'].isoformat() if agent['created_at'] else None,
                'updated_at': agent['updated_at'].isoformat() if agent['updated_at'] else None,
                'stats': {
                    'total_attacks': stats['total_attacks'] or 0,
                    'unique_ips': ip_stats['unique_ips'] or 0,
                    'attacks_today': stats['attacks_today'] or 0,
                    'attacks_week': stats['attacks_week'] or 0,
                    'attacks_month': stats['attacks_month'] or 0,
                },
                'top_countries': top_countries,
                'recent_attacks': formatted_attacks
            }

    except Exception as e:
        print(f"Error getting agent about: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def get_complete_report_data() -> Dict[str, Any]:
    """
    Récupère toutes les données nécessaires pour un rapport complet.

    Returns:
        Dict[str, Any]: Dictionnaire contenant toutes les métriques et statistiques:
            - metrics: Métriques générales
            - country_ranking: Classement des pays
            - top_passwords: Mots de passe les plus tentés
            - top_usernames: Usernames les plus tentés
            - service_distribution: Distribution des services
            - top_ips: IPs les plus agressives
            - attacks_by_day: Attaques par jour
            - attacks_by_hour: Attaques par heure
            - agents: Statistiques des agents
            - payloads: Statistiques des payloads
            - port_distribution: Distribution des ports
            - credential_combinations: Combinaisons de credentials
    """
    return {
        'metrics': get_default_metric_data(),
        'country_ranking': get_country_ranking(),
        'top_passwords': get_top_passwords(20),
        'top_usernames': get_top_usernames(20),
        'service_distribution': get_service_distribution(),
        'top_ips': get_top_malicious_ips(20),
        'attacks_by_day': get_attacks_by_day(7),
        'attacks_by_hour': get_attacks_by_hour(),
        'agents': get_agent_statistics(),
        'payloads': get_payload_statistics(),
        'port_distribution': get_port_distribution(),
        'credential_combinations': get_credential_combinations()
    }
