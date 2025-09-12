from flask import Blueprint, jsonify
from module.database.agent import get_default_metric_data

agent_user_api_bp = Blueprint('agent_user_api', __name__, url_prefix='/api/agent/user')


@agent_user_api_bp.route("/metric_dashboard", methods=['GET'])
def get_default_metric_data_agent():

    data = get_default_metric_data()

    return jsonify(data)