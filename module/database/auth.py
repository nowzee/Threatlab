import hashlib
from module.database.db_manager import DatabaseManagerUser
from module.crypto_utils.key_manager import *

def auth_user(username, password):
    password = hashlib.sha256(password.encode()).hexdigest()

    with DatabaseManagerUser() as db:
        db.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
        result = db.fetchone()
        if result:
            return True
        else:
            return False

def a2f_active(username):

    with DatabaseManagerUser() as db:
        db.execute("SELECT otp_active FROM users WHERE username = ?", (username,))
        result = db.fetchone()[0]
        if result == 2:
            return True
        else:
            return False

def get_otp_secret(username):
    """Récupère le secret OTP d'un utilisateur pour la vérification A2F"""

    with DatabaseManagerUser() as db:
        db.execute("SELECT otp_code FROM users WHERE username = ?", (username,))
        result = db.fetchone()
        if result:

            key_manager = Key_manager_db()
            data = key_manager.decrypt(result[0])

            return data
        return None

def update_otp_status(username, active_code, secret=None):
    """Active ou désactive l'A2F pour un utilisateur et met à jour le secret si fourni"""

    with DatabaseManagerUser() as db:
        if secret:

            key_manager = Key_manager_db()
            cypher_secret = key_manager.encrypt(secret)

            db.execute("UPDATE users SET otp_active = ?, otp_code = ? WHERE username = ?",
                         (active_code, cypher_secret, username))
        else:
            db.execute("UPDATE users SET otp_active = ? WHERE username = ?",
                         (active_code, username))
        return True