from flask import Blueprint, jsonify, request
from module.database.agent import ManagerAgent

agent_manage_bp = Blueprint('agent_manage', __name__, url_prefix='/api/agent/manage')

@agent_manage_bp.route("/delete", methods=['POST'])
def delete_agent():
    data = request.json
    agent_id: int = data.get('agent_id')

    manager = ManagerAgent()
    if manager.remove(agent_id):
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 400

@agent_manage_bp.route("/update", methods=['POST'])
def update_agent():
    data = request.json

    return jsonify({'success': True}), 200

@agent_manage_bp.route("/list", methods=['GET'])
def list_agent():
    manager = ManagerAgent()
    agents = manager.list()

    return jsonify(agents), 200