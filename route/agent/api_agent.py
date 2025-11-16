"""
Agent API Route Module.

This module provides Flask routes for honeypot agent operations,
including agent creation, attack reporting, and agent file downloads.
"""

from typing import Tuple
from flask import Blueprint, jsonify, request, current_app, send_file, Response
import jwt
import os
from module.database.agent import create_agent_token, add_malicious_ip_address, add_compromised_credential, add_attack_log, add_smtp_interaction
from module.database.db_manager import DatabaseManagerHoneypot
from string import Template
from module.auth.decorator import agent_jwt_required

agent_create_bp = Blueprint('agent_create', __name__, url_prefix='/api/agent')


def generate_jwt(agent_id: int) -> str:
    """
    Generate a unique JWT token for a specific agent.

    Args:
        agent_id: The ID of the agent to generate a token for.

    Returns:
        A JWT token string containing the agent_id and a random nonce.
    """
    secret_key = current_app.config['AGENT_SECRET_KEY']
    payload_to_encode = {
        'agent_id': agent_id,
        'nonce': os.urandom(16).hex()  # Random nonce prevents token reuse
    }
    # Sign with HS256 for agent authentication
    token = jwt.encode(payload_to_encode, secret_key, algorithm='HS256')
    return token


@agent_create_bp.route("/create", methods=['POST'])
def agent_create() -> Tuple[Response, int]:
    """
    Create a new honeypot agent and generate its authentication token.

    Expects JSON body with:
    - agent_name: Name of the agent
    - agent_type: Service type (default: 'ssh')
    - ip_address: Agent's IP address (default: '0.0.0.0')
    - country_name: Country where the agent is deployed
    - groupe: Group name for organizing agents
    - banner: Service banner to display (default: SSH banner)

    Returns:
        JSON response with agent_id and secret_token on success.
        HTTP status codes: 200 (success), 500 (creation failed).
    """
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
def agent_report() -> Tuple[Response, int]:
    """
    Receive and process attack reports from honeypot agents.

    This endpoint is protected by JWT authentication and processes attack data
    based on the service type (SSH, SMTP, etc.).

    Required fields in JSON body:
    - source_ip: The attacker's IP address
    - service_type: The service being attacked (ssh, smtp, etc.)

    Optional fields vary by service type:
    - For SSH: username_attempt, password_attempt
    - For SMTP: sender_email, recipient_email, subject, message_content, attachments

    Returns:
        JSON response with success status and message.
        HTTP status codes: 200 (success), 400 (missing fields), 500 (database error).
    """
    try:
        data = request.json
        agent_id = data.get('agent_id')

        # Validate that essential fields are present
        required_fields = ['source_ip', 'service_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        source_ip = data.get('source_ip')
        service_type = data.get('service_type')
        country_name = data.get('country_name')

        # Build attack data dictionary with all available fields
        attack_data = {
            'agent_id': data.get('agent_id'),  # Use agent_id from JWT payload
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

        # Register or update IP in malicious_ips table with relationships
        if not add_malicious_ip_address(agent_id, source_ip, service_type, country_name,
                                        data.get('country_code'), data.get('classification')):
            return jsonify({'success': False, 'error': 'Failed to add malicious IP'}), 500

        # Insert detailed attack log for forensics and analysis
        if not add_attack_log(attack_data):
            return jsonify({'success': False, 'error': 'Failed to add attack log'}), 500

        # Process service-specific data (SSH credentials, SMTP emails, etc.)
        if service_type == 'ssh':
            username_attempt = data.get('username_attempt')
            password_attempt = data.get('password_attempt')

            # Track compromised credentials for brute-force analysis
            if username_attempt and password_attempt:
                if not add_compromised_credential(source_ip, username_attempt, password_attempt, service_type):
                    return jsonify({'success': False, 'error': 'Failed to add compromised credential'}), 500

        elif service_type == 'smtp':
            sender_email = data.get('sender_email')
            recipient_email = data.get('recipient_email')
            subject = data.get('subject')
            message_content = data.get('message_content')
            attachments = data.get('attachments')

            # Store SMTP-specific data for phishing/spam analysis
            if not add_smtp_interaction(source_ip, sender_email, recipient_email,
                                        subject, message_content, attachments):
                return jsonify({'success': False, 'error': 'Failed to add SMTP interaction'}), 500

        return jsonify({'success': True, 'message': f'{service_type.upper()} attack data processed successfully'})

    except Exception as e:
        print(f"Error in agent_report: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 200


@agent_create_bp.route("/download/<int:agent_id>", methods=['GET'])
def download_agent(agent_id: int) -> Tuple[Response, int]:
    """
    Generate and download the Python honeypot agent script for a specific agent.

    This endpoint creates a customized honeypot agent script based on a template,
    filling in the agent's specific configuration (ID, token, banner, etc.).

    Args:
        agent_id: The ID of the agent to generate a script for.

    Returns:
        A Python script file as download, or JSON error response.
        HTTP status codes: 200 (success), 404 (agent not found), 500 (generation error).
    """
    try:
        # Get agent details from database
        with DatabaseManagerHoneypot() as db:
            db.execute("""SELECT agent_name, banner, ip_address
                         FROM honey_agents
                         WHERE id = ?""", (agent_id,))
            result = db.fetchone()

            if not result:
                return jsonify({'error': 'Agent not found'}), 404

            agent_name, banner, ip_address = result

        # Read the template file
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'module', 'templates', 'ssh_honeypot_agent.py'
        )

        with open(template_path, 'r') as f:
            template_content = f.read()

        # Generate a fresh JWT token for this agent download
        # We can't retrieve the original token (stored as SHA-256 hash), so generate new one
        secret_token = generate_jwt(agent_id)

        # Extract server URL from current request for agent to report back to
        server_url = request.host_url.rstrip('/')

        # Set default configuration values
        ssh_port = 22  # Default SSH port for honeypot
        if not banner:
            banner = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"  # Default SSH banner

        # Load template and substitute placeholders with actual values
        with open(template_path, 'r') as f:
            template_content = f.read()

        # Use Template for safe variable substitution
        t = Template(template_content)
        agent_content = t.substitute(
            agent_id=agent_id,
            agent_token=secret_token,
            server_url=server_url,
            ssh_port=ssh_port,
            ssh_banner=banner,
            ip_address=ip_address
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