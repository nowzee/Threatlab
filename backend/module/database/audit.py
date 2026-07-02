"""
Audit log storage and helpers.

Records sensitive actions (user create/delete, agent create/delete, auth events,
...) into the ``audit_logs`` table that powers the admin "Journaux d'audit"
screen. The acting user's name is denormalised (``actor_username``) so entries
survive the deletion of the user that produced them.

The ``audit_logs`` table is defined in database/schemas.sql.
"""
from typing import Any, Dict, List, Optional
from module.database.db_manager import DatabaseManagerHoneypot


def log_audit(action: str,
              actor_id: Optional[int] = None,
              actor_username: Optional[str] = None,
              target_type: Optional[str] = None,
              target_id: Optional[Any] = None,
              detail: Optional[str] = None,
              ip_address: Optional[str] = None) -> None:
    """Best-effort insertion of an audit entry. Never raises to the caller so a
    logging failure can't break the action being audited."""
    try:
        with DatabaseManagerHoneypot() as db:
            db.execute("""
                INSERT INTO audit_logs
                    (actor_id, actor_username, action, target_type, target_id, detail, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (actor_id, actor_username, action, target_type,
                  str(target_id) if target_id is not None else None,
                  detail, ip_address))
    except Exception as e:
        print(f"Error writing audit log: {e}")


def list_audit(page: int = 1, limit: int = 25) -> Dict[str, Any]:
    """Paginated audit entries, newest first. Returns {items, total, page, limit}."""
    page = max(1, int(page))
    limit = max(1, min(100, int(limit)))
    try:
        with DatabaseManagerHoneypot() as db:
            db.execute("SELECT COUNT(*) AS c FROM audit_logs")
            total = db.fetchone()['c']
            db.execute("""
                SELECT id, created_at, actor_id, actor_username, action,
                       target_type, target_id, detail, ip_address
                FROM audit_logs
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """, (limit, (page - 1) * limit))
            rows: List[Dict[str, Any]] = db.fetchall()
            for r in rows:
                if r.get('created_at') is not None:
                    r['created_at'] = r['created_at'].isoformat()
            return {'items': rows, 'total': total, 'page': page, 'limit': limit}
    except Exception as e:
        print(f"Error listing audit logs: {e}")
        return {'items': [], 'total': 0, 'page': page, 'limit': limit}
