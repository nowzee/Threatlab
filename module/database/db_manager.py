"""
Module de gestion des bases de données SQLite pour le système Threatlabs.

Ce module fournit deux gestionnaires de contexte pour interagir avec les bases de données:
- DatabaseManagerHoneypot: Gestion des agents honeypot et des logs d'attaques
- DatabaseManagerUser: Gestion des utilisateurs et des clés API
"""
from typing import Optional, List, Tuple, Any
import sqlite3
import time
import string
import secrets
import hashlib

honeypot_db = 'db/honeypot.db'
users_db = 'db/user.db'


def generate_custom_snowflake(username: str) -> int:
    """
    Génère un identifiant unique de type Snowflake pour un utilisateur.

    Cette fonction crée un ID unique basé sur un timestamp, un datacenter ID,
    un worker ID et une séquence générée à partir du nom d'utilisateur.

    Args:
        username (str): Nom d'utilisateur pour lequel générer l'ID.

    Returns:
        int: Identifiant Snowflake unique.
    """
    # === Snowflake ID bit allocation ===
    # Sequence: 12 bits (0-4095) - incremental counter for same millisecond
    # Worker ID: 5 bits (0-31) - identifies which worker/process generated the ID
    # Datacenter ID: 5 bits (0-31) - identifies which datacenter
    # Timestamp: 42 bits (remaining) - milliseconds since custom epoch
    SEQUENCE_BITS = 12
    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5

    # Calculate maximum values for each component using bit shifting
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095
    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1  # 31
    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1  # 31

    # Calculate bit shift positions for each component
    WORKER_ID_SHIFT = SEQUENCE_BITS  # 12
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS  # 17
    TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS  # 22

    # Custom epoch: January 1st, 2020 in milliseconds
    EPOCH = 1577836800000

    # Get current timestamp in milliseconds since epoch
    timestamp = int(time.time() * 1000)

    # Generate random datacenter and worker IDs
    datacenter_id = secrets.randbelow(MAX_DATACENTER_ID + 1)
    worker_id = secrets.randbelow(MAX_WORKER_ID + 1)

    # Generate pseudo-random sequence based on username and timestamp
    # Use SHA256 hash to ensure uniqueness
    hash_input = f"{username}-{timestamp}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    # Take first 3 hex characters (12 bits) and apply bitmask
    sequence = int(hash_digest[:3], 16) & MAX_SEQUENCE

    # Construct the Snowflake ID by combining all components with bit shifts
    # Format: [timestamp][datacenter_id][worker_id][sequence]
    snowflake = (
            ((timestamp - EPOCH) << TIMESTAMP_LEFT_SHIFT) |
            (datacenter_id << DATACENTER_ID_SHIFT) |
            (worker_id << WORKER_ID_SHIFT) |
            sequence
    )
    print(f"Snowflake ID generated for {username}: {snowflake}")

    return snowflake

def generate_random_string(length: int = 12) -> str:
    """
    Génère une chaîne aléatoire alphanumérique.

    Args:
        length (int, optional): Longueur de la chaîne à générer. Par défaut 12.

    Returns:
        str: Chaîne aléatoire de la longueur spécifiée.
    """
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

