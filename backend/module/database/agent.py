"""
Module for managing honeypot agents and attack data.

This module provides the functions to create and manage honeypot agents,
record attacks, manage malicious IPs and generate reports.
"""
from typing import Optional, Tuple, Dict, List, Any
from module.database.db_manager import DatabaseManagerHoneypot
from datetime import datetime
import jwt
import os
import hashlib
from flask import current_app


def _clip(value: Any, max_len: int) -> Optional[str]:
    """
    Truncate a value to the maximum length of a VARCHAR column.

    Honeypots receive arbitrary and potentially oversized input (overflow,
    malicious payloads). Truncating upfront avoids MySQL 1406 "Data too long"
    errors that made the attack record fail (HTTP 500).

    Args:
        value: Value to insert (str or None).
        max_len: Maximum length of the target column.

    Returns:
        The truncated string, or None if the value is None.
    """
    if value is None:
        return None
    s = value if isinstance(value, str) else str(value)
    return s[:max_len]


def generate_jwt(agent_id: int) -> str:
    """
    Generates a unique JWT for a specific agent.

    Args:
        agent_id (int): Identifier of the honeypot agent.

    Returns:
        str: Signed JWT token containing the agent ID and a nonce.
    """
    secret_key = current_app.config.get('AGENT_SECRET_KEY') or current_app.config['SECRET_KEY']
    payload_to_encode = {
        'agent_id': agent_id,
        'nonce': os.urandom(16).hex()  # Add random nonce for uniqueness and replay protection
    }
    # Sign token with HS256 algorithm for agent authentication
    token = jwt.encode(payload_to_encode, secret_key, algorithm='HS256')
    return token


