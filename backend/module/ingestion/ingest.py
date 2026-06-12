"""
Asynchronous ingestion of attack reports.

Agents POST to /api/agent/report. Instead of running ~10 synchronous SQL
queries per HTTP request (which caused 500s and collapsed under load), the
report is placed in an in-memory queue and we return 200 immediately. A
background thread drains the queue and writes to the database, batching inserts
into `attack_logs` (the highest-volume, append-only table).

Accepted trade-off: a report still in the queue (not yet flushed) can be lost if
the worker is killed abruptly (SIGKILL after a gunicorn timeout). We therefore
keep batches small and the flush frequent, plus a flush on graceful shutdown
(worker recycling via max_requests / SIGTERM). When the queue is full the caller
gets a 503 and the agent re-queues the attack to resend it later.
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

# --- Settings (overridable via environment variables) ---
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
    Queue a report without blocking the HTTP request.

    Returns:
        True if the report was queued, False if the queue is full (overload) —
        the caller then returns 503 and the agent retries.
    """
    global _dropped
    try:
        _q.put_nowait(report)
        return True
    except queue.Full:
        _dropped += 1
        if _dropped % 100 == 1:
            print(f"[ingest] queue full, reports refused (total): {_dropped}")
        return False


def _process_one(report: Dict[str, Any], attack_batch: List[Dict[str, Any]]) -> None:
    """Process one report: state upserts synchronously, attack_log deferred to a batch."""
    service_type = report.get("service_type")
    source_ip = report.get("source_ip")
    agent_id = report.get("agent_id")

    # Aggregated state (malicious IP + relations + counters): must precede the
    # credentials (foreign key constraint on malicious_ip_id).
    add_malicious_ip_address(
        agent_id, source_ip, service_type,
        report.get("country_name"), report.get("country_code"),
        report.get("classification"),
    )

    # attack_logs: append-only -> accumulated for a batch insert.
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
    """Insert the accumulated attack_logs batch then clear it."""
    if not attack_batch:
        return
    try:
        add_attack_logs_batch(attack_batch)
    except Exception as e:
        print(f"[ingest] attack_logs flush error ({len(attack_batch)} rows): {e}")
    finally:
        attack_batch.clear()


def _run() -> None:
    """Worker loop: drain the queue and write to the database in batches."""
    attack_batch: List[Dict[str, Any]] = []
    while True:
        try:
            report = _q.get(timeout=FLUSH_INTERVAL)
        except queue.Empty:
            # Quiet queue -> flush whatever is pending.
            _flush(attack_batch)
            continue

        if report is None:
            # Stop sentinel (shutdown / recycling).
            _q.task_done()
            _flush(attack_batch)
            return

        try:
            _process_one(report, attack_batch)
        except Exception as e:
            print(f"[ingest] report processing error: {e}")
        finally:
            _q.task_done()

        if len(attack_batch) >= BATCH_SIZE:
            _flush(attack_batch)


def start_worker() -> None:
    """Start the ingestion thread (once per process)."""
    global _worker_started, _worker_thread
    with _start_lock:
        if _worker_started:
            return
        _worker_thread = threading.Thread(target=_run, name="ingest-worker", daemon=True)
        _worker_thread.start()
        _worker_started = True
        atexit.register(flush_on_exit)
        print(f"[ingest] worker started (batch={BATCH_SIZE}, flush={FLUSH_INTERVAL}s, "
              f"queue_max={QUEUE_MAXSIZE})")


def flush_on_exit() -> None:
    """
    Synchronously drain the remaining queue before the process exits.

    Called on graceful shutdown (atexit) and by the gunicorn worker_exit hook
    on worker recycling, so reports still in memory are not lost.
    """
    # Ask the worker to stop and let it flush its current batch.
    try:
        _q.put_nowait(None)
    except queue.Full:
        pass
    if _worker_thread is not None:
        _worker_thread.join(timeout=5)

    # Safety net: drain anything left in the queue.
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
                print(f"[ingest] flush_on_exit error (processing): {e}")
        _flush(batch)
        print(f"[ingest] final flush: {len(leftover)} reports drained")