class DatabaseManagerHoneypot:
    """
    Gestionnaire de contexte pour la base de données Honeypot.

    Cette classe gère les connexions à la base de données SQLite contenant
    les informations sur les agents honeypot, les logs d'attaques, les IPs
    malveillantes et les payloads capturés.

    Attributes:
        conn (sqlite3.Connection): Connexion à la base de données.
        cursor (sqlite3.Cursor): Curseur pour exécuter les requêtes SQL.
    """

    def __init__(self) -> None:
        """Initialise la connexion à la base de données honeypot."""
        self.conn = sqlite3.connect(honeypot_db)
        self.cursor = self.conn.cursor()

    def __enter__(self) -> 'DatabaseManagerHoneypot':
        """
        Entre dans le contexte du gestionnaire.

        Returns:
            DatabaseManagerHoneypot: L'instance elle-même.
        """
        return self

    def create_db(self) -> None:
        """
        Crée toutes les tables nécessaires pour la base de données honeypot.

        Crée les tables suivantes si elles n'existent pas:
        - honey_agents: Informations sur les agents honeypot
        - groups_agent: Groupes d'agents
        - attack_logs: Logs des attaques détectées
        - malicious_ips: IPs malveillantes détectées
        - ip_agent_relations: Relations entre IPs et agents
        - ip_service_attacks: Attaques par service
        - payloads: Payloads et malwares capturés
        - smtp_interactions: Interactions SMTP spécifiques
        - compromised_credentials: Credentials compromis collectés
        - password_attempted: Mots de passe tentés
        - username_viewed: Noms d'utilisateur observés
        """
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS honey_agents
                                (
                                    id                  INTEGER PRIMARY KEY,
                                    agent_name          TEXT UNIQUE NOT NULL,
                                    ip_address          TEXT        NOT NULL,
                                    country_name        TEXT,
                                    service_type        TEXT        NOT NULL,
                                    groupe              TEXT,
                                    banner              TEXT,
                                    alert_generated     INTEGER DEFAULT 0,
                                    is_active           INTEGER  DEFAULT 0,
                                    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    secret_token_sha256 TEXT UNIQUE
                                )
                                ''')

            # Add banner column to existing tables if it doesn't exist
            try:
                self.cursor.execute("ALTER TABLE honey_agents ADD COLUMN banner TEXT")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Table des groupes pour les agents
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups_agent
            (
                id INTEGER PRIMARY KEY,
                group_name TEXT NOT NULL
            )
                                ''')

            # Table pour stocker les logs d'attaques
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS attack_logs
                                (
                                    id               INTEGER PRIMARY KEY,
                                    created_at       DATETIME,
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

    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> None:
        """
        Exécute une requête SQL.

        Args:
            query (str): Requête SQL à exécuter.
            params (Optional[Tuple[Any, ...]], optional): Paramètres de la requête. Par défaut None.
        """
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchall(self) -> List[Tuple[Any, ...]]:
        """
        Récupère tous les résultats de la dernière requête.

        Returns:
            List[Tuple[Any, ...]]: Liste de tuples contenant les résultats.
        """
        return self.cursor.fetchall()

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """
        Récupère le premier résultat de la dernière requête.

        Returns:
            Optional[Tuple[Any, ...]]: Tuple contenant le résultat, ou None si aucun résultat.
        """
        return self.cursor.fetchone()

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        """
        Sortie du context manager.

        Commit les changements si aucune erreur n'est survenue, sinon rollback.
        Ferme toujours la connexion à la base de données.

        Args:
            exc_type (Optional[type]): Type d'exception si une erreur est survenue.
            exc_val (Optional[BaseException]): Instance de l'exception.
            exc_tb (Optional[Any]): Traceback de l'exception.
        """
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
    """
    Gestionnaire de contexte pour la base de données utilisateurs.

    Cette classe gère les connexions à la base de données SQLite contenant
    les informations sur les utilisateurs, les clés API et les logs de connexion.

    Attributes:
        conn (sqlite3.Connection): Connexion à la base de données.
        cursor (sqlite3.Cursor): Curseur pour exécuter les requêtes SQL.
    """

    def __init__(self) -> None:
        """Initialise la connexion à la base de données utilisateurs."""
        self.conn = sqlite3.connect(users_db)
        self.cursor = self.conn.cursor()

    def __enter__(self) -> 'DatabaseManagerUser':
        """
        Entre dans le contexte du gestionnaire.

        Returns:
            DatabaseManagerUser: L'instance elle-même.
        """
        return self

    def create_db(self) -> None:
        """
        Crée toutes les tables nécessaires pour la base de données utilisateurs.

        Crée les tables suivantes si elles n'existent pas:
        - users: Informations des utilisateurs
        - api_keys: Clés API pour les intégrations
        - log_attempt_account: Logs des tentatives de connexion

        Crée également un utilisateur Admin par défaut si aucun n'existe.
        """
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
                                integration TEXT,
                                created_at DATETIME,
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
        

    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> None:
        """
        Exécute une requête SQL.

        Args:
            query (str): Requête SQL à exécuter.
            params (Optional[Tuple[Any, ...]], optional): Paramètres de la requête. Par défaut None.
        """
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchall(self) -> List[Tuple[Any, ...]]:
        """
        Récupère tous les résultats de la dernière requête.

        Returns:
            List[Tuple[Any, ...]]: Liste de tuples contenant les résultats.
        """
        return self.cursor.fetchall()

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        """
        Récupère le premier résultat de la dernière requête.

        Returns:
            Optional[Tuple[Any, ...]]: Tuple contenant le résultat, ou None si aucun résultat.
        """
        return self.cursor.fetchone()

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        """
        Sortie du context manager.

        Commit les changements si aucune erreur n'est survenue, sinon rollback.
        Ferme toujours la connexion à la base de données.

        Args:
            exc_type (Optional[type]): Type d'exception si une erreur est survenue.
            exc_val (Optional[BaseException]): Instance de l'exception.
            exc_tb (Optional[Any]): Traceback de l'exception.
        """
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