def create_agent_token(agent_name: str,
                       ip_address: str = "0.0.0.0",
                       country_name: Optional[str] = None,
                       service_type: str = "ssh",
                       banner: Optional[str] = None,
                       interactive: bool = True,
                       allow_upload: bool = True,
                       owner_id: Optional[int] = None,
                       auth_mode: str = 'any',
                       auth_whitelist: Optional[str] = None,
                       port: Optional[str] = None) -> Tuple[Optional[int], Optional[str]]:
    """
    Creates a record for a new honeypot agent and generates a unique token.

    Args:
        agent_name (str): Name of the honeypot agent.
        ip_address (str, optional): IP address of the agent. Defaults to "0.0.0.0".
        country_name (Optional[str], optional): Name of the country where the agent is deployed. Defaults to None.
        service_type (str, optional): Type of simulated service (ssh, smtp, ftp, etc.). Defaults to "ssh".
        banner (Optional[str], optional): Banner of the simulated service. Defaults to None.
        interactive (bool, optional): Enable interactive mode (SSH shell / FTP session). Defaults to True.
        allow_upload (bool, optional): Allow file uploads (SFTP/SCP for SSH, STOR for FTP). Defaults to True.
        owner_id (Optional[int], optional): id of the user creating the agent (ownership). Defaults to None.

    Returns:
        Tuple[Optional[int], Optional[str]]: (agent_id, secret_token) if successful, otherwise (None, None).
    """
    try:
        print(f"[DEBUG] Starting create_agent_token for: {agent_name}")
        with DatabaseManagerHoneypot() as db:
            db.execute("""
                INSERT INTO honey_agents (agent_name, ip_address, country_name, service_type, banner, interactive, allow_upload, owner_id, auth_mode, auth_whitelist, port)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (agent_name, ip_address, country_name, service_type, banner,
                  1 if interactive else 0, 1 if allow_upload else 0, owner_id,
                  auth_mode if auth_mode in ('any', 'whitelist') else 'any', auth_whitelist, port))

            # Step 2: Get the auto-generated ID of the newly inserted agent
            agent_id = db.cursor.lastrowid
            # Step 3: Generate JWT token using agent_id and hash it with SHA-256
            # We store the hash only for security, return plaintext token to agent
            secret_token = generate_jwt(agent_id)
            secret_token_sha256 = hashlib.sha256(secret_token.encode()).hexdigest()

            # Step 4: Update agent record with token hash for future authentication
            db.execute("""
                UPDATE honey_agents
                SET secret_token_sha256 = %s
                WHERE id = %s
            """, (secret_token_sha256, agent_id))

            print(f"Agent {agent_id} created with token {secret_token}")

            return agent_id, secret_token

    except Exception as e:
        import traceback
        print(f"[ERROR] Error creating agent token: {e}")
        print(f"[ERROR] Full traceback:")
        print(traceback.format_exc())
        return None, None

def add_malicious_ip_address(agent_id: int,
                            ip_address: str,
                            service_type: str,
                            country_name: Optional[str] = None,
                            country_code: Optional[str] = None,
                            classification: Optional[str] = None) -> bool:
    """
    Adds or updates a malicious IP with its normalized relations.

    Handles recording the IP, the IP-Agent relation and the IP-Service attack counter.

    Args:
        agent_id (int): Identifier of the honeypot agent.
        ip_address (str): Malicious IP address.
        service_type (str): Type of targeted service (ssh, smtp, ftp, etc.).
        country_name (Optional[str], optional): Name of the country of origin. Defaults to None.
        country_code (Optional[str], optional): Country code (ISO). Defaults to None.
        classification (Optional[str], optional): Threat classification. Defaults to None.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # Step 1: Check if IP already exists in malicious_ips table
            db.execute("SELECT id, total_attack_count FROM malicious_ips WHERE ip_address = %s", (ip_address,))
            existing_ip = db.fetchone()

            if existing_ip:
                ip_id = existing_ip['id']
                total_attack_count = existing_ip['total_attack_count']
                new_total_count = total_attack_count + 1

                db.execute("""UPDATE malicious_ips
                              SET last_seen          = CURRENT_TIMESTAMP,
                                  total_attack_count = %s,
                                  country_name       = COALESCE(%s, country_name),
                                  country_code       = COALESCE(%s, country_code),
                                  classification     = COALESCE(%s, classification)
                              WHERE id = %s""",
                           (new_total_count, country_name, country_code, classification, ip_id))
            else:
                # Insert new IP
                db.execute("""INSERT INTO malicious_ips
                                  (ip_address, country_name, country_code, classification)
                              VALUES (%s, %s, %s, %s)""",
                           (ip_address, country_name, country_code, classification))

                # Retrieve the auto-generated ID
                db.execute("SELECT id FROM malicious_ips WHERE ip_address = %s", (ip_address,))
                ip_id = db.fetchone()['id']

            # Step 2: Update many-to-many relationship between IP and Agent
            _update_ip_agent_relation(db, ip_id, agent_id)

            # Step 3: Update attack counter for this IP-Service combination
            _update_ip_service_attacks(db, ip_id, service_type)

            return True
    except Exception as e:
        print(f"Error adding malicious IP address: {e}")
        return False

def _update_ip_agent_relation(db: DatabaseManagerHoneypot, ip_id: int, agent_id: int) -> None:
    """
    Updates the relation between an IP and an agent (helper function).

    Args:
        db (DatabaseManagerHoneypot): Instance of the database manager.
        ip_id (int): Identifier of the malicious IP.
        agent_id (int): Identifier of the honeypot agent.

    Raises:
        Exception: If an error occurs during the update.
    """
    try:
        # Check if this IP has already been seen by this specific agent
        db.execute("SELECT id, report_count FROM ip_agent_relations WHERE ip_id = %s AND agent_id = %s",
                  (ip_id, agent_id))
        existing_relation = db.fetchone()

        if existing_relation:
            # Relationship exists - increment counter to track frequency
            relation_id = existing_relation['id']
            report_count = existing_relation['report_count']
            new_report_count = report_count + 1
            db.execute("""UPDATE ip_agent_relations
                         SET last_seen = CURRENT_TIMESTAMP, report_count = %s
                         WHERE id = %s""",
                      (new_report_count, relation_id))
        else:
            # First time this IP has attacked this agent - create new relation
            db.execute("""INSERT INTO ip_agent_relations (ip_id, agent_id)
                         VALUES (%s, %s)""", (ip_id, agent_id))
    except Exception as e:
        print(f"Error updating IP-Agent relationship: {e}")
        raise

def _update_ip_service_attacks(db: DatabaseManagerHoneypot, ip_id: int, service_type: str) -> None:
    """
    Updates the IP-Service attack counter (helper function).

    Args:
        db (DatabaseManagerHoneypot): Instance of the database manager.
        ip_id (int): Identifier of the malicious IP.
        service_type (str): Type of targeted service.

    Raises:
        Exception: If an error occurs during the update.
    """
    try:
        # Check if this IP has targeted this service type before
        db.execute("SELECT id, attack_count FROM ip_service_attacks WHERE ip_id = %s AND service_type = %s",
                  (ip_id, service_type))
        existing_service = db.fetchone()

        if existing_service:
            # IP has attacked this service before - increment counter
            service_id = existing_service['id']
            attack_count = existing_service['attack_count']
            new_attack_count = attack_count + 1
            db.execute("""UPDATE ip_service_attacks
                         SET last_seen = CURRENT_TIMESTAMP, attack_count = %s
                         WHERE id = %s""",
                      (new_attack_count, service_id))
        else:
            # First time this IP targets this service type - create new record
            db.execute("""INSERT INTO ip_service_attacks (ip_id, service_type)
                         VALUES (%s, %s)""", (ip_id, service_type))
    except Exception as e:
        print(f"Error updating IP-Service attacks: {e}")
        raise

def add_compromised_credential(malicious_ip: str,
                              username: str,
                              password: str,
                              service_type: str) -> bool:
    """
    Adds or updates compromised credentials.

    Also updates the global statistics of observed usernames and passwords.

    Args:
        malicious_ip (str): Malicious IP address.
        username (str): Attempted username.
        password (str): Attempted password.
        service_type (str): Type of targeted service.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    try:
        # Truncate to the column limits (VARCHAR(255)/VARCHAR(50)) so that the
        # lookup and the insertion are consistent and do not fail on oversized
        # malicious inputs.
        username = _clip(username, 255)
        password = _clip(password, 255)
        service_type = _clip(service_type, 50)

        with DatabaseManagerHoneypot() as db:
            # Lookup the IP ID from the malicious_ips table
            db.execute("SELECT id FROM malicious_ips WHERE ip_address = %s", (malicious_ip,))
            ip_record = db.fetchone()

            if not ip_record:
                print(f"Malicious IP {malicious_ip} not found in database")
                return False

            malicious_ip_id = ip_record['id']

            # Check if this exact credential pair has been tried by this IP before
            db.execute("""SELECT id, attempt_count FROM compromised_credentials
                         WHERE malicious_ip_id = %s AND service_type = %s AND username = %s AND password = %s""",
                      (malicious_ip_id, service_type, username, password))
            existing_credential = db.fetchone()

            if existing_credential:
                # Credential combination exists - increment attempt counter
                credential_id = existing_credential['id']
                attempt_count = existing_credential['attempt_count']
                new_attempt_count = attempt_count + 1
                db.execute("""UPDATE compromised_credentials
                             SET last_seen = CURRENT_TIMESTAMP, attempt_count = %s
                             WHERE id = %s""",
                          (new_attempt_count, credential_id))
            else:
                # New credential combination - insert with initial count of 1
                db.execute("""INSERT INTO compromised_credentials
                             (malicious_ip_id, service_type, username, password)
                             VALUES (%s, %s, %s, %s)""",
                          (malicious_ip_id, service_type, username, password))

            # Update global username statistics for analytics
            db.execute("SELECT id, count FROM username_viewed WHERE username = %s", (username,))
            username_record = db.fetchone()

            if username_record:
                username_id = username_record['id']
                count = username_record['count']
                db.execute("UPDATE username_viewed SET count = %s, last_seen = CURRENT_TIMESTAMP WHERE id = %s",
                          (count + 1, username_id))
            else:
                # First time seeing this username globally
                db.execute("INSERT INTO username_viewed (username) VALUES (%s)", (username,))

            # Update global password statistics for analytics
            db.execute("SELECT id, count FROM password_attempted WHERE password = %s", (password,))
            password_record = db.fetchone()

            if password_record:
                password_id = password_record['id']
                count = password_record['count']
                db.execute("UPDATE password_attempted SET count = %s, last_seen = CURRENT_TIMESTAMP WHERE id = %s",
                          (count + 1, password_id))
            else:
                # First time seeing this password globally
                db.execute("INSERT INTO password_attempted (password) VALUES (%s)", (password,))

            return True
    except Exception as e:
        print(f"Error adding compromised credential: {e}")
        return False

def add_attack_log(attack_data: Dict[str, Any]) -> bool:
    """
    Inserts an attack log into the database with the current timestamp.

    Args:
        attack_data (Dict[str, Any]): Dictionary containing the attack data:
            - agent_id: Identifier of the agent
            - source_ip: Source IP of the attack
            - source_port: Source port
            - target_port: Targeted port
            - service_type: Type of service
            - username_attempt: Username attempt (optional)
            - password_attempt: Password attempt (optional)
            - payload: Captured payload (optional)
            - malware_hash: Malware hash (optional)
            - classification: Attack type (optional)
            - country_code: Country code (optional)
            - country_name: Country name (optional)

    Returns:
        bool: True if the insertion succeeded, False otherwise.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            db.execute("""INSERT INTO attack_logs
                         (agent_id, source_ip, source_port, target_port, service_type,
                          username_attempt, password_attempt, payload, malware_hash,
                          attack_type, country_code, country_name)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                      (attack_data.get('agent_id'),
                       _clip(attack_data.get('source_ip'), 45),
                       attack_data.get('source_port'),
                       attack_data.get('target_port'),
                       _clip(attack_data.get('service_type'), 50),
                       _clip(attack_data.get('username_attempt'), 255),
                       _clip(attack_data.get('password_attempt'), 255),
                       attack_data.get('payload'),
                       _clip(attack_data.get('malware_hash'), 255),
                       _clip(attack_data.get('classification'), 50),
                       _clip(attack_data.get('country_code'), 10),
                       _clip(attack_data.get('country_name'), 100)))
            return True
    except Exception as e:
        print(f"Error adding attack log: {e}")
        return False

def add_attack_logs_batch(rows: List[Dict[str, Any]]) -> bool:
    """
    Insert several attack logs in a single query (batch insert).

    Used by the async ingestion worker to absorb high volume: one multi-row
    query instead of one INSERT per attack greatly reduces SQL round-trips.

    Args:
        rows (List[Dict[str, Any]]): List of attack dicts (same keys as
            add_attack_log).

    Returns:
        bool: True if the insert succeeded, False otherwise.
    """
    if not rows:
        return True
    try:
        with DatabaseManagerHoneypot() as db:
            params = [
                (r.get('agent_id'),
                 _clip(r.get('source_ip'), 45),
                 r.get('source_port'),
                 r.get('target_port'),
                 _clip(r.get('service_type'), 50),
                 _clip(r.get('username_attempt'), 255),
                 _clip(r.get('password_attempt'), 255),
                 r.get('payload'),
                 _clip(r.get('malware_hash'), 255),
                 _clip(r.get('classification'), 50),
                 _clip(r.get('country_code'), 10),
                 _clip(r.get('country_name'), 100))
                for r in rows
            ]
            db.executemany("""INSERT INTO attack_logs
                         (agent_id, source_ip, source_port, target_port, service_type,
                          username_attempt, password_attempt, payload, malware_hash,
                          attack_type, country_code, country_name)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", params)
            return True
    except Exception as e:
        print(f"Error adding attack log batch ({len(rows)} rows): {e}")
        return False


_uploaded_files_table_ready = False


def _ensure_uploaded_files_table(db) -> None:
    """Create the uploaded_files table if missing (existing deployments)."""
    global _uploaded_files_table_ready
    if _uploaded_files_table_ready:
        return
    db.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_hash VARCHAR(64) UNIQUE NOT NULL,
            file_name VARCHAR(255),
            file_size BIGINT,
            stored_path VARCHAR(512),
            source_ip VARCHAR(45),
            username VARCHAR(255),
            password VARCHAR(255),
            request_headers TEXT,
            agent_id BIGINT,
            service_type VARCHAR(50),
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            upload_count INT DEFAULT 1
        )
    """)
    _uploaded_files_table_ready = True


def upload_hash_exists(file_hash: str) -> bool:
    """Return whether a file with this hash has already been recorded."""
    try:
        with DatabaseManagerHoneypot() as db:
            _ensure_uploaded_files_table(db)
            db.execute("SELECT id FROM uploaded_files WHERE file_hash = %s", (file_hash,))
            return db.fetchone() is not None
    except Exception as e:
        print(f"Error checking upload hash: {e}")
        return False


def record_uploaded_file(file_hash: str, file_name: str, file_size: int, stored_path: str,
                         source_ip: str, username: str, password: str, request_headers: str,
                         agent_id: Optional[int], service_type: str) -> bool:
    """
    Record an uploaded file (deduplicated by hash).

    Atomic INSERT with ON DUPLICATE KEY UPDATE: a hash already seen just bumps
    the counter and refreshes the last observed name, without duplicating the row.

    Returns:
        bool: True if the record was stored successfully.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            _ensure_uploaded_files_table(db)
            db.execute("""
                INSERT INTO uploaded_files
                    (file_hash, file_name, file_size, stored_path, source_ip,
                     username, password, request_headers, agent_id, service_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    last_seen = CURRENT_TIMESTAMP,
                    upload_count = upload_count + 1,
                    file_name = VALUES(file_name)
            """, (file_hash, _clip(file_name, 255), file_size, _clip(stored_path, 512),
                  _clip(source_ip, 45), _clip(username, 255), _clip(password, 255),
                  request_headers, agent_id, _clip(service_type, 50)))
            return True
    except Exception as e:
        print(f"Error recording uploaded file: {e}")
        return False


_UPLOAD_COLS = ("file_hash, file_name, file_size, stored_path, source_ip, username, "
                "password, service_type, agent_id, upload_count, first_seen, last_seen")


def get_uploaded_files_page(page: int = 1, limit: int = 10, q: Optional[str] = None) -> Dict[str, Any]:
    """
    Paginated list of captured files.

    If `q` is given, returns files whose metadata (name, ip, user, hash) OR
    file content contains the string. Returns {items, total, page, limit}.
    """
    page = max(1, int(page))
    limit = max(1, min(100, int(limit)))
    try:
        with DatabaseManagerHoneypot() as db:
            _ensure_uploaded_files_table(db)

            if not q:
                db.execute("SELECT COUNT(*) AS c FROM uploaded_files")
                total = db.fetchone()['c']
                db.execute("SELECT " + _UPLOAD_COLS + " FROM uploaded_files "
                           "ORDER BY last_seen DESC LIMIT %s OFFSET %s",
                           (limit, (page - 1) * limit))
                rows = db.fetchall()
                return {'items': rows, 'total': total, 'page': page, 'limit': limit}

            # Search: scan recent files, match metadata then file content.
            db.execute("SELECT " + _UPLOAD_COLS + " FROM uploaded_files "
                       "ORDER BY last_seen DESC LIMIT 3000")
            candidates = db.fetchall()

        ql = q.lower()
        qb = q.encode('utf-8', 'ignore')
        matches = []
        for r in candidates:
            meta = ' '.join(str(r.get(k) or '') for k in
                            ('file_name', 'source_ip', 'username', 'password', 'file_hash')).lower()
            hit = ql in meta
            if not hit:
                path = r.get('stored_path')
                if path and (r.get('file_size') or 0) <= 10 * 1024 * 1024 and os.path.exists(path):
                    try:
                        with open(path, 'rb') as f:
                            hit = qb in f.read()
                    except Exception:
                        hit = False
            if hit:
                matches.append(r)

        total = len(matches)
        start = (page - 1) * limit
        return {'items': matches[start:start + limit], 'total': total, 'page': page, 'limit': limit}
    except Exception as e:
        print(f"Error listing uploaded files: {e}")
        return {'items': [], 'total': 0, 'page': page, 'limit': limit}


def get_uploaded_file(file_hash: str) -> Optional[Dict[str, Any]]:
    """Return the stored path and name of a captured file by hash."""
    try:
        with DatabaseManagerHoneypot() as db:
            _ensure_uploaded_files_table(db)
            db.execute("SELECT stored_path, file_name FROM uploaded_files WHERE file_hash = %s",
                       (file_hash,))
            return db.fetchone()
    except Exception as e:
        print(f"Error fetching uploaded file: {e}")
        return None


def get_shell_commands_page(status: str = 'all', page: int = 1, limit: int = 10,
                            q: Optional[str] = None) -> Dict[str, Any]:
    """
    Paginated list of observed shell commands.

    Args:
        status: 'all', 'success' (recognized) or 'failed' (command not found).
        page, limit: Pagination.
        q: Optional substring to match against the command text.

    Returns:
        {items, total, page, limit}.
    """
    page = max(1, int(page))
    limit = max(1, min(100, int(limit)))
    try:
        with DatabaseManagerHoneypot() as db:
            where = "attack_type IN ('shell_command', 'shell_command_failed')"
            params: List[Any] = []
            if status == 'success':
                where += " AND attack_type = %s"
                params.append('shell_command')
            elif status == 'failed':
                where += " AND attack_type = %s"
                params.append('shell_command_failed')
            if q:
                where += " AND payload LIKE %s"
                params.append('%' + q + '%')

            db.execute("SELECT COUNT(*) AS c FROM attack_logs WHERE " + where, tuple(params))
            total = db.fetchone()['c']

            db.execute("SELECT id, created_at, source_ip, country_code, agent_id, "
                       "username_attempt, payload, attack_type, service_type "
                       "FROM attack_logs WHERE " + where +
                       " ORDER BY id DESC LIMIT %s OFFSET %s",
                       tuple(params) + (limit, (page - 1) * limit))
            return {'items': db.fetchall(), 'total': total, 'page': page, 'limit': limit}
    except Exception as e:
        print(f"Error listing shell commands: {e}")
        return {'items': [], 'total': 0, 'page': page, 'limit': limit}


def add_smtp_interaction(malicious_ip: str,
                        sender_email: str,
                        recipient_email: str,
                        subject: str,
                        message_content: str,
                        attachments: Optional[List[str]] = None) -> bool:
    """
    Inserts an SMTP interaction into the database.

    Args:
        malicious_ip (str): IP address of the malicious server.
        sender_email (str): Sender's email.
        recipient_email (str): Recipient's email.
        subject (str): Subject of the email.
        message_content (str): Content of the message.
        attachments (Optional[List[str]], optional): List of attachments. Defaults to None.

    Returns:
        bool: True if the insertion succeeded, False otherwise.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # Get malicious IP ID
            db.execute("SELECT id FROM malicious_ips WHERE ip_address = %s", (malicious_ip,))
            ip_record = db.fetchone()

            if not ip_record:
                print(f"Malicious IP {malicious_ip} not found in database")
                return False

            malicious_ip_id = ip_record['id']

            # Insert SMTP interaction
            import json
            attachments_json = json.dumps(attachments) if attachments else None

            db.execute("""INSERT INTO smtp_interactions
                         (malicious_server_ip_id, sender_email, recipient_email, subject,
                          message_content, attachments)
                         VALUES (%s, %s, %s, %s, %s, %s)""",
                      (malicious_ip_id, sender_email, recipient_email, subject,
                       message_content, attachments_json))
            return True
    except Exception as e:
        print(f"Error adding SMTP interaction: {e}")
        return False

def get_default_metric_data(owner_id: Optional[int] = None) -> Dict[str, int]:
    """
    Retrieves the dashboard's default metrics.

    When ``owner_id`` is given (a non-admin member), the metrics are scoped to
    the honeypots owned by that user; otherwise they are platform-wide (admin).

    Returns:
        Dict[str, int]: {ip_count, Sample_downloaded, number_honeypot, tentative_access}
    """
    with DatabaseManagerHoneypot() as db:
        if owner_id is None:
            db.execute('''
                       SELECT (SELECT COUNT(id) FROM malicious_ips) AS ip_count,
                              (SELECT COUNT(id) FROM payloads)      AS Sample_downloaded,
                              (SELECT COUNT(id) FROM honey_agents)  AS number_honeypot,
                              (SELECT COUNT(id) FROM attack_logs)   AS tentative_access
                       ''')
        else:
            db.execute('''
                SELECT
                    (SELECT COUNT(DISTINCT r.ip_id)
                       FROM ip_agent_relations r
                       JOIN honey_agents ha ON ha.id = r.agent_id
                       WHERE ha.owner_id = %s) AS ip_count,
                    (SELECT COUNT(DISTINCT al.malware_hash)
                       FROM attack_logs al
                       JOIN honey_agents ha ON ha.id = al.agent_id
                       WHERE ha.owner_id = %s AND al.malware_hash IS NOT NULL AND al.malware_hash != '') AS Sample_downloaded,
                    (SELECT COUNT(id) FROM honey_agents WHERE owner_id = %s) AS number_honeypot,
                    (SELECT COUNT(al.id)
                       FROM attack_logs al
                       JOIN honey_agents ha ON ha.id = al.agent_id
                       WHERE ha.owner_id = %s) AS tentative_access
            ''', (owner_id, owner_id, owner_id, owner_id))

        result = db.fetchone()
        return result


def get_agent_details(owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the details of the last 5 attack logs with agent information.

    When ``owner_id`` is given, only logs for that user's honeypots are returned.
    The admin (global) view also exposes the owning user's name.

    Returns:
        List[Dict[str, Any]]: List of dictionaries containing the log information.
    """
    with DatabaseManagerHoneypot() as db:
        if owner_id is None:
            db.execute('''
                       SELECT al.country_name,
                              al.source_ip,
                              al.target_port,
                              al.service_type,
                              al.agent_id,
                              ha.agent_name,
                              u.username AS owner_username,
                              al.created_at,
                              al.id
                       FROM attack_logs al
                                LEFT JOIN honey_agents ha ON al.agent_id = ha.id
                                LEFT JOIN users u ON ha.owner_id = u.id
                       ORDER BY al.id DESC
                       LIMIT 5
                       ''')
        else:
            db.execute('''
                       SELECT al.country_name,
                              al.source_ip,
                              al.target_port,
                              al.service_type,
                              al.agent_id,
                              ha.agent_name,
                              al.created_at,
                              al.id
                       FROM attack_logs al
                                JOIN honey_agents ha ON al.agent_id = ha.id
                       WHERE ha.owner_id = %s
                       ORDER BY al.id DESC
                       LIMIT 5
                       ''', (owner_id,))

        return db.fetchall()


def get_country_ranking(owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the country ranking by number of attacks for the dashboard.

    Scoped to the user's honeypots when ``owner_id`` is provided.

    Returns:
        List[Dict[str, Any]]: List of the 10 countries with the most attacks, sorted in descending order.
    """
    with DatabaseManagerHoneypot() as db:
        if owner_id is None:
            db.execute('''
                       SELECT country_name AS country_name,
                              COUNT(*)     AS attack_count
                       FROM attack_logs
                       WHERE country_name IS NOT NULL
                         AND country_name != ''
                       GROUP BY country_name
                       ORDER BY attack_count DESC
                       LIMIT 10
                       ''')
        else:
            db.execute('''
                       SELECT al.country_name AS country_name,
                              COUNT(*)        AS attack_count
                       FROM attack_logs al
                                JOIN honey_agents ha ON al.agent_id = ha.id
                       WHERE ha.owner_id = %s
                         AND al.country_name IS NOT NULL
                         AND al.country_name != ''
                       GROUP BY al.country_name
                       ORDER BY attack_count DESC
                       LIMIT 10
                       ''', (owner_id,))

        return db.fetchall()


def get_password_ranking(owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the ranking of the 5 most attempted passwords.

    Platform-wide by default; when ``owner_id`` is given, computed from the
    attack logs of that user's honeypots only.

    Returns:
        List[Dict[str, Any]]: List of the 5 most popular passwords.
    """
    with DatabaseManagerHoneypot() as db:
        if owner_id is None:
            db.execute('''
                SELECT
                    password,
                    MAX(count) AS count
                FROM password_attempted
                GROUP BY password
                ORDER BY count DESC
                LIMIT 5
            ''')
        else:
            db.execute('''
                SELECT al.password_attempt AS password,
                       COUNT(*)            AS count
                FROM attack_logs al
                         JOIN honey_agents ha ON al.agent_id = ha.id
                WHERE ha.owner_id = %s
                  AND al.password_attempt IS NOT NULL
                  AND al.password_attempt != ''
                GROUP BY al.password_attempt
                ORDER BY count DESC
                LIMIT 5
            ''', (owner_id,))

        return db.fetchall()



class ManagerAgent:
    """
    Class to manage CRUD operations on honeypot agents.
    """

    @staticmethod
    def get_agent_by_id(agent_id: int) -> bool:
        with DatabaseManagerHoneypot() as db:

            db.execute('''SELECT id FROM honey_agents WHERE id = %s''', (int(agent_id),))
            agent = db.fetchone()
            if agent:
                return True
            return False

    @staticmethod
    def remove(agent_id: int, viewer_id: Optional[int] = None, is_admin: bool = True) -> bool:
        """
        Removes a honeypot agent from the database.

        When ``is_admin`` is False, the agent is only removed if it is owned by
        ``viewer_id`` (members can only delete their own honeypots).

        Args:
            agent_id (int): Identifier of the agent to remove.
            viewer_id (Optional[int]): id of the requesting user (for ownership check).
            is_admin (bool): True to bypass the ownership check.

        Returns:
            bool: True if the agent was removed, False if it does not exist or is not owned.
        """
        with DatabaseManagerHoneypot() as db:

            db.execute('''SELECT id, owner_id FROM honey_agents WHERE id = %s''', (int(agent_id),))
            agent = db.fetchone()
            if not agent:
                return False
            # Members may only delete honeypots they own.
            if not is_admin and agent.get('owner_id') != viewer_id:
                return False

            db.execute("UPDATE attack_logs SET agent_id = NULL WHERE agent_id = %s", (int(agent_id),))
            db.execute("DELETE FROM ip_agent_relations WHERE agent_id = %s", (int(agent_id),))
            db.execute("DELETE FROM honey_agents WHERE id = %s", (int(agent_id),))
            return True

    @staticmethod
    def list(viewer_id: Optional[int] = None, is_admin: bool = True) -> List[Dict[str, Any]]:

        owner_column = ", u.username AS owner_username" if is_admin else ""
        owner_join = "LEFT JOIN users u ON ha.owner_id = u.id" if is_admin else ""
        where_clause = "" if is_admin else "WHERE ha.owner_id = %s"
        params = None if is_admin else (viewer_id,)

        with DatabaseManagerHoneypot() as db:
            db.execute(f"""
                       SELECT ha.id,
                              ha.agent_name,
                              ha.ip_address,
                              ha.service_type,
                              COALESCE(a.cnt, 0) AS alert_generated,
                              la.last_activity,
                              ha.created_at,
                              ha.owner_id{owner_column}
                       FROM honey_agents ha
                                {owner_join}
                                LEFT JOIN (SELECT agent_id, COUNT(*) AS cnt
                                           FROM attack_logs
                                           WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                                           GROUP BY agent_id) a ON a.agent_id = ha.id
                                LEFT JOIN (SELECT agent_id, MAX(created_at) AS last_activity
                                           FROM attack_logs
                                           GROUP BY agent_id) la ON la.agent_id = ha.id
                       {where_clause}
                       ORDER BY ha.id DESC
                       """, params)
            return db.fetchall()



# ============= FUNCTIONS FOR REPORT GENERATION =============

def get_wordlist_stats() -> Dict[str, Any]:
    """
    Retrieves the global wordlist statistics (count + total attempts) via COUNT/SUM SQL.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
            SELECT
                (SELECT COUNT(*) FROM password_attempted) AS password_count,
                (SELECT COALESCE(SUM(count), 0) FROM password_attempted) AS password_attempts,
                (SELECT COUNT(*) FROM username_viewed) AS username_count,
                (SELECT COALESCE(SUM(count), 0) FROM username_viewed) AS username_attempts,
                (SELECT COUNT(*) FROM compromised_credentials) AS combo_count,
                (SELECT COALESCE(SUM(attempt_count), 0) FROM compromised_credentials) AS combo_attempts
        ''')
        return db.fetchone()


def get_top_passwords(limit: Optional[int] = 20) -> List[Dict[str, Any]]:
    """
    Retrieves the most attempted passwords.

    Args:
        limit: Maximum number of results. None = all.

    Returns:
        List[Dict[str, Any]]: List of passwords with their number of occurrences.
    """
    with DatabaseManagerHoneypot() as db:
        query = 'SELECT password, count FROM password_attempted WHERE password IS NOT NULL ORDER BY count DESC'
        if limit is not None:
            query += ' LIMIT %s'
            db.execute(query, (limit,))
        else:
            db.execute(query)
        return db.fetchall()


def get_top_usernames(limit: Optional[int] = 20) -> List[Dict[str, Any]]:
    """
    Retrieves the most attempted usernames.

    Args:
        limit: Maximum number of results. None = all.

    Returns:
        List[Dict[str, Any]]: List of usernames with their number of occurrences.
    """
    with DatabaseManagerHoneypot() as db:
        query = 'SELECT username, count FROM username_viewed WHERE username IS NOT NULL ORDER BY count DESC'
        if limit is not None:
            query += ' LIMIT %s'
            db.execute(query, (limit,))
        else:
            db.execute(query)

        return db.fetchall()


def get_service_distribution() -> List[Dict[str, Any]]:
    """
    Retrieves the distribution of attacks by service type.

    Returns:
        List[Dict[str, Any]]: List of targeted services with the number of attacks.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT service_type, COUNT(*) as count
                   FROM attack_logs
                   WHERE service_type IS NOT NULL
                   GROUP BY service_type
                   ORDER BY count DESC
                   ''')

        return db.fetchall()


def get_top_malicious_ips(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieves the most aggressive malicious IPs.

    Args:
        limit (int, optional): Maximum number of results. Defaults to 20.

    Returns:
        List[Dict[str, Any]]: List of IPs with their details and statistics.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT m.ip_address                               AS ip,
                          COALESCE(m.country_name, 'Unknown')        AS country,
                          m.total_attack_count                       AS attacks,
                          COALESCE(m.classification, 'Unclassified') AS classification,
                          m.first_seen,
                          m.last_seen
                   FROM malicious_ips m
                   ORDER BY m.total_attack_count DESC
                   LIMIT %s
                   ''', (limit,))

        return db.fetchall()


def get_attacks_by_day(days: int = 7) -> List[Dict[str, Any]]:
    """
    Retrieves the number of attacks for the last N days.

    Args:
        days (int, optional): Number of days to analyze. Defaults to 7.

    Returns:
        List[Dict[str, Any]]: List of dates with the number of attacks per day.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT DATE(created_at) AS date,
                          COUNT(*)         AS count
                   FROM attack_logs
                   WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                   GROUP BY DATE(created_at)
                   ORDER BY date ASC
                   ''', (days,))

        return db.fetchall()


def get_attacks_by_hour() -> List[Dict[str, Any]]:
    """
    Retrieves the number of attacks per hour for the last 24 hours.

    Returns:
        List[Dict[str, Any]]: List of hours with the number of attacks.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT HOUR(created_at) AS hour,
                          COUNT(*)         AS count
                   FROM attack_logs
                   WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                   GROUP BY HOUR(created_at)
                   ORDER BY hour ASC
                   ''')

        results = db.fetchall()

        data = [
            {
                'hour': f"{row['hour']:02d}:00",
                'count': row['count']
            }
            for row in results
        ]

        return data


def get_agent_statistics() -> List[Dict[str, Any]]:
    """
    Retrieves the statistics for all honeypot agents.

    Returns:
        List[Dict[str, Any]]: List of agents with their detailed statistics.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT ha.id                                AS id,
                          ha.agent_name                        AS name,
                          COALESCE(ha.country_name, 'Unknown') AS country,
                          ha.service_type                      AS service,
                          ha.alert_generated                   AS alerts,
                          ha.created_at                        AS created_at,
                          COUNT(al.id)                         AS total_logs
                   FROM honey_agents ha
                            LEFT JOIN attack_logs al ON ha.id = al.agent_id
                   GROUP BY ha.id
                   ORDER BY total_logs DESC
                   ''')

        return db.fetchall()


