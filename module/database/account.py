import hashlib
from module.database.db_manager import DatabaseManagerUser

def change_password_account(username :str, old_password :str, new_password :str):
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