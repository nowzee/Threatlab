from flask import Blueprint, jsonify, request, current_app
import secrets
import hashlib
import time
import uuid
from module.database.agent import create_agent_token

agent_create_bp = Blueprint('agent_create', __name__, url_prefix='/api')

def generer_apikey_agent(agent_name=""):
    prefixe = "agent"
    secret_key = current_app.config.get('SECRET_KEY', '')

    uuid_partie = str(uuid.uuid4())
    partie_aleatoire = secrets.token_hex(19)
    timestamp = str(int(time.time()))

    donnees_combinees = f"{agent_name}{uuid_partie}{secret_key}{partie_aleatoire}{timestamp}".encode()
    hash_final = hashlib.sha256(donnees_combinees).hexdigest()
    return f"{prefixe}-{hash_final}"

@agent_create_bp.route("/agent/create", methods=['POST'])
def agent_create():
    agent_name = request.json.get('agent_name')

    secret_token = generer_apikey_agent(agent_name)

    if create_agent_token(agent_name, secret_token):
        return jsonify({'success': True, 'secret_token': secret_token}), 200
    else:
        return jsonify({'success': False}), 500

@agent_create_bp.route("/agent/report", methods=['POST'])
def agent_report():
    data = request.json

    attack_data = {
        'agent_id': data.get('id'), # Obligatoire
        'source_ip': data.get('source_ip'), # Obligatoire
        'service_type': data.get('service_type'),  # Obligatoire
        'source_port': data.get('source_port'),  # Peut être None
        'target_port': data.get('target_port'),  # Peut être None
        'username_attempt': data.get('username_attempt'),  # Peut être None
        'password_attempt': data.get('password_attempt'),  # Peut être None
        'payload': data.get('payload'),  # Peut être None
        'malware_hash': data.get('malware_hash'),  # Peut être None
        'attack_type': data.get('attack_type'),  # Peut être None
        'country_code': data.get('country_code'),  # Peut être None
        'country_name': data.get('country_name')  # Peut être None
    }
