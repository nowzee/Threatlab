import sqlite3
import hashlib


def auth_user(username, password):

    password = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect('honeypot.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        if result:
            return True
        else:
            return False

def a2f_active(username):
    with sqlite3.connect('honeypot.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT otp_active FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()[0]
        if result == 2:
            return True
        else:
            return False

def get_otp_secret(username):
    """Récupère le secret OTP d'un utilisateur pour la vérification A2F"""
    with sqlite3.connect('honeypot.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT otp_code FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

def update_otp_status(username, active_code, secret=None):
    """Active ou désactive l'A2F pour un utilisateur et met à jour le secret si fourni"""
    with sqlite3.connect('honeypot.db') as conn:
        cursor = conn.cursor()
        if secret:
            cursor.execute("UPDATE users SET otp_active = ?, otp_code = ? WHERE username = ?", 
                         (active_code, secret, username))
        else:
            cursor.execute("UPDATE users SET otp_active = ? WHERE username = ?", 
                         (active_code, username))
        conn.commit()
        return True