def get_payload_statistics() -> List[Dict[str, Any]]:
    """
    Retrieves the statistics on captured payloads/malware.

    Returns:
        List[Dict[str, Any]]: List of payload types with their counter.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT COALESCE(payload_type, 'Unknown')   AS type,
                          COALESCE(malware_family, 'Unknown') AS family,
                          COUNT(*)                            AS count
                   FROM payloads
                   WHERE payload_type IS NOT NULL
                      OR malware_family IS NOT NULL
                   GROUP BY payload_type, malware_family
                   ORDER BY count DESC
                   LIMIT 20
                   ''')

        return db.fetchall()


def get_port_distribution() -> List[Dict[str, Any]]:
    """
    Retrieves the distribution of targeted ports.

    Returns:
        List[Dict[str, Any]]: List of the 10 most targeted ports with their counter.
    """
    with DatabaseManagerHoneypot() as db:
        db.execute('''
                   SELECT target_port AS port,
                          COUNT(*)    AS count
                   FROM attack_logs
                   WHERE target_port IS NOT NULL
                   GROUP BY target_port
                   ORDER BY count DESC
                   LIMIT 10
                   ''')

        return db.fetchall()


def get_credential_combinations(limit: Optional[int] = 15) -> List[Dict[str, Any]]:
    """
    Retrieves the observed username/password combinations, sorted by frequency.

    Args:
        limit: Maximum number of combinations. None = all unique combinations.

    Returns:
        List[Dict[str, Any]]: List of credential combinations with their counter.
    """
    with DatabaseManagerHoneypot() as db:
        query = '''
                SELECT username,
                       password,
                       SUM(attempt_count) AS count
                FROM compromised_credentials
                GROUP BY username, password
                ORDER BY count DESC
                '''
        if limit is not None:
            query += ' LIMIT %s'
            db.execute(query, (limit,))
        else:
            db.execute(query)

        return db.fetchall()


def get_agent_about(agent_id: int, viewer_id: Optional[int] = None,
                    is_admin: bool = True) -> Optional[Dict[str, Any]]:
    """
    Retrieves all the detailed information of a specific honeypot agent.

    When ``is_admin`` is False, returns None unless the agent is owned by
    ``viewer_id`` (hides other users' honeypots — same 404 as "not found").

    Args:
        agent_id (int): Identifier of the agent.
        viewer_id (Optional[int]): id of the requesting user (ownership check).
        is_admin (bool): True to bypass the ownership check.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with the agent details, or None if not found/allowed.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            # 1. Agent base info
            db.execute("""
                SELECT ha.id, ha.agent_name, ha.ip_address, ha.country_name, ha.service_type,
                       ha.banner, ha.alert_generated, ha.created_at, ha.updated_at,
                       ha.owner_id, u.username AS owner_username
                FROM honey_agents ha
                LEFT JOIN users u ON ha.owner_id = u.id
                WHERE ha.id = %s
            """, (agent_id,))
            agent = db.fetchone()

            if not agent:
                return None

            # Members can only inspect their own honeypots.
            if not is_admin and agent.get('owner_id') != viewer_id:
                return None

            # 2. Attack stats
            db.execute("""
                SELECT
                    COUNT(*) AS total_attacks,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) AS attacks_today,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) AS attacks_week,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) AS attacks_month
                FROM attack_logs
                WHERE agent_id = %s
            """, (agent_id,))
            stats = db.fetchone()

            # 3. Unique IPs count
            db.execute("""
                SELECT COUNT(DISTINCT ip_id) AS unique_ips
                FROM ip_agent_relations
                WHERE agent_id = %s
            """, (agent_id,))
            ip_stats = db.fetchone()

            # 4. Top countries for this agent
            db.execute("""
                SELECT country_name, COUNT(*) AS count
                FROM attack_logs
                WHERE agent_id = %s AND country_name IS NOT NULL AND country_name != ''
                GROUP BY country_name
                ORDER BY count DESC
                LIMIT 10
            """, (agent_id,))
            top_countries_raw = db.fetchall()

            total_with_country = sum(c['count'] for c in top_countries_raw) if top_countries_raw else 1
            top_countries = [
                {
                    'country': c['country_name'],
                    'count': c['count'],
                    'percentage': round(c['count'] / total_with_country * 100, 1)
                }
                for c in top_countries_raw
            ]

            # 5. Recent attacks
            db.execute("""
                SELECT id, created_at, source_ip, country_code, country_name,
                       attack_type, service_type, source_port, target_port,
                       username_attempt, password_attempt
                FROM attack_logs
                WHERE agent_id = %s
                ORDER BY id DESC
                LIMIT 20
            """, (agent_id,))
            recent_attacks = db.fetchall()

            # Format attacks for frontend
            formatted_attacks = []
            for a in recent_attacks:
                formatted_attacks.append({
                    'id': a['id'],
                    'timestamp': a['created_at'],
                    'source_ip': a['source_ip'],
                    'country': a['country_code'] or a['country_name'] or 'N/A',
                    'type': a['attack_type'] or a['service_type'] or 'Unknown',
                    'service_type': a['service_type'],
                    'source_port': a['source_port'],
                    'target_port': a['target_port'],
                    'username': a['username_attempt'],
                    'password': a['password_attempt']
                })

            return {
                'id': agent['id'],
                'name': agent['agent_name'],
                'type': agent['service_type'],
                'status': 'active',
                'ip': agent['ip_address'],
                'country': agent['country_name'],
                'banner': agent['banner'],
                'owner_id': agent.get('owner_id'),
                'owner_username': agent.get('owner_username'),
                'alert_generated': agent['alert_generated'],
                'created_at': agent['created_at'],
                'updated_at': agent['updated_at'],
                'stats': {
                    'total_attacks': stats['total_attacks'] or 0,
                    'unique_ips': ip_stats['unique_ips'] or 0,
                    'attacks_today': stats['attacks_today'] or 0,
                    'attacks_week': stats['attacks_week'] or 0,
                    'attacks_month': stats['attacks_month'] or 0,
                },
                'top_countries': top_countries,
                'recent_attacks': formatted_attacks
            }

    except Exception as e:
        print(f"Error getting agent about: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def get_complete_report_data() -> Dict[str, Any]:
    """
    Retrieves all the data needed for a complete report.

    Returns:
        Dict[str, Any]: Dictionary containing all the metrics and statistics:
            - metrics: General metrics
            - country_ranking: Country ranking
            - top_passwords: Most attempted passwords
            - top_usernames: Most attempted usernames
            - service_distribution: Service distribution
            - top_ips: Most aggressive IPs
            - attacks_by_day: Attacks per day
            - attacks_by_hour: Attacks per hour
            - agents: Agent statistics
            - payloads: Payload statistics
            - port_distribution: Port distribution
            - credential_combinations: Credential combinations
    """
    return {
        'metrics': get_default_metric_data(),
        'country_ranking': get_country_ranking(),
        'top_passwords': get_top_passwords(20),
        'top_usernames': get_top_usernames(20),
        'service_distribution': get_service_distribution(),
        'top_ips': get_top_malicious_ips(20),
        'attacks_by_day': get_attacks_by_day(7),
        'attacks_by_hour': get_attacks_by_hour(),
        'agents': get_agent_statistics(),
        'payloads': get_payload_statistics(),
        'port_distribution': get_port_distribution(),
        'credential_combinations': get_credential_combinations()
    }
