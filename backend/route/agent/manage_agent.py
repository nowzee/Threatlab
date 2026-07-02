"""
Agent Management Route Module.

This module provides Flask routes for managing honeypot agents,
including delete, update, and list operations.
"""

from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from module.database.agent import ManagerAgent
from module.auth.session_helpers import current_user_id, current_username, is_admin
from module.database.audit import log_audit

agent_manage_bp = Blueprint('agent_manage', __name__, url_prefix='/api/agent/manage')


@agent_manage_bp.route("/delete", methods=['POST'])
def delete_agent() -> Tuple[Response, int]:
    """
    Delete a honeypot agent.

    Expects JSON body with:
    - agent_id: The ID of the agent to delete

    Members can only delete their own honeypots; admins can delete any.

    Returns:
        JSON response with success status.
        HTTP status codes: 200 (success), 400 (failure / not owned).
    """
    data = request.json
    agent_id: int = data.get('agent_id')

    manager = ManagerAgent()
    if manager.remove(agent_id, viewer_id=current_user_id(), is_admin=is_admin()):
        log_audit('agent.delete', actor_id=current_user_id(), actor_username=current_username(),
                  target_type='agent', target_id=agent_id, ip_address=request.remote_addr)
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400


@agent_manage_bp.route("/list", methods=['GET'])
def list_agent() -> Tuple[Response, int]:
    """
    List honeypot agents.

    Admins see every agent (with owner name); members see only their own.

    Returns:
        JSON array of agent objects.
        HTTP status code 200.
    """
    manager = ManagerAgent()
    agents = manager.list(viewer_id=current_user_id(), is_admin=is_admin())

    return jsonify(agents), 200
