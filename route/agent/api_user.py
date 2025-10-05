from flask import Blueprint, jsonify
from module.database.agent import get_default_metric_data, get_agent_details, get_country_ranking

agent_user_api_bp = Blueprint('agent_user_api', __name__, url_prefix='/api/agent/user')


@agent_user_api_bp.route("/metric_dashboard", methods=['GET'])
def get_default_metric_data_agent():

    data = get_default_metric_data()

    return jsonify(data)


@agent_user_api_bp.route("/new_logs", methods=['GET'])
def get_new_logs_agent():

    data = get_agent_details()

    return jsonify(data)


@agent_user_api_bp.route("/country_ranking", methods=['GET'])
def get_country_ranking_data():

    data = get_country_ranking()

    return jsonify(data)