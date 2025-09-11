from module.database.db_manager import DatabaseManagerHoneypot
import sqlite3

def create_agent_token(agent_name, secret_token):

    try:
        with sqlite3.connect('honeypot.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO honey_agents (agent_name, secret_token) VALUES (?, ?)",
                           (agent_name, secret_token))
            return True
    finally:return False

def add_malicious_ip_address(agent_id, ip_address, service_type, country_name=None, country_code=None, classification=None):
    return True

def add_compromised_credential(malicious_ip, username, password, service_type):
    with DatabaseManagerHoneypot() as db:
        db.execute("SELECT id FROM honey_agents WHERE ip_address = ? ", (malicious_ip,))
        ip_id = db.fetchone()[0]

        print(ip_id)
    return True