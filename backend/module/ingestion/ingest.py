"""
Ingestion asynchrone des rapports d'attaque.

Les agents postent sur /api/agent/report. Plutôt que d'exécuter ~10 requêtes
SQL synchrones par requête HTTP (ce qui provoquait des 500 et s'effondrait sous
charge), on place le rapport dans une file en mémoire et on répond 200 tout de
suite. Un thread de fond consomme la file et écrit en base, en groupant les
insertions dans `attack_logs` (table append-only, la plus volumineuse) par lots.

Compromis assumé : un rapport encore en file (non flushé) peut être perdu si le
worker est tué brutalement (SIGKILL après timeout gunicorn). On garde donc des
lots petits et un flush fréquent, plus un flush au shutdown gracieux (recyclage
de worker via max_requests / SIGTERM). En cas de file pleine, l'appelant reçoit
un 503 et l'agent ré-enfile l'attaque pour la renvoyer plus tard.
"""
import os
import queue
import threading
import atexit
from typing import Any, Dict, List

from module.database.agent import (
    add_malicious_ip_address,
    add_compromised_credential,
    add_smtp_interaction,
    add_attack_logs_batch,
)

# --- Réglages (surchargeables par variables d'environnement) ---
QUEUE_MAXSIZE = int(os.getenv("INGEST_QUEUE_MAXSIZE", "10000"))
BATCH_SIZE = int(os.getenv("INGEST_BATCH_SIZE", "200"))
FLUSH_INTERVAL = float(os.getenv("INGEST_FLUSH_INTERVAL", "0.5"))

_q: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=QUEUE_MAXSIZE)
_worker_started = False
_worker_thread: "threading.Thread | None" = None
_start_lock = threading.Lock()
_dropped = 0


def enqueue_report(report: Dict[str, Any]) -> bool:
    """
    Met un rapport en file sans bloquer la requête HTTP.

    Returns:
        True si le rapport a été mis en file, False si la file est pleine
        (surcharge) — l'appelant renvoie alors 503 et l'agent réessaiera.
    """
    global _dropped
    try:
        _q.put_nowait(report)
        return True
    except queue.Full:
        _dropped += 1
        if _dropped % 100 == 1:
            print(f"[ingest] file pleine, rapports refusés (cumul): {_dropped}")
        return False


def _process_one(report: Dict[str, Any], attack_batch: List[Dict[str, Any]]) -> None:
    """Traite un rapport : upserts d'état en synchrone, attack_log différé en lot."""
    service_type = report.get("service_type")
    source_ip = report.get("source_ip")
    agent_id = report.get("agent_id")

    # État agrégé (IP malveillante + relations + compteurs) : doit précéder les
    # credentials (contrainte de clé étrangère sur malicious_ip_id).
    add_malicious_ip_address(
        agent_id, source_ip, service_type,
        report.get("country_name"), report.get("country_code"),
        report.get("classification"),
    )

    # attack_logs : append-only -> accumulé pour insertion par lot.
    attack_batch.append(report)

    if service_type in ("ssh", "ftp"):
        username = report.get("username_attempt")
        password = report.get("password_attempt")
        if username and password:
            add_compromised_credential(source_ip, username, password, service_type)
    elif service_type == "smtp":
        add_smtp_interaction(
            source_ip,
            report.get("sender_email"), report.get("recipient_email"),
            report.get("subject"), report.get("message_content"),
            report.get("attachments"),
        )


def _flush(attack_batch: List[Dict[str, Any]]) -> None:
    """Insère le lot d'attack_logs accumulé puis le vide."""
    if not attack_batch:
        return
    try:
        add_attack_logs_batch(attack_batch)
    except Exception as e:
        print(f"[ingest] erreur flush attack_logs ({len(attack_batch)} lignes): {e}")
    finally:
        attack_batch.clear()


def _run() -> None:
    """Boucle du worker : draine la file et écrit en base par lots."""
    attack_batch: List[Dict[str, Any]] = []
    while True:
        try:
            report = _q.get(timeout=FLUSH_INTERVAL)
        except queue.Empty:
            # Silence sur la file -> on flushe ce qui est en attente.
            _flush(attack_batch)
            continue

        if report is None:
            # Sentinelle d'arrêt (shutdown / recyclage).
            _q.task_done()
            _flush(attack_batch)
            return

        try:
            _process_one(report, attack_batch)
        except Exception as e:
            print(f"[ingest] erreur traitement rapport: {e}")
        finally:
            _q.task_done()

        if len(attack_batch) >= BATCH_SIZE:
            _flush(attack_batch)


def start_worker() -> None:
    """Démarre le thread d'ingestion (une fois par processus)."""
    global _worker_started, _worker_thread
    with _start_lock:
        if _worker_started:
            return
        _worker_thread = threading.Thread(target=_run, name="ingest-worker", daemon=True)
        _worker_thread.start()
        _worker_started = True
        atexit.register(flush_on_exit)
        print(f"[ingest] worker démarré (batch={BATCH_SIZE}, flush={FLUSH_INTERVAL}s, "
              f"queue_max={QUEUE_MAXSIZE})")


def flush_on_exit() -> None:
    """
    Vide la file restante de façon synchrone avant l'arrêt du processus.

    Appelé au shutdown gracieux (atexit) et par le hook gunicorn worker_exit
    lors du recyclage des workers, pour ne pas perdre les rapports en mémoire.
    """
    # Demander au worker de s'arrêter et lui laisser flusher son lot courant.
    try:
        _q.put_nowait(None)
    except queue.Full:
        pass
    if _worker_thread is not None:
        _worker_thread.join(timeout=5)

    # Filet de sécurité : drainer ce qui resterait dans la file.
    leftover: List[Dict[str, Any]] = []
    while True:
        try:
            item = _q.get_nowait()
        except queue.Empty:
            break
        if item is not None:
            leftover.append(item)

    if leftover:
        batch: List[Dict[str, Any]] = []
        for r in leftover:
            try:
                _process_one(r, batch)
            except Exception as e:
                print(f"[ingest] erreur flush_on_exit (traitement): {e}")
        _flush(batch)
        print(f"[ingest] flush final: {len(leftover)} rapports écoulés")
