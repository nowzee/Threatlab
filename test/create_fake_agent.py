import sqlite3
import hashlib
import random
import string
from datetime import datetime

DB_PATH = "../db/honeypot.db"

def random_token(length=32):
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    sha256 = hashlib.sha256(token.encode()).hexdigest()
    return token, sha256

def create_fake_agent():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS honey_agents
        (
            id                  INTEGER PRIMARY KEY,
            agent_name          TEXT UNIQUE NOT NULL,
            ip_address          TEXT        NOT NULL,
            country_name        TEXT,
            service_type        TEXT        NOT NULL,
            groupe              TEXT,
            alert_generated     INTEGER DEFAULT 0,
            is_active           INTEGER  DEFAULT 0,
            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            secret_token_sha256 TEXT UNIQUE NOT NULL
        )
    ''')

    # Données simulées
    agent_name = f"agent_{random.randint(1000,9999)}"
    ip_address = f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
    country_name = random.choice(["France", "Germany", "USA", "Japan", "Brazil"])
    service_type = random.choice(["SSH", "HTTP", "FTP", "SMTP", "Telnet"])
    groupe = random.choice(["default", "prod", "test", "honeynet"])
    alert_generated = random.randint(0, 50)
    is_active = random.choice([0, 1])
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_at = created_at
    token, token_sha256 = random_token()

    # Insertion
    cursor.execute('''
        INSERT INTO honey_agents 
        (agent_name, ip_address, country_name, service_type, groupe, alert_generated, is_active, created_at, updated_at, secret_token_sha256)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (agent_name, ip_address, country_name, service_type, groupe, alert_generated, is_active, created_at, updated_at, token_sha256))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_fake_agent()
