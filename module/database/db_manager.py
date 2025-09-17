import sqlite3
import time
import string
import secrets
import hashlib

honeypot_db = 'db/honeypot.db'
users_db = 'db/user.db'


def generate_custom_snowflake(username: str) -> int:
    # Paramètres fixes pour éviter des IDs trop grands
    SEQUENCE_BITS = 12
    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5

    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1
    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1
    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1

    WORKER_ID_SHIFT = SEQUENCE_BITS
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    EPOCH = 1577836800000  # 1er janvier 2020 en ms

    # Horodatage actuel en millisecondes
    timestamp = int(time.time() * 1000)

    # Datacenter et Worker aléatoires
    datacenter_id = secrets.randbelow(MAX_DATACENTER_ID + 1)
    worker_id = secrets.randbelow(MAX_WORKER_ID + 1)

    # Générer une "sequence" pseudo-aléatoire basée sur username + timestamp
    hash_input = f"{username}-{timestamp}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    sequence = int(hash_digest[:3], 16) & MAX_SEQUENCE

    # Construction de l'ID avec limitation de la taille
    snowflake = (
            ((timestamp - EPOCH) << TIMESTAMP_LEFT_SHIFT) |
            (datacenter_id << DATACENTER_ID_SHIFT) |
            (worker_id << WORKER_ID_SHIFT) |
            sequence
    )
    print(f"Snowflake ID generated for {username}: {snowflake}")

    return snowflake

