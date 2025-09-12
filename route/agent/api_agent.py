from flask import Blueprint, jsonify, request, current_app
import secrets
import hashlib
import time
import uuid
from module.database.agent import create_agent_token, add_malicious_ip_address, add_compromised_credential, add_attack_log, add_smtp_interaction

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
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['source_ip', 'service_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        source_ip = data.get('source_ip')
        agent_id = data.get('agent_id')
        service_type = data.get('service_type')
        country_name = data.get('country_name')

        # Prepare attack data structure
        attack_data = {
            'agent_id': data.get('agent_id'),  # Use agent_id instead of id
            'source_ip': data.get('source_ip'),
            'service_type': data.get('service_type'),
            'source_port': data.get('source_port'),
            'target_port': data.get('target_port'),
            'username_attempt': data.get('username_attempt'),
            'password_attempt': data.get('password_attempt'),
            'payload': data.get('payload'),
            'malware_hash': data.get('malware_hash'),
            'classification': data.get('classification'),
            'country_code': data.get('country_code'),
            'country_name': data.get('country_name')
        }

        # Add malicious IP to database
        if not add_malicious_ip_address(agent_id, source_ip, service_type, country_name, 
                                      data.get('country_code'), data.get('classification')):
            return jsonify({'success': False, 'error': 'Failed to add malicious IP'}), 500

        # Insert attack log for all
        if not add_attack_log(attack_data):
            return jsonify({'success': False, 'error': 'Failed to add attack log'}), 500

        # Service-specific processing
        if service_type == 'ssh':
            username_attempt = data.get('username_attempt')
            password_attempt = data.get('password_attempt')
            
            if username_attempt and password_attempt:
                if not add_compromised_credential(source_ip, username_attempt, password_attempt, service_type):
                    return jsonify({'success': False, 'error': 'Failed to add compromised credential'}), 500

        elif service_type == 'smtp':
            sender_email = data.get('sender_email')
            recipient_email = data.get('recipient_email')
            subject = data.get('subject')
            message_content = data.get('message_content')
            attachments = data.get('attachments')
            
            # Store SMTP-specific interaction data
            if not add_smtp_interaction(source_ip, sender_email, recipient_email, 
                                      subject, message_content, attachments):
                return jsonify({'success': False, 'error': 'Failed to add SMTP interaction'}), 500

        return jsonify({'success': True, 'message': f'{service_type.upper()} attack data processed successfully'})
    
    except Exception as e:
        print(f"Error in agent_report: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
