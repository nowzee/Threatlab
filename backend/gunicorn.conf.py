"""
Configuration gunicorn pour le backend Threatlab.

Remplace le serveur de développement Flask (`app.run`). Points clés :
- workers gthread (concurrence I/O sans réécriture async) ;
- recyclage automatique des workers (anti fuite mémoire / blocage) ;
- TLS auto-signé persistant (équivalent de l'ancien ssl_context='adhoc') ;
- initialisation des bases + flush de l'ingestion aux bons moments.
"""
import os

# --- Réseau ---
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")

# --- Workers ---
# Par défaut volontairement modeste : workers * DB_POOL_SIZE doit rester sous le
# max_connections de MySQL (~151). Ajustable via l'env si la machine est grosse.
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.getenv("GUNICORN_THREADS", "8"))

# --- Recyclage des workers (le « des fois ça down ») ---
# Chaque worker est redémarré automatiquement après ~max_requests requêtes
# (le jitter évite que tous les workers se recyclent en même temps). Cela purge
# d'éventuelles fuites mémoire ou états dégradés sans interrompre le service.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "200"))

# Un worker bloqué plus de `timeout` secondes est tué puis respawné par le
# maître. `graceful_timeout` laisse aux requêtes en cours le temps de finir.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# --- TLS (auto-signé, servi directement par gunicorn) ---
certfile = os.getenv("TLS_CERT", "/app/secrets/server.crt")
keyfile = os.getenv("TLS_KEY", "/app/secrets/server.key")

# --- Logs ---
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
accesslog = "-"
errorlog = "-"


def on_starting(server):
    """Exécuté une fois dans le maître, avant le fork des workers."""
    # 1) Certificat TLS auto-signé si absent (avant la création des sockets SSL).
    from module.tls import ensure_self_signed_cert
    ensure_self_signed_cert(certfile, keyfile)

    # 2) Initialisation des bases (équivalent de l'ancien bloc __main__ d'app.py).
    from module.database.db_manager import DatabaseManagerUser, DatabaseManagerHoneypot
    with DatabaseManagerUser() as db:
        db.create_db()
    with DatabaseManagerHoneypot() as db:
        db.create_db()


def worker_exit(server, worker):
    """
    Appelé quand un worker s'arrête (y compris lors du recyclage max_requests).

    On vide la file d'ingestion en mémoire pour ne pas perdre les rapports déjà
    acceptés (200) mais pas encore écrits en base.
    """
    try:
        from module.ingestion.ingest import flush_on_exit
        flush_on_exit()
    except Exception as e:
        print(f"[gunicorn] worker_exit flush error: {e}")
