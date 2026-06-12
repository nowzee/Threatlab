"""
Authentication and Two-Factor Authentication (2FA) module.

Handles user authentication, 2FA status management and OTP secret handling.
"""
from typing import Optional
from module.database.db_manager import DatabaseManagerUser
from module.crypto_utils.key_manager import Key_manager_db
from module.crypto_utils.password_hash import verify_password


def auth_user(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.

    Args:
        username (str): Username to authenticate.
        password (str): Password in plaintext.

    Returns:
        bool: True if authentication successful, False otherwise.
    """
    with DatabaseManagerUser() as db:
        db.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = db.fetchone()
        if not result:
            return False
        return verify_password(result[0], password)


def a2f_active(username: str) -> bool:
    """
    Check if Two-Factor Authentication is active for a user.

    Args:
        username (str): Username to check.

    Returns:
        bool: True if 2FA is active (status = 2), False otherwise.
    """
    with DatabaseManagerUser() as db:
        db.execute("SELECT otp_active FROM users WHERE username = ?", (username,))
        result = db.fetchone()[0]
        # Status 2 means 2FA is fully activated and verified
        # Status 1 means 2FA setup is pending, Status 0 means disabled
        if result == 2:
            return True
        else:
            return False


def get_otp_secret(username: str) -> Optional[str]:
    """
    Retrieve the OTP secret for a user for 2FA verification.

    The secret is stored encrypted in the database and is decrypted before returning.

    Args:
        username (str): Username to retrieve OTP secret for.

    Returns:
        Optional[str]: Decrypted OTP secret, or None if not found.
    """
    with DatabaseManagerUser() as db:
        # Retrieve the encrypted OTP secret from database
        db.execute("SELECT otp_code FROM users WHERE username = ?", (username,))
        result = db.fetchone()
        if result:
            # Decrypt the secret using AES-GCM before returning
            key_manager = Key_manager_db()
            data = key_manager.decrypt(result[0])
            return data
        return None


def update_otp_status(username: str, active_code: int, secret: Optional[str] = None) -> bool:
    """
    Enable or disable 2FA for a user and update the secret if provided.

    Args:
        username (str): Username to update.
        active_code (int): Status code (0=disabled, 1=pending, 2=active).
        secret (Optional[str], optional): OTP secret to store (encrypted). Defaults to None.

    Returns:
        bool: True if update was successful.
    """
    with DatabaseManagerUser() as db:
        if secret:
            # Encrypt the OTP secret using AES-GCM before storing
            key_manager = Key_manager_db()
            cypher_secret = key_manager.encrypt(secret)

            # Update both status and encrypted secret
            db.execute("UPDATE users SET otp_active = ?, otp_code = ? WHERE username = ?",
                         (active_code, cypher_secret, username))
        else:
            # Only update status (e.g., when disabling 2FA)
            db.execute("UPDATE users SET otp_active = ? WHERE username = ?",
                         (active_code, username))
        return True