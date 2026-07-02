"""
Gunicorn configuration for the Threatlab backend.

Replaces the Flask development server (`app.run`). Key points:
- gthread workers (I/O concurrency without an async rewrite);
- automatic worker recycling (guards against memory leaks / hangs);
- persistent self-signed TLS (equivalent to the old ssl_context='adhoc');
- database initialization + ingestion flush at the right moments.
"""
import os

# --- Network ---
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")

# --- Workers ---
# Intentionally modest default: workers * DB_POOL_SIZE must stay under MySQL's
# max_connections (~151). Tune via env if the machine is large.
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.getenv("GUNICORN_THREADS", "8"))

# --- Worker recycling (the "sometimes it goes down") ---
# Each worker is restarted automatically after ~max_requests requests (the
# jitter prevents all workers from recycling at the same time). This purges
# possible memory leaks or degraded states without interrupting the service.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "200"))

# A worker blocked for more than `timeout` seconds is killed and respawned by
# the master. `graceful_timeout` gives in-flight requests time to finish.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# --- TLS (self-signed, served directly by gunicorn) ---
certfile = os.getenv("TLS_CERT", "/app/secrets/server.crt")
keyfile = os.getenv("TLS_KEY", "/app/secrets/server.key")

# --- Logs ---
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
accesslog = "-"
errorlog = "-"


def on_starting(server):
    """Runs once in the master, before workers are forked."""
    import os
    import secrets

    # 1) Pre-create the secret keys ONCE, before workers fork, so every worker
    # reads the same Flask SECRET_KEY. Otherwise concurrent workers each generate
    # their own key on first run and session cookies fail across workers
    # (constant re-authentication on every reload).
    secret_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets')
    os.makedirs(secret_dir, exist_ok=True)
    for fname in ('.app_secret_key', '.agent_secret_key'):
        path = os.path.join(secret_dir, fname)
        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write(secrets.token_hex(4096))

    # 2) Self-signed TLS certificate if missing (before SSL sockets are created).
    from module.tls import ensure_self_signed_cert
    ensure_self_signed_cert(certfile, keyfile)

    # 3) Database initialization: create the bootstrap admin if needed. The
    #    honeypot schema is provided by database/schemas.sql (no runtime init).
    from module.database.db_manager import DatabaseManagerUser
    with DatabaseManagerUser() as db:
        db.create_db()


def worker_exit(server, worker):
    """
    Called when a worker stops (including max_requests recycling).

    Flush the in-memory ingestion queue so reports already accepted (200) but
    not yet written to the database are not lost.
    """
    try:
        from module.ingestion.ingest import flush_on_exit
        flush_on_exit()
    except Exception as e:
        print(f"[gunicorn] worker_exit flush error: {e}")
