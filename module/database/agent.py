import sqlite3

def create_agent_token(agent_name, secret_token):

    try:
        with sqlite3.connect('honeypot.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO honey_agents (agent_name, secret_token) VALUES (?, ?)",
                           (agent_name, secret_token))
            return True
    finally:return False