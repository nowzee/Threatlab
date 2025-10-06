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
    secret_key = current_app.config['SECRET_KEY']
    payload_to_encode = {
        'agent_id': agent_id,
        'nonce': os.urandom(16).hex()
    }
    token = jwt.encode(payload_to_encode, secret_key, algorithm='HS256')
    return token


def create_agent_token(agent_name: str,
                       ip_address: str = "0.0.0.0",
                       country_name: Optional[str] = None,
                       service_type: str = "ssh",
                       groupe: Optional[str] = None,
                       banner: Optional[str] = None) -> Tuple[Optional[int], Optional[str]]:
    """
    Crée un enregistrement pour un nouvel agent honeypot et génère un token unique.

    Args:
        agent_name (str): Nom de l'agent honeypot.
        ip_address (str, optional): Adresse IP de l'agent. Par défaut "0.0.0.0".
        country_name (Optional[str], optional): Nom du pays où l'agent est déployé. Par défaut None.
        service_type (str, optional): Type de service simulé (ssh, smtp, ftp, etc.). Par défaut "ssh".
        groupe (Optional[str], optional): Groupe d'appartenance de l'agent. Par défaut None.
        banner (Optional[str], optional): Banner du service simulé. Par défaut None.

    Returns:
        Tuple[Optional[int], Optional[str]]: (agent_id, secret_token) si succès, sinon (None, None).
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # 1. Insérer un nouvel agent sans token
            db.execute("""
                INSERT INTO honey_agents (agent_name, ip_address, country_name, service_type, groupe, banner)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (agent_name, ip_address, country_name, service_type, groupe, banner))

            # 2. Récupérer l'ID de l'agent inséré
            db.execute("SELECT last_insert_rowid()")
            agent_id = db.fetchone()[0]

            # 3. Générer un token unique et son hash
            secret_token = generate_jwt(agent_id)
            secret_token_sha256 = hashlib.sha256(secret_token.encode()).hexdigest()

            # 4. Mettre à jour l'agent avec le hash du token
            db.execute("""
                UPDATE honey_agents
                SET secret_token_sha256 = ?
                WHERE id = ?
            """, (secret_token_sha256, agent_id))

            return agent_id, secret_token

    except Exception as e:
        print(f"Error creating agent token: {e}")
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
            # Step 1: Get or create the malicious IP record
            db.execute("SELECT id, total_attack_count FROM malicious_ips WHERE ip_address = ?", (ip_address,))
            existing_ip = db.fetchone()

            if existing_ip:
                # Update existing IP record
                ip_id, total_attack_count = existing_ip
                new_total_count = total_attack_count + 1

                db.execute("""UPDATE malicious_ips
                             SET last_seen = CURRENT_TIMESTAMP,
                                 total_attack_count = ?,
                                 country_name = COALESCE(?, country_name),
                                 country_code = COALESCE(?, country_code),
                                 classification = COALESCE(?, classification)
                             WHERE id = ?""",
                          (new_total_count, country_name, country_code, classification, ip_id))
            else:
                # Insert new malicious IP
                db.execute("""INSERT INTO malicious_ips
                             (ip_address, country_name, country_code, classification)
                             VALUES (?, ?, ?, ?)""",
                          (ip_address, country_name, country_code, classification))

                # Get the newly inserted IP ID
                db.execute("SELECT id FROM malicious_ips WHERE ip_address = ?", (ip_address,))
                ip_id = db.fetchone()[0]

            # Step 2: Manage IP-Agent relationship
            _update_ip_agent_relation(db, ip_id, agent_id)

            # Step 3: Manage IP-Service attack count
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
        # Check if relationship already exists
        db.execute("SELECT id, report_count FROM ip_agent_relations WHERE ip_id = ? AND agent_id = ?",
                  (ip_id, agent_id))
        existing_relation = db.fetchone()

        if existing_relation:
            # Update existing relationship
            relation_id, report_count = existing_relation
            new_report_count = report_count + 1
            db.execute("""UPDATE ip_agent_relations
                         SET last_seen = CURRENT_TIMESTAMP, report_count = ?
                         WHERE id = ?""",
                      (new_report_count, relation_id))
        else:
            # Insert new IP-Agent relationship
            db.execute("""INSERT INTO ip_agent_relations (ip_id, agent_id)
                         VALUES (?, ?)""", (ip_id, agent_id))
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
        # Check if IP-Service combination already exists
        db.execute("SELECT id, attack_count FROM ip_service_attacks WHERE ip_id = ? AND service_type = ?",
                  (ip_id, service_type))
        existing_service = db.fetchone()

        if existing_service:
            # Update existing service attack count
            service_id, attack_count = existing_service
            new_attack_count = attack_count + 1
            db.execute("""UPDATE ip_service_attacks
                         SET last_seen = CURRENT_TIMESTAMP, attack_count = ?
                         WHERE id = ?""",
                      (new_attack_count, service_id))
        else:
            # Insert new IP-Service attack record
            db.execute("""INSERT INTO ip_service_attacks (ip_id, service_type)
                         VALUES (?, ?)""", (ip_id, service_type))
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
            # Get malicious IP ID
            db.execute("SELECT id FROM malicious_ips WHERE ip_address = ?", (malicious_ip,))
            ip_record = db.fetchone()

            if not ip_record:
                print(f"Malicious IP {malicious_ip} not found in database")
                return False

            malicious_ip_id = ip_record[0]

            # Check if credential combination already exists
            db.execute("""SELECT id, attempt_count FROM compromised_credentials
                         WHERE malicious_ip_id = ? AND service_type = ? AND username = ? AND password = ?""",
                      (malicious_ip_id, service_type, username, password))
            existing_credential = db.fetchone()

            if existing_credential:
                # Update existing credential
                credential_id, attempt_count = existing_credential
                new_attempt_count = attempt_count + 1
                db.execute("""UPDATE compromised_credentials
                             SET last_seen = CURRENT_TIMESTAMP, attempt_count = ?
                             WHERE id = ?""",
                          (new_attempt_count, credential_id))
            else:
                # Insert new credential
                db.execute("""INSERT INTO compromised_credentials
                             (malicious_ip_id, service_type, username, password)
                             VALUES (?, ?, ?, ?)""",
                          (malicious_ip_id, service_type, username, password))

            # Update username statistics
            db.execute("SELECT id, count FROM username_viewed WHERE username = ?", (username,))
            username_record = db.fetchone()

            if username_record:
                username_id, count = username_record
                db.execute("UPDATE username_viewed SET count = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?",
                          (count + 1, username_id))
            else:
                db.execute("INSERT INTO username_viewed (username) VALUES (?)", (username,))

            # Update password statistics
            db.execute("SELECT id, count FROM password_attempted WHERE password = ?", (password,))
            password_record = db.fetchone()

            if password_record:
                password_id, count = password_record
                db.execute("UPDATE password_attempted SET count = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?",
                          (count + 1, password_id))
            else:
                db.execute("INSERT INTO password_attempted (password) VALUES (?)", (password,))

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
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
            db.execute("SELECT id FROM malicious_ips WHERE ip_address = ?", (malicious_ip,))
            ip_record = db.fetchone()

            if not ip_record:
                print(f"Malicious IP {malicious_ip} not found in database")
                return False

            malicious_ip_id = ip_record[0]

            # Insert SMTP interaction
            import json
            attachments_json = json.dumps(attachments) if attachments else None

            db.execute("""INSERT INTO smtp_interactions
                         (malicious_server_ip_id, sender_email, recipient_email, subject,
                          message_content, attachments)
                         VALUES (?, ?, ?, ?, ?, ?)""",
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
            - active_honeypot: Nombre d'agents honeypot actifs
    """
    with DatabaseManagerHoneypot() as db:
        db.execute("SELECT COUNT(*) FROM malicious_ips")
        ip_count = db.fetchone()

        db.execute("SELECT COUNT(*) FROM payloads")
        unique_sample_count = db.fetchone()

        db.execute("SELECT COUNT(*) FROM honey_agents WHERE is_active = 1;")
        active_agents = db.fetchone()

        db.execute("SELECT COUNT(*) FROM attack_logs")
        tentative_attacks = db.fetchone()

        data = {
            "ip_count": ip_count[0],
            "Sample_downloaded": unique_sample_count[0],
            "tentative_access": tentative_attacks[0],
            "active_honeypot": active_agents[0]
        }

        return data

def get_agent_details() -> List[Dict[str, Any]]:
    """
    Récupère les détails des 5 derniers logs d'attaques avec informations des agents.

    Returns:
        List[Dict[str, Any]]: Liste de dictionnaires contenant les informations des logs.
    """
    with DatabaseManagerHoneypot() as db:
        # Récupérer les 5 derniers logs
        db.execute('''
            SELECT country_name, source_ip, target_port, service_type, agent_id, created_at, id
            FROM attack_logs
            ORDER BY id DESC
            LIMIT 5
        ''')
        logs = db.fetchall()

        if not logs:
            return []

        data = []
        for log in logs:
            agent_id = log[4]
            # Récupérer le nom de l'agent pour chaque log
            db.execute("SELECT agent_name FROM honey_agents WHERE id = ?", (agent_id,))
            result = db.fetchone()
            agent_name = result[0] if result else None

            data.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "country_name": log[0],
                "source_ip": log[1],
                "target_port": log[2],
                "service_type": log[3],
                "created_at": log[5],
                "id": log[6]
            })

    return data


def get_country_ranking() -> List[Dict[str, Any]]:
    """
    Récupère le classement des pays par nombre d'attaques pour le dashboard.

    Returns:
        List[Dict[str, Any]]: Liste des 10 pays avec le plus d'attaques, triés par ordre décroissant.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT country_name, COUNT(*) as attack_count
            FROM attack_logs
            WHERE country_name IS NOT NULL AND country_name != ''
            GROUP BY country_name
            ORDER BY attack_count DESC
            LIMIT 10
        ''')
        countries = db.fetchall()

        data = []
        for country in countries:
            data.append({
                "country_name": country[0],
                "attack_count": country[1]
            })

        return data

def get_password_ranking() -> List[Dict[str, Any]]:
    """
    Récupère le classement des 5 mots de passe les plus tentés.

    Returns:
        List[Dict[str, Any]]: Liste des 5 mots de passe les plus populaires.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''SELECT password, count FROM password_attempted GROUP BY password ORDER BY count DESC LIMIT 5''')
        results = db.fetchall()

        data = []
        for password in results:
            data.append({
                'password': password[0],
                'count': password[1]
            })

        return data


