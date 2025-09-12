from flask import Blueprint, jsonify, request, current_app

agent_user_api_bp = Blueprint('agent_user_api', __name__, url_prefix='/api/agent/user')
