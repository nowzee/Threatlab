import sqlite3
import hashlib

def change_password_account(username :str, old_password :str, new_password :str):
    old_password = hashlib.sha512(old_password.encode()).hexdigest()

    with sqlite3.connect('honeypot.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, old_password))
        result = cursor.fetchone()

        if result:
            new_password = hashlib.sha512(new_password.encode()).hexdigest()

            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, result[0]))
            conn.commit()
            return True
        else:
            return False