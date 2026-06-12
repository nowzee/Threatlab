from mysql.connector import pooling
import os
import time
import string
import secrets
import hashlib

# Configuration de la base de données via variables d'environnement
DB_TYPE = 'mysql'
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'threatlabs_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'threatlabs_password')
DB_NAME = os.getenv('DB_NAME', 'threatlabs')

# Taille du pool configurable (attention : multipliée par le nombre de workers
# gunicorn ; garder workers * DB_POOL_SIZE sous max_connections de MySQL ~151)
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))

# Créer le pool de connexions une seule fois (par processus)
connection_pool = pooling.MySQLConnectionPool(
    pool_name="threatlabs_pool",
    pool_size=DB_POOL_SIZE,
    pool_reset_session=True,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)


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
        self.conn = connection_pool.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)

    def __enter__(self):
        return self

    def create_db(self):
        # En MySQL, le schéma est déjà chargé via schemas.sql dans Docker
        pass

    def execute(self, query, params=None):
        # Adapter le placeholder pour MySQL (%s au lieu de ?)
        query = query.replace('?', '%s')

        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def executemany(self, query, seq_params):
        """Exécute une requête sur une séquence de paramètres (insertion par lot)."""
        query = query.replace('?', '%s')
        self.cursor.executemany(query, seq_params)

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
                print(f"erreur cote db honeypot : {exc_type.__name__}: {exc_val}")
                self.conn.rollback()
        finally:
            # Dans tous les cas : on ferme la connexion
            self.conn.close()

class DatabaseManagerUser:
    def __init__(self):
        self.conn = connection_pool.get_connection()
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def create_db(self):
        # Initialisation spécifique MySQL : créer admin user si nécessaire
        self.create_admin_if_not_exists()

    def create_admin_if_not_exists(self):
        """Créer un utilisateur admin par défaut s'il n'existe pas."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", ('admin',))
            count = self.cursor.fetchone()[0]

            if count == 0:
                # Générer un mot de passe aléatoire
                admin_password = generate_random_string(16)
                admin_id = generate_custom_snowflake('admin')

                from module.crypto_utils.password_hash import hash_password
                password_hash = hash_password(admin_password)

                # Insérer l'utilisateur admin
                self.cursor.execute(
                    "INSERT INTO users (id, username, password) VALUES (%s, %s, %s)",
                    (admin_id, 'admin', password_hash)
                )
                self.conn.commit()
                print(f"Admin user created with password: {admin_password}")
                print(f"IMPORTANT: Save this password, it will not be shown again!")
        except Exception as e:
            print(f"Error creating admin user: {e}")

    def execute(self, query, params=None):
        # Adapter le placeholder pour MySQL (%s au lieu de ?)
        query = query.replace('?', '%s')

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
                print(f"erreur cote db user : {exc_type.__name__}: {exc_val}")
                self.conn.rollback()
        finally:
            # Dans tous les cas : on ferme la connexion
            self.conn.close()