def generate_random_string(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

class DatabaseManagerHoneypot:
    def __init__(self):
        self.conn = sqlite3.connect(honeypot_db)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def create_db(self):
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS honey_agents
                                (
                                    id                  INTEGER PRIMARY KEY,
                                    agent_name          TEXT UNIQUE NOT NULL,
                                    ip_address          TEXT        NOT NULL,
                                    country_name        TEXT,
                                    service_type        TEXT        NOT NULL,
                                    is_active           INTEGER  DEFAULT 0,
                                    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    secret_token_sha256 TEXT UNIQUE NOT NULL
                                )
                                ''')

            # Table pour stocker les logs d'attaques
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS attack_logs
                                (
                                    id               INTEGER PRIMARY KEY,
                                    agent_id         INTEGER,
                                    source_ip        TEXT NOT NULL,
                                    source_port      INTEGER,
                                    target_port      INTEGER,
                                    service_type     TEXT NOT NULL,
                                    command          TEXT,
                                    username_attempt TEXT,
                                    password_attempt TEXT,
                                    payload          TEXT,
                                    malware_hash     TEXT,
                                    attack_type      TEXT,
                                    country_code     TEXT,
                                    country_name     TEXT,
                                    FOREIGN KEY (agent_id) REFERENCES honey_agents (id)
                                )
                                ''')

            # Table pour les IP malveillantes classifie (normalized)
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS malicious_ips
                                (
                                    id                INTEGER PRIMARY KEY,
                                    ip_address        TEXT UNIQUE NOT NULL,
                                    first_seen        DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    last_seen         DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    total_attack_count INTEGER  DEFAULT 1,
                                    country_code      TEXT,
                                    country_name      TEXT,
                                    reputation_score  INTEGER  DEFAULT 0,
                                    classification    TEXT,
                                    notes             TEXT
                                )
                                ''')

            # Table pour les relations IP-Agent (qui a vu quelle IP)
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS ip_agent_relations
                                (
                                    id           INTEGER PRIMARY KEY,
                                    ip_id        INTEGER NOT NULL,
                                    agent_id     INTEGER NOT NULL,
                                    first_seen   DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    last_seen    DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    report_count INTEGER  DEFAULT 1,
                                    FOREIGN KEY (ip_id) REFERENCES malicious_ips (id),
                                    FOREIGN KEY (agent_id) REFERENCES honey_agents (id),
                                    UNIQUE(ip_id, agent_id)
                                )
                                ''')

            # Table pour les attaques par service (IP-Service avec compteurs)
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS ip_service_attacks
                                (
                                    id           INTEGER PRIMARY KEY,
                                    ip_id        INTEGER NOT NULL,
                                    service_type TEXT    NOT NULL,
                                    attack_count INTEGER  DEFAULT 1,
                                    first_seen   DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    last_seen    DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    FOREIGN KEY (ip_id) REFERENCES malicious_ips (id),
                                    UNIQUE(ip_id, service_type)
                                )
                                ''')

            # Table pour les payloads et malwares
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS payloads
                                (
                                    id              INTEGER PRIMARY KEY,
                                    malicious_ip_id INTEGER,
                                    service_type    TEXT        NOT NULL,
                                    payload_name    TEXT        NOT NULL,
                                    payload_hash    TEXT UNIQUE NOT NULL,
                                    file_extension  TEXT,
                                    file_size       INTEGER,
                                    payload_content TEXT,
                                    payload_type    TEXT,
                                    malware_family  TEXT,
                                    first_seen      DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    last_seen       DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    detection_count INTEGER  DEFAULT 1,
                                    FOREIGN KEY (malicious_ip_id) REFERENCES malicious_ips (id)
                                )
                                ''')

            # Table pour les interactions SMTP mail spécifiques
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS smtp_interactions
                                (
                                    id                     INTEGER PRIMARY KEY,
                                    malicious_server_ip_id INTEGER,
                                    sender_email           TEXT,
                                    recipient_email        TEXT,
                                    subject                TEXT,
                                    message_content        TEXT,
                                    attachments            TEXT, -- JSON array des pièces jointes
                                    timestamp              DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    FOREIGN KEY (malicious_server_ip_id) REFERENCES malicious_ips (id)
                                )
                                ''')

            # Table pour les credentials compromis collectés par service
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS compromised_credentials
                                (
                                    id              INTEGER PRIMARY KEY,
                                    malicious_ip_id INTEGER,
                                    service_type    TEXT NOT NULL, -- 'smtp', 'ftp', 'iot', 'ssh', etc.
                                    username        TEXT NOT NULL,
                                    password        TEXT NOT NULL,
                                    first_seen      DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    last_seen       DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    attempt_count   INTEGER  DEFAULT 1,
                                    FOREIGN KEY (malicious_ip_id) REFERENCES malicious_ips (id)
                                )
                                ''')

            # Table de tout les mots de passe collecte et les plus teste
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS password_attempted
                                (
                                    id         INTEGER PRIMARY KEY,
                                    password   TEXT NOT NULL,
                                    count      INTEGER  DEFAULT 1,
                                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    last_seen  DATETIME DEFAULT CURRENT_TIMESTAMP
                                )
                                ''')

            # Table pour les username les plus vues
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS username_viewed
                                (
                                    id         INTEGER PRIMARY KEY,
                                    username   TEXT NOT NULL,
                                    count      INTEGER  DEFAULT 1,
                                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    last_seen  DATETIME DEFAULT CURRENT_TIMESTAMP
                                )
                                ''')

            self.conn.commit()

    def execute(self, query, params=None):
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchall(self):
        return self.cursor.fetchall()
    def fetchone(self):
        return self.cursor.fetchone()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sortie du context manager - TOUJOURS appelée"""
        try:
            if exc_type is None:
                # Pas d'erreur : on commit les changements
                self.conn.commit()
            else:
                # Il y a eu une erreur : on rollback
                print(f"erreur cote db honeypote : {exc_type.__name__}: {exc_val}")
                self.conn.rollback()
        finally:
            # Dans tous les cas : on ferme la connexion
            self.conn.close()

class DatabaseManagerUser:
    def __init__(self):
        self.conn = sqlite3.connect(users_db)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self


    def create_db(self):
        self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users
                           (
                               id INTEGER PRIMARY KEY,
                               username TEXT UNIQUE NOT NULL,
                               password TEXT NOT NULL,
                               otp_code TEXT UNIQUE,
                               otp_active INTEGER DEFAULT 0
                           )
                        ''')

        self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS api_keys
                            (
                                id INTEGER PRIMARY KEY,
                                name TEXT UNIQUE NOT NULL,
                                key TEXT UNIQUE NOT NULL,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                            )
        ''')

        self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS log_attempt_account 
                        (
                            id INTEGER PRIMARY KEY,
                            account_id INTEGER,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL ,
                            ip_address TEXT NOT NULL,
                            status TEXT NOT NULL ,
                            FOREIGN KEY (account_id) REFERENCES users (id)
                        )
        ''')

        User = "Admin"
        # Check if admin user already exists
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (User,))
        existing_admin = self.cursor.fetchone()

        if not existing_admin:
            raw_password = generate_random_string(16)
            password = hashlib.sha256(raw_password.encode()).hexdigest()

            self.cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)",
                                (generate_custom_snowflake(User), User, password))
            print(f"Admin user created with password: {raw_password}")
        

    def execute(self, query, params=None):
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)


    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # Pas d'erreur : on commit les changements
                self.conn.commit()
            else:
                # Il y a eu une erreur : on rollback
                print(f"erreur cote db cliente : {exc_type.__name__}: {exc_val}")
                self.conn.rollback()
        finally:
            # Dans tous les cas : on ferme la connexion
            self.conn.close()
