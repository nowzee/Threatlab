from module.database.db_manager import DatabaseManagerUser
from module.crypto_utils.key_manager import *
from datetime import datetime


def verify_api_key(api_key):
    with DatabaseManagerUser() as db:
        db.execute("SELECT id FROM api_keys WHERE key = ?", (api_key,))
        result = db.fetchone()
        return result is not None


class ManageApiKey:

    def add(self, api_key, name, integration):

        key_manager = Key_manager_db()
        cypher_api_key = key_manager.encrypt(api_key)

        if verify_api_key(cypher_api_key):
            return False

        now = datetime.now()

        with DatabaseManagerUser() as db:
            db.execute(
                "INSERT INTO api_keys (key, name, integration, created_at) VALUES (?, ?, ?, ?)",
                (cypher_api_key, name, integration, now)
            )
        return True

    def list(self):
        key_manager = Key_manager_db()
        with DatabaseManagerUser() as db:
            db.execute("SELECT id, key, name, integration FROM api_keys")
            result = db.fetchall()

        # 🔓 Déchiffre les clés avant de les retourner
        decrypted_results = []
        for row in result:

            decrypted_results.append({
                "id": row[0],
                "key": key_manager.decrypt(row[1]),
                "name": row[2],
                "integration": row[3]
            })

        return decrypted_results

    def update(self, api_key, name, integration):

        key_manager = Key_manager_db()
        cypher_api_key = key_manager.encrypt(api_key)

        if not verify_api_key(cypher_api_key):
            return False

        with DatabaseManagerUser() as db:
            db.execute(
                "UPDATE api_keys SET name = ?, integration = ? WHERE key = ?",
                (name, integration, cypher_api_key)
            )
        return True
