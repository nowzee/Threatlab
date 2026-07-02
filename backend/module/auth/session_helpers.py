"""
Session-based user role helpers.

Complements ``decorator.agent_jwt_required`` (which authenticates *agents*).
These helpers work on the Flask *user* session established at login and provide
the numeric user id, the role, and a ``@require_admin`` guard for admin routes.

All non-public endpoints are already login-gated by ``app.before_request``; the
guard here adds the role check on top of that.
"""
from functools import wraps
from typing import Any, Callable, Optional, Tuple

from flask import session, jsonify, Response

from module.database.auth import get_user_auth


def _ensure_role_in_session() -> None:
    """Backfill user_id/role for sessions created before roles existed."""
    if session.get('logged_in') and session.get('role') is None:
        username = session.get('username')
        if username:
            info = get_user_auth(username)
            if info:
                session['user_id'] = info['id']
                session['role'] = info['role']


def current_user_id() -> Optional[int]:
    """Numeric id of the logged-in user (or None)."""
    _ensure_role_in_session()
    return session.get('user_id')


def current_username() -> Optional[str]:
    """Username of the logged-in user (or None)."""
    return session.get('username')


def current_role() -> Optional[str]:
    """Role of the logged-in user ('admin' | 'member' | None)."""
    _ensure_role_in_session()
    return session.get('role')


def is_admin() -> bool:
    """True if the logged-in user is an administrator."""
    return current_role() == 'admin'


def require_admin(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator restricting a route to administrators (401 if anonymous, 403 if not admin)."""
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Tuple[Response, int] | Any:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Non authentifié'}), 401
        if current_role() != 'admin':
            return jsonify({'success': False, 'error': 'Accès réservé aux administrateurs'}), 403
        return fn(*args, **kwargs)

    return wrapper
