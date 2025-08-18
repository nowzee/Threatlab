import sqlite3
import os
import string
import time
import hashlib
import secrets


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


def setup_dbs():
    if not os.path.exists('honeypot.db'):
        with sqlite3.connect('honeypot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS users
                           (
                               id INTEGER PRIMARY KEY,
                               username TEXT UNIQUE NOT NULL,
                               password TEXT NOT NULL,
                               otp_code TEXT UNIQUE,
                               otp_active INTEGER DEFAULT 0
                           )
                           ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS honey_agents
                           (
                               id INTEGER PRIMARY KEY,
                               agent_name TEXT UNIQUE NOT NULL,
                               secret_token TEXT UNIQUE NOT NULL
                           )
                           ''')

            # Table pour stocker les logs d'attaques
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS attack_logs
                           (
                               id               INTEGER PRIMARY KEY,
                               agent_id         INTEGER,
                               source_ip        TEXT NOT NULL,
                               source_port      INTEGER,
                               target_port      INTEGER,
                               service_type     TEXT NOT NULL,
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

            # Table pour les IP malveillantes classifiées
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS malicious_ips
                           (
                               id               INTEGER PRIMARY KEY,
                               ip_address       TEXT UNIQUE NOT NULL,
                               first_seen       DATETIME DEFAULT CURRENT_TIMESTAMP,
                               last_seen        DATETIME DEFAULT CURRENT_TIMESTAMP,
                               attack_count     INTEGER  DEFAULT 1,
                               attack_types     TEXT,
                               services_attacked TEXT,
                               country_code     TEXT,
                               country_name     TEXT,
                               seen_in_agents   TEXT NOT NULL,
                               reputation_score INTEGER  DEFAULT 0,
                               classification   TEXT,
                               notes            TEXT
                           )
                           ''')

            # Table pour les payloads et malwares
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS payloads
                           (
                               id              INTEGER PRIMARY KEY,
                               malicious_ip_id INTEGER,
                               payload_name    TEXT NOT NULL,
                               payload_hash    TEXT UNIQUE NOT NULL,
                               payload_content TEXT,
                               payload_type    TEXT,
                               malware_family  TEXT,
                               first_seen      DATETIME DEFAULT CURRENT_TIMESTAMP,
                               last_seen       DATETIME DEFAULT CURRENT_TIMESTAMP,
                               detection_count INTEGER  DEFAULT 1,
                               FOREIGN KEY (malicious_ip_id) REFERENCES malicious_ips (id)
                           )
                           ''')

            raw_password = generate_random_string(16)
            password = hashlib.sha256(raw_password.encode()).hexdigest()

            User = "Admin"

            cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)",
                           (generate_custom_snowflake(User), User, password))
            print(f"Admin user created with password: {raw_password}")