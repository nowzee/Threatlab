from flask import Blueprint, request, jsonify
from module.database.api import ManageApiKey

config_api_key_bp = Blueprint('api_key', __name__, url_prefix='/api_key')

@config_api_key_bp.route("/add", methods=['POST'])
def add_api_key():
    manager = ManageApiKey()
    data = request.json

    api_key = data.get('api_key')
    name = data.get('name')
    integration = data.get('integration')

    if not all([api_key, name, integration]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields: api_key, name, integration'
        }), 400

    success = manager.add(api_key, name, integration)

    if not success:
        return jsonify({'success': False, 'error': 'Invalid API key'}), 400

    return jsonify({'success': success}), 200

@config_api_key_bp.route("/delete", methods=['POST'])
def delete_api_key():
    manager = ManageApiKey()
    data = request.json


    api_key = data.get('api_key')

    if not api_key:
        return jsonify({'success': False, 'error': 'Missing required field: api_key'}), 400

    success = manager.delete(api_key)

    if not success:
        return jsonify({'success': False, 'error': 'Invalid API key'}), 400

    return jsonify({'success': True}), 200

@config_api_key_bp.route("/list", methods=['GET'])
def list_api_key():
    manager = ManageApiKey()
    api_keys = manager.list()
    return jsonify(api_keys), 200

@config_api_key_bp.route("/update", methods=['POST'])
def update_api_key():
    manager = ManageApiKey()
    data = request.json
    api_key = data.get('api_key')
    name = data.get('name')
    integration = data.get('integration')

    if not all([api_key, name, integration]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields: api_key, name, integration'
        }), 400

    manager.update(api_key, name, integration)

    return jsonify({'success': True}), 200