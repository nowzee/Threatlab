from flask import Blueprint, request, session, jsonify

config_api_key_bp = Blueprint('api_key', __name__, url_prefix='/api_key')

@config_api_key_bp.route("/add", methods=['POST'])
def add_api_key():
    return jsonify({'success': True}), 200

@config_api_key_bp.route("/delete", methods=['POST'])
def delete_api_key():
    return jsonify({'success': True}), 200

@config_api_key_bp.route("/list", methods=['GET'])
def list_api_key():
    return jsonify({'success': True}), 200