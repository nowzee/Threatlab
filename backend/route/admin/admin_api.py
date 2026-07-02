"""
Admin API Route Module.

Admin-only endpoints (role == 'admin') for managing user accounts and reading
the audit log. Login-gating is provided globally by ``app.before_request``; the
``@require_admin`` decorator adds the role check.
"""
from typing import Tuple

from flask import Blueprint, jsonify, request, Response

from module.auth.session_helpers import require_admin, current_user_id, current_username
from module.auth.password_policy import validate_password
from module.database.users_admin import list_users, create_member, delete_user
from module.database.audit import list_audit, log_audit

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@require_admin
def admin_list_users() -> Tuple[Response, int]:
    """List all accounts with their owned-honeypot counts."""
    return jsonify({'success': True, 'users': list_users()}), 200


@admin_bp.route('/users', methods=['POST'])
@require_admin
def admin_create_user() -> Tuple[Response, int]:
    """Create a new member account. Role is forced to 'member' server-side."""
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username:
        return jsonify({'success': False, 'error': "Nom d'utilisateur requis"}), 400

    ok, msg = validate_password(password)
    if not ok:
        return jsonify({'success': False, 'error': msg}), 400

    created, code, user_id = create_member(username, password)
    if not created:
        errors = {
            'username_taken': "Ce nom d'utilisateur existe déjà",
            'invalid_username': "Nom d'utilisateur invalide",
        }
        return jsonify({'success': False, 'error': errors.get(code, 'Erreur lors de la création')}), 400

    log_audit('user.create', actor_id=current_user_id(), actor_username=current_username(),
              target_type='user', target_id=user_id,
              detail=f"username={username}, role=member", ip_address=request.remote_addr)
    return jsonify({'success': True, 'id': user_id}), 201


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def admin_delete_user(user_id: int) -> Tuple[Response, int]:
    """Delete a member account (never self, never an admin)."""
    if current_user_id() == user_id:
        return jsonify({'success': False,
                        'error': 'Vous ne pouvez pas supprimer votre propre compte'}), 400

    ok, code, uname = delete_user(user_id)
    if not ok:
        errors = {
            'not_found': 'Utilisateur introuvable',
            'cannot_delete_admin': "Impossible de supprimer un compte administrateur",
        }
        status = 404 if code == 'not_found' else 403
        return jsonify({'success': False, 'error': errors.get(code, 'Erreur')}), status

    log_audit('user.delete', actor_id=current_user_id(), actor_username=current_username(),
              target_type='user', target_id=user_id, detail=f"username={uname}",
              ip_address=request.remote_addr)
    return jsonify({'success': True}), 200


@admin_bp.route('/audit', methods=['GET'])
@require_admin
def admin_audit() -> Tuple[Response, int]:
    """Paginated audit log. Query: ?page=&limit=."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 25))
    except (TypeError, ValueError):
        page, limit = 1, 25
    return jsonify(list_audit(page, limit)), 200
