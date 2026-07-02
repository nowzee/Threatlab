"""
Admin-side user management data layer.

CRUD helpers used by the admin "Utilisateurs" screen. Runs on
``DatabaseManagerUser`` (tuple cursor) — dicts are built by hand. Since ``users``
and ``honey_agents`` live in the same ``threatlabs`` database, cross-table
statements (JOIN, ownership reassignment on delete) execute on one connection.

Role policy: new accounts are always created as ``member``; ``admin`` accounts
are protected from deletion here.
"""
from typing import Any, Dict, List, Optional, Tuple

from module.database.db_manager import DatabaseManagerUser, generate_custom_snowflake
from module.crypto_utils.password_hash import hash_password


def list_users() -> List[Dict[str, Any]]:
    """All users with the number of honeypots they own."""
    with DatabaseManagerUser() as db:
        db.execute("""
            SELECT u.id, u.username, u.role, COUNT(ha.id) AS honeypot_count
            FROM users u
            LEFT JOIN honey_agents ha ON ha.owner_id = u.id
            GROUP BY u.id, u.username, u.role
            ORDER BY u.username
        """)
        rows = db.fetchall()
        return [
            {'id': r[0], 'username': r[1], 'role': r[2], 'honeypot_count': r[3]}
            for r in rows
        ]


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Return {'id','username','role'} for a user id, or None."""
    with DatabaseManagerUser() as db:
        db.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
        r = db.fetchone()
        if not r:
            return None
        return {'id': r[0], 'username': r[1], 'role': r[2]}


def create_member(username: str, password: str) -> Tuple[bool, str, Optional[int]]:
    """
    Create a new account with role 'member' (role is forced, never client-chosen).

    Returns:
        (ok, code, user_id). code is 'ok' | 'invalid_username' | 'username_taken'.
    """
    username = (username or '').strip()
    if not username or len(username) > 140:
        return False, 'invalid_username', None
    with DatabaseManagerUser() as db:
        db.execute("SELECT id FROM users WHERE username = ?", (username,))
        if db.fetchone():
            return False, 'username_taken', None
        user_id = generate_custom_snowflake(username)
        password_hash = hash_password(password)
        db.execute(
            "INSERT INTO users (id, username, password, role) VALUES (?, ?, ?, ?)",
            (user_id, username, password_hash, 'member')
        )
        return True, 'ok', user_id


def delete_user(user_id: int) -> Tuple[bool, str, Optional[str]]:
    """
    Delete a member account.

    Protects admins (cannot be deleted here). The user's honeypots are orphaned
    (owner_id -> NULL, data kept) and login-attempt FK references are cleared,
    then the account is removed — all on one connection/transaction.

    Returns:
        (ok, code, username). code is 'ok' | 'not_found' | 'cannot_delete_admin'.
    """
    with DatabaseManagerUser() as db:
        db.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
        row = db.fetchone()
        if not row:
            return False, 'not_found', None
        uid, uname, role = row[0], row[1], row[2]
        if role == 'admin':
            return False, 'cannot_delete_admin', uname
        db.execute("UPDATE honey_agents SET owner_id = NULL WHERE owner_id = ?", (uid,))
        db.execute("UPDATE log_attempt_account SET account_id = NULL WHERE account_id = ?", (uid,))
        db.execute("DELETE FROM users WHERE id = ?", (uid,))
        return True, 'ok', uname
