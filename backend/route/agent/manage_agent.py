"""
Agent Management Route Module.

This module provides Flask routes for managing honeypot agents,
including delete, update, list, and group creation operations.
"""

from typing import Tuple
from flask import Blueprint, jsonify, request, Response
from module.database.agent import ManagerAgent

agent_manage_bp = Blueprint('agent_manage', __name__, url_prefix='/api/agent/manage')


@agent_manage_bp.route("/delete", methods=['POST'])
def delete_agent() -> Tuple[Response, int]:
    """
    Delete a honeypot agent.

    Expects JSON body with:
    - agent_id: The ID of the agent to delete

    Returns:
        JSON response with success status.
        HTTP status codes: 200 (success), 400 (failure).
    """
    data = request.json
    agent_id: int = data.get('agent_id')

    manager = ManagerAgent()
    if manager.remove(agent_id):
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400


@agent_manage_bp.route("/list", methods=['GET'])
def list_agent() -> Tuple[Response, int]:
    """
    List all registered honeypot agents.

    Returns:
        JSON array of agent objects.
        HTTP status code 200.
    """
    manager = ManagerAgent()
    agents = manager.list()

    return jsonify(agents), 200


@agent_manage_bp.route("/create_group", methods=['POST'])
def create_group() -> Tuple[Response, int]:
    """
    Create a new agent group.

    Expects JSON body with:
    - group_name: The name of the group to create

    Returns:
        JSON response with success status.
        HTTP status codes: 200 (success), 400 (failure).
    """
    data = request.json
    group_name = data.get('group_name')

    manager = ManagerAgent()
    if manager.create_group(group_name):
        return jsonify({'success': True}), 200

    return jsonify({'success': False}), 400