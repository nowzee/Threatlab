from module.database.db_manager import DatabaseManagerUser
from datetime import datetime


def verify_api_key(api_key):
    with DatabaseManagerUser() as db:
        db.execute("SELECT id FROM api_keys WHERE key = ?", (api_key,))
        result = db.fetchone()
        return result is not None


class ManageApiKey:

    def add(self, api_key, name, integration):
        if verify_api_key(api_key):
            return False

        now = datetime.now()

        with DatabaseManagerUser() as db:
            db.execute(
                "INSERT INTO api_keys (key, name, integration, created_at) VALUES (?, ?, ?, ?)",
                (api_key, name, integration, now)
            )
        return True

    def delete(self, api_key):
        if not verify_api_key(api_key):
            return False

        with DatabaseManagerUser() as db:
            db.execute("DELETE FROM api_keys WHERE key = ?", (api_key,))
        return True

    def list(self):
        with DatabaseManagerUser() as db:

            db.execute("SELECT id, key, name, integration FROM api_keys")
            result = db.fetchall()
            print(result)
            return result

    def update(self, api_key, name, integration):
        if not verify_api_key(api_key):
            return False

        with DatabaseManagerUser() as db:
            db.execute(
                "UPDATE api_keys SET name = ?, integration = ? WHERE key = ?",
                (name, integration, api_key)
            )
        return True
