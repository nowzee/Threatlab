from module.database.db_manager import DatabaseManagerHoneypot
from datetime import datetime
import jwt, os, hashlib
from flask import current_app

def generate_jwt(agent_id: int) -> str:
    """
    Génère un JWT unique pour un agent spécifique.
    """
    secret_key = current_app.config['SECRET_KEY']
    payload_to_encode = {
        'agent_id': agent_id,
        'nonce': os.urandom(16).hex()  # Ajoute de l'aléatoire pour garantir l'unicité
    }
    token = jwt.encode(payload_to_encode, secret_key, algorithm='HS256')
    return token


def create_agent_token(agent_name: str,
                       ip_address: str = "0.0.0.0",
                       country_name: str = None,
                       service_type: str = "ssh",
                       groupe: str = None,
                       banner: str = None):
    """
    Crée un enregistrement pour un nouvel agent honeypot et génère un token unique.
    Retourne (agent_id, secret_token) si succès, sinon (None, None).
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

def add_malicious_ip_address(agent_id, ip_address, service_type, country_name=None, country_code=None, classification=None):
    """
    Add or update malicious IP with normalized relationships.
    Manages IP record, IP-Agent relationship, and IP-Service attack count.
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

def _update_ip_agent_relation(db, ip_id, agent_id):
    """Helper function to update IP-Agent relationship"""
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

def _update_ip_service_attacks(db, ip_id, service_type):
    """Helper function to update IP-Service attack count"""
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

def add_compromised_credential(malicious_ip, username, password, service_type):
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

def add_attack_log(attack_data):
    """Insert attack log data into the database with current timestamp"""
    try:
        with DatabaseManagerHoneypot() as db:
            now = datetime.now()  # heure locale du serveur
            # ou datetime.utcnow() si tu veux UTC

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

def add_smtp_interaction(malicious_ip, sender_email, recipient_email, subject, message_content, attachments=None):
    """Insert SMTP interaction data into the database"""
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

def get_default_metric_data():
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

def get_agent_details():
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT country_name, source_ip, target_port, service_type, agent_id, created_at 
            FROM attack_logs 
            ORDER BY id DESC 
            LIMIT 5
        ''')
        logs = db.fetchall()

        db.execute("SELECT agent_name FROM honey_agents WHERE id = ?", (logs[0][4],))
        agent_name = db.fetchone()[0]

        data = []
        for log in logs:
            data.append({
                "agent_id": log[4],
                "agent_name": agent_name,
                "country_name": log[0],
                "source_ip": log[1],
                "target_port": log[2],
                "service_type": log[3],
                "created_at": log[5]
            })

    return data

def get_country_ranking():
    """
    Get the top countries by attack count for dashboard visualization
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


class ManagerAgent:
    @staticmethod
    def remove(agent_id: int) -> bool:
        with DatabaseManagerHoneypot() as db:
            
            db.execute('''SELECT id FROM honey_agents WHERE id = ?''', (int(agent_id),))
            agent = db.fetchone()
            if agent:
                db.execute("DELETE FROM honey_agents WHERE id = ?", (int(agent_id),))
                return True
            return False

    def update(self, agent_id, agent_name, is_active):
        pass

    @staticmethod
    def list() -> list:
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
                    'is_active': row[5] if len(row) > 5 else 1,  # Valeur par défaut
                    'groupe': row[6] if len(row) > 6 else 'default',  # Valeur par défaut
                    'alert_generated': row[7] if len(row) > 7 else 0,  # Valeur par défaut
                    'created_at': row[8] if len(row) > 8 else row[4]  # Utiliser updated_at si created_at n'existe pas
                }
                agents.append(agent)

            return agents

    @staticmethod
    def create_group(group_name) -> bool:
        with DatabaseManagerHoneypot() as db:
            db.execute("SELECT id FROM groups_agent WHERE group_name = ?", (str(group_name),))
            result = db.fetchone()
            if result:
                return False

            db.execute("INSERT INTO groups_agent (group_name) VALUES (?)", (str(group_name),))
            return True