class ManagerAgent:
    """
    Classe pour gérer les opérations CRUD sur les agents honeypot.
    """

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

            db.execute('''SELECT id FROM honey_agents WHERE id = ?''', (int(agent_id),))
            agent = db.fetchone()
            if agent:
                db.execute("DELETE FROM honey_agents WHERE id = ?", (int(agent_id),))
                return True
            return False

    def update(self, agent_id: int, agent_name: str, is_active: int) -> None:
        """
        Met à jour les informations d'un agent honeypot.

        Args:
            agent_id (int): Identifiant de l'agent.
            agent_name (str): Nouveau nom de l'agent.
            is_active (int): Statut d'activation (0 ou 1).
        """
        pass

    @staticmethod
    def list() -> List[Dict[str, Any]]:
        """
        Récupère la liste complète de tous les agents honeypot.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant les informations des agents.
        """
        with DatabaseManagerHoneypot() as db:
            db.execute('''SELECT id,
                                 agent_name,
                                 ip_address,
                                 service_type,
                                 updated_at,
                                 is_active,
                                 groupe,
                                 alert_generated,
                                 created_at
                          FROM honey_agents''')
            result = db.fetchall()

            # Convertir les tuples en dictionnaires
            agents = []
            for row in result:
                agent = {
                    'id': row[0],
                    'agent_name': row[1],
                    'ip_address': row[2],
                    'service_type': row[3],
                    'updated_at': row[4],
                    'is_active': row[5] if len(row) > 5 else 1,
                    'groupe': row[6] if len(row) > 6 else 'default',
                    'alert_generated': row[7] if len(row) > 7 else 0,
                    'created_at': row[8] if len(row) > 8 else row[4]
                }
                agents.append(agent)

            return agents

    @staticmethod
    def create_group(group_name: str) -> bool:
        """
        Crée un nouveau groupe d'agents.

        Args:
            group_name (str): Nom du groupe à créer.

        Returns:
            bool: True si le groupe a été créé, False s'il existe déjà.
        """
        with DatabaseManagerHoneypot() as db:
            db.execute("SELECT id FROM groups_agent WHERE group_name = ?", (str(group_name),))
            result = db.fetchone()
            if result:
                return False

            db.execute("INSERT INTO groups_agent (group_name) VALUES (?)", (str(group_name),))
            return True


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
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        results = db.fetchall()

        data = []
        for row in results:
            if row[0]:  # Skip null passwords
                data.append({
                    'password': row[0],
                    'count': row[1]
                })
        return data


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
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        results = db.fetchall()

        data = []
        for row in results:
            if row[0]:  # Skip null usernames
                data.append({
                    'username': row[0],
                    'count': row[1]
                })
        return data


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
        results = db.fetchall()

        data = []
        for row in results:
            data.append({
                'service': row[0],
                'count': row[1]
            })
        return data


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
            SELECT
                m.ip_address,
                m.country_name,
                m.total_attack_count,
                m.classification,
                m.first_seen,
                m.last_seen
            FROM malicious_ips m
            ORDER BY m.total_attack_count DESC
            LIMIT ?
        ''', (limit,))
        results = db.fetchall()

        data = []
        for row in results:
            data.append({
                'ip': row[0],
                'country': row[1] or 'Unknown',
                'attacks': row[2],
                'classification': row[3] or 'Unclassified',
                'first_seen': row[4],
                'last_seen': row[5]
            })
        return data


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
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM attack_logs
            WHERE created_at >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        ''', (days,))
        results = db.fetchall()

        data = []
        for row in results:
            data.append({
                'date': row[0],
                'count': row[1]
            })
        return data


