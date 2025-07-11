import sqlite3
import os
import string
import time
import hashlib
import secrets


def generate_custom_snowflake(username: str) -> int:
    # Paramètres
    SEQUENCE_BITS = os.urandom(1)[0] % 10 + 12
    WORKER_ID_BITS = os.urandom(1)[0] % 4 + 5
    DATACENTER_ID_BITS = os.urandom(1)[0] % 4 + 2

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
    datacenter_id = secrets.randbelow(MAX_DATACENTER_ID + 1)  # de 0 à 31 inclus
    worker_id = secrets.randbelow(MAX_WORKER_ID + 1)          # de 0 à 31 inclus

    # Générer une "sequence" pseudo-aléatoire basée sur username + timestamp
    hash_input = f"{username}-{timestamp}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    sequence = int(hash_digest[:3], 16) & MAX_SEQUENCE  # Prendre 3 caractères hex (max 4095)

    # Construction de l'ID
    snowflake = (
        ((timestamp - EPOCH) << TIMESTAMP_LEFT_SHIFT) |
        (datacenter_id << DATACENTER_ID_SHIFT) |
        (worker_id << WORKER_ID_SHIFT) |
        sequence
    )

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
                               id       INTEGER,
                               username TEXT UNIQUE NOT NULL,
                               password TEXT        NOT NULL,
                               otp_code      TEXT UNIQUE,
                               otp_active INTEGER DEFAULT 0
                               
                           )
                           ''')


            raw_password = generate_random_string(16)
            password = hashlib.sha512(raw_password.encode()).hexdigest()

            User = "Admin"

            cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", (generate_custom_snowflake(User), User, password, ))
            print(f"Admin user created with password: {raw_password}")


