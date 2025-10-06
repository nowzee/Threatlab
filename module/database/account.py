"""
Account management module.

Provides functions for password changes and login attempt logging.
"""
import hashlib
from module.database.db_manager import DatabaseManagerUser


def change_password_account(username: str, old_password: str, new_password: str) -> bool:
    """
    Change user account password.

    Verifies the old password and updates it with the new one if valid.

    Args:
        username (str): Username of the account.
        old_password (str): Current password (plaintext).
        new_password (str): New password to set (plaintext).

    Returns:
        bool: True if password was changed successfully, False otherwise.
    """
    old_password = hashlib.sha256(old_password.encode()).hexdigest()

    with DatabaseManagerUser() as db:
        db.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, old_password))
        result = db.fetchone()
        if result:
            new_password = hashlib.sha256(new_password.encode()).hexdigest()
            db.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, result[0]))
            return True
        else:
            return False


def log_attempt_account(account_name: str, ip_address: str, status: str) -> bool:
    """
    Log a login attempt for an account.

    Records login attempts (successful or failed) with IP address and status.

    Args:
        account_name (str): Username attempting to login.
        ip_address (str): IP address of the login attempt.
        status (str): Status of the attempt (e.g., 'Successful login', 'Failed login').

    Returns:
        bool: True if the account exists, False if account not found.
    """
    with DatabaseManagerUser() as db:
        db.execute("SELECT id FROM users WHERE username = ?", (account_name,))
        result = db.fetchone()

        if result is None:
            db.execute(
                "INSERT INTO log_attempt_account (ip_address, status) VALUES (?, ?)",
                (ip_address, status)
            )

            return False

        account_id = result[0]

        db.execute("INSERT INTO log_attempt_account (ip_address, status, account_id) VALUES (?, ?, ?)", (ip_address, status, account_id))

        return True