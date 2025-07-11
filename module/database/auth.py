import sqlite3
import hashlib


def auth_user(username, password):

    password = hashlib.sha512(password.encode()).hexdigest()

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
        if result == 1:
            return True
        else:
            return False