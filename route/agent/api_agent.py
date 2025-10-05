from flask import Blueprint, jsonify, request, current_app, send_file
import jwt
import os
from module.database.agent import create_agent_token, add_malicious_ip_address, add_compromised_credential, add_attack_log, add_smtp_interaction
from module.database.db_manager import DatabaseManagerHoneypot
from string import Template
from module.auth.decorator import agent_jwt_required

agent_create_bp = Blueprint('agent_create', __name__, url_prefix='/api/agent')

def generate_jwt(agent_id: int) -> str:
    """
    Génère un JWT unique pour un agent spécifique.
    """
    secret_key = current_app.config['SECRET_KEY']
    payload_to_encode = {
        'agent_id': agent_id,
        'nonce': os.urandom(16).hex()
    }
    token = jwt.encode(payload_to_encode, secret_key, algorithm='HS256')
    return token

@agent_create_bp.route("/create", methods=['POST'])
def agent_create():
    agent_name = request.json.get('agent_name')
    agent_type = request.json.get('agent_type', 'ssh')
    ip_address = request.json.get('ip_address', '0.0.0.0')
    country_name = request.json.get('country_name')
    groupe = request.json.get('groupe')
    banner = request.json.get('banner', 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5')

    agent_id, secret_token = create_agent_token(
        agent_name,
        ip_address=ip_address,
        country_name=country_name,
        service_type=agent_type,
        groupe=groupe,
        banner=banner
    )

    if agent_id:
        return jsonify({
            'success': True,
            'secret_token': secret_token,
            'agent_id': agent_id
        }), 200
    else:
        return jsonify({'success': False, 'error': 'Failed to create agent'}), 500


@agent_create_bp.route("/report", methods=['POST'])
@agent_jwt_required
def agent_report():
    try:
        data = request.json
        agent_id = data.get('agent_id')

        # Validate required fields
        required_fields = ['source_ip', 'service_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        source_ip = data.get('source_ip')
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
        return jsonify({'success': False, 'error': 'Internal server error'}), 200


@agent_create_bp.route("/download/<int:agent_id>", methods=['GET'])
def download_agent(agent_id):
    """Generate and download the Python honeypot agent for the specified agent_id"""
    try:
        # Get agent details from database
        with DatabaseManagerHoneypot() as db:
            db.execute("""SELECT agent_name, ip_address, secret_token_sha256, banner, service_type
                         FROM honey_agents
                         WHERE id = ?""", (agent_id,))
            result = db.fetchone()

            if not result:
                return jsonify({'error': 'Agent not found'}), 404

            agent_name, ip_address, secret_token_sha256, banner, service_type = result

        # Read the template file
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'module', 'templates', 'ssh_honeypot_agent.py'
        )

        with open(template_path, 'r') as f:
            template_content = f.read()

        # Retrieve the actual JWT token for this agent
        # Since we can't reverse the SHA256, we'll generate a new JWT token
        secret_token = generate_jwt(agent_id)

        # Get server URL from request
        server_url = request.host_url.rstrip('/')

        # Default values
        ssh_port = 22
        if not banner:
            banner = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"

        # Replace placeholders in template
        with open(template_path, 'r') as f:
            template_content = f.read()

        t = Template(template_content)
        agent_content = t.substitute(
            agent_id=agent_id,
            agent_token=secret_token,
            server_url=server_url,
            ssh_port=ssh_port,
            ssh_banner=banner
        )

        # Write to temporary file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(agent_content)
        temp_file.close()

        # Send file as download
        filename = f"agent_{agent_name.replace(' ', '_')}.py"

        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='text/x-python'
        )

    except Exception as e:
        print(f"Error generating agent download: {e}")
        return jsonify({'error': 'Failed to generate agent file'}), 500