from module.database.db_manager import DatabaseManagerHoneypot

def create_agent_token(agent_name, secret_token):
    try:
        with DatabaseManagerHoneypot() as db:
            # Hash the secret token for security
            import hashlib
            secret_token_sha256 = hashlib.sha256(secret_token.encode()).hexdigest()
            
            db.execute("INSERT INTO honey_agents (agent_name, ip_address, service_type, secret_token_sha256) VALUES (?, ?, ?, ?)",
                      (agent_name, "0.0.0.0", "honeypot", secret_token_sha256))
            return True
    except Exception as e:
        print(f"Error creating agent token: {e}")
        return False

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
    """Insert attack log data into the database"""
    try:
        with DatabaseManagerHoneypot() as db:
            db.execute("""INSERT INTO attack_logs 
                         (agent_id, source_ip, source_port, target_port, service_type, 
                          username_attempt, password_attempt, payload, malware_hash, 
                          attack_type, country_code, country_name) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (attack_data.get('agent_id'),
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

        db.execute("SELECT COUNT(payload_hash) FROM payloads")
        unique_sample_count = db.fetchone()

        db.execute("SELECT COUNT(*) FROM honey_agents WHERE is_active = 1;")
        active_agents = db.fetchone()

        data = {
            "ip_count": ip_count[0],
            "Sample_downloaded": unique_sample_count[0],
            "tentative_access": 0,
            "active_honeypot": active_agents[0]
        }

        return data

def get_agent_details():
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT country_name, source_ip, target_port, service_type, agent_id 
            FROM attack_logs 
            ORDER BY id DESC 
            LIMIT 5
        ''')
        logs = db.fetchall()

        agent_name = "ssh-honeypot-test"

        data = []
        for log in logs:
            data.append({
                "agent_id": log[4],
                "agent_name": agent_name,
                "country_name": log[0],
                "source_ip": log[1],
                "target_port": log[2],
                "service_type": log[3]
            })

    return data