def get_attacks_by_hour() -> List[Dict[str, Any]]:
    """
    Récupère le nombre d'attaques par heure pour les dernières 24 heures.

    Returns:
        List[Dict[str, Any]]: Liste des heures avec le nombre d'attaques.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT
                strftime('%H', created_at) as hour,
                COUNT(*) as count
            FROM attack_logs
            WHERE created_at >= datetime('now', '-1 day')
            GROUP BY hour
            ORDER BY hour ASC
        ''')
        results = db.fetchall()

        data = []
        for row in results:
            data.append({
                'hour': row[0] + ':00',
                'count': row[1]
            })
        return data


def get_agent_statistics() -> List[Dict[str, Any]]:
    """
    Récupère les statistiques pour tous les agents honeypot.

    Returns:
        List[Dict[str, Any]]: Liste des agents avec leurs statistiques détaillées.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT
                ha.id,
                ha.agent_name,
                ha.country_name,
                ha.service_type,
                ha.is_active,
                ha.alert_generated,
                ha.created_at,
                COUNT(al.id) as total_logs
            FROM honey_agents ha
            LEFT JOIN attack_logs al ON ha.id = al.agent_id
            GROUP BY ha.id
            ORDER BY total_logs DESC
        ''')
        results = db.fetchall()

        data = []
        for row in results:
            data.append({
                'id': row[0],
                'name': row[1],
                'country': row[2] or 'Unknown',
                'service': row[3],
                'is_active': row[4],
                'alerts': row[5],
                'created_at': row[6],
                'total_logs': row[7]
            })
        return data


def get_payload_statistics() -> List[Dict[str, Any]]:
    """
    Récupère les statistiques sur les payloads/malwares capturés.

    Returns:
        List[Dict[str, Any]]: Liste des types de payloads avec leur compteur.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT
                payload_type,
                malware_family,
                COUNT(*) as count
            FROM payloads
            WHERE payload_type IS NOT NULL OR malware_family IS NOT NULL
            GROUP BY payload_type, malware_family
            ORDER BY count DESC
            LIMIT 20
        ''')
        results = db.fetchall()

        data = []
        for row in results:
            data.append({
                'type': row[0] or 'Unknown',
                'family': row[1] or 'Unknown',
                'count': row[2]
            })
        return data


def get_port_distribution() -> List[Dict[str, Any]]:
    """
    Récupère la distribution des ports ciblés.

    Returns:
        List[Dict[str, Any]]: Liste des 10 ports les plus ciblés avec leur compteur.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT
                target_port,
                COUNT(*) as count
            FROM attack_logs
            WHERE target_port IS NOT NULL
            GROUP BY target_port
            ORDER BY count DESC
            LIMIT 10
        ''')
        results = db.fetchall()

        data = []
        for row in results:
            data.append({
                'port': row[0],
                'count': row[1]
            })
        return data


def get_credential_combinations() -> List[Dict[str, Any]]:
    """
    Récupère les 15 combinaisons username/password les plus observées.

    Returns:
        List[Dict[str, Any]]: Liste des combinaisons de credentials avec leur compteur.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT
                username,
                password,
                SUM(attempt_count) as total_attempts
            FROM compromised_credentials
            GROUP BY username, password
            ORDER BY total_attempts DESC
            LIMIT 15
        ''')
        results = db.fetchall()

        data = [
            {
                'username': row[0],
                'password': row[1],
                'count': row[2]
            }
            for row in results
        ]
        return data



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
