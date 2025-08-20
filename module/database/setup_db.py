import os
from module.database.db_manager import DatabaseManagerHoneypot, DatabaseManagerUser



def setup_dbs():

    if not os.path.exists('db'):
        os.makedirs('db')

    with DatabaseManagerUser() as db:
        db.create_db()

    with DatabaseManagerHoneypot() as db:
        db.create_db()
