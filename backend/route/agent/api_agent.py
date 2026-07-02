"""
Agent API Route Module.

This module provides Flask routes for honeypot agent operations,
including agent creation, attack reporting, and agent file downloads.
"""

from typing import Tuple
from flask import Blueprint, jsonify, request, current_app, send_file, Response
import jwt
import os
import hashlib
from module.database.agent import create_agent_token, add_malicious_ip_address, add_compromised_credential, add_attack_log, add_smtp_interaction, get_agent_about, record_uploaded_file
from module.database.db_manager import DatabaseManagerHoneypot
from module.ingestion.ingest import enqueue_report
from string import Template
from module.auth.decorator import agent_jwt_required
from module.auth.session_helpers import current_user_id, current_username, is_admin
from module.database.audit import log_audit

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
    - banner: Service banner to display (default: SSH banner)

    Returns:
        JSON response with agent_id and secret_token on success.
        HTTP status codes: 200 (success), 500 (creation failed).
    """
    try:
        agent_name = request.json.get('agent_name')
        agent_type = request.json.get('agent_type', 'ssh')
        ip_address = request.json.get('ip_address', '0.0.0.0')
        country_name = request.json.get('country_name')
        banner = request.json.get('banner', 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5')
        interactive = bool(request.json.get('interactive', True))
        allow_upload = bool(request.json.get('allow_upload', True))

        # Listening port(s) chosen by the user. Accepts a single value, a list,
        # or a "22,2222"/"22 2222" string. Stored as a comma-separated list.
        default_port = 22 if agent_type == 'ssh' else (21 if agent_type == 'ftp' else 22)
        raw_ports = request.json.get('port')
        if raw_ports is None:
            raw_ports = request.json.get('ports')
        if isinstance(raw_ports, list):
            candidates = raw_ports
        elif raw_ports is None:
            candidates = []
        else:
            candidates = str(raw_ports).replace(',', ' ').split()
        ports = []
        for c in candidates:
            try:
                pi = int(c)
            except (TypeError, ValueError):
                continue
            if 1 <= pi <= 65535 and pi not in ports:
                ports.append(pi)
        if not ports:
            ports = [default_port]
        port = ','.join(str(p) for p in ports)

        # Interactive-shell auth policy. Credential capture is ALWAYS on; this
        # only controls which credentials may enter the fake shell.
        import json as _json
        auth_mode = request.json.get('auth_mode', 'any')
        if auth_mode not in ('any', 'whitelist'):
            auth_mode = 'any'
        raw_wl = request.json.get('auth_whitelist') or []
        allow = []
        if isinstance(raw_wl, list):
            for e in raw_wl[:100]:
                if not isinstance(e, dict):
                    continue
                u = str(e.get('username') or '').strip()[:255]
                p = str(e.get('password') or '').strip()[:255]
                if u or p:
                    entry = {}
                    if u:
                        entry['username'] = u
                    if p:
                        entry['password'] = p
                    allow.append(entry)
        # A whitelist only makes sense in interactive mode and with real entries;
        # otherwise fall back to 'any' so the shell stays reachable.
        if not interactive or auth_mode != 'whitelist' or not allow:
            auth_mode = 'any'
            auth_whitelist_json = None
        else:
            auth_whitelist_json = _json.dumps(allow)

        # Stamp ownership with the current session user so members only see
        # their own honeypots (admins still see everything).
        owner_id = current_user_id()

        agent_id, secret_token = create_agent_token(
            agent_name,
            ip_address=ip_address,
            country_name=country_name,
            service_type=agent_type,
            banner=banner,
            interactive=interactive,
            allow_upload=allow_upload,
            owner_id=owner_id,
            auth_mode=auth_mode,
            auth_whitelist=auth_whitelist_json,
            port=port
        )

        if agent_id:
            log_audit('agent.create', actor_id=owner_id, actor_username=current_username(),
                      target_type='agent', target_id=agent_id,
                      detail=f"name={agent_name}, type={agent_type}", ip_address=request.remote_addr)
            return jsonify({
                'success': True,
                'secret_token': secret_token,
                'agent_id': agent_id
            }), 200
        else:
            print(f"Failed to create agent for {agent_id} with IP {ip_address}")
            return jsonify({'success': False, 'error': 'Failed to create agent'}), 500
    except Exception as e:
        import traceback
        print(f"Error in agent_create: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Internal error: {str(e)}'}), 500


@agent_create_bp.route("/upload", methods=['POST'])
@agent_jwt_required
def agent_upload() -> Tuple[Response, int]:
    """
    Receive a file uploaded to an interactive honeypot (e.g. FTP STOR).

    The agent sends the raw file plus metadata (hash, ip, username, password,
    request headers). The server recomputes the SHA-256 (no trust in the agent
    hash), stores the file once (dedup by hash) in a created folder, and records
    the metadata in the uploaded_files table.

    Returns JSON: {success, new, hash}. `new` is False if this hash was already
    known (file not re-stored).
    """
    try:
        f = request.files.get('file')
        if f is None:
            return jsonify({'success': False, 'error': 'no file provided'}), 400

        file_bytes = f.read()
        if not file_bytes:
            return jsonify({'success': False, 'error': 'empty file'}), 400

        # Hash recomputed server-side (we don't trust the agent-provided hash).
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        form = request.form
        upload_dir = os.getenv('UPLOAD_DIR', '/app/uploads')
        os.makedirs(upload_dir, exist_ok=True)
        stored_path = os.path.join(upload_dir, file_hash)

        # Storage dedup: only write the file if the hash is unknown.
        is_new = not os.path.exists(stored_path)
        if is_new:
            with open(stored_path, 'wb') as out:
                out.write(file_bytes)

        agent_id = form.get('agent_id')
        try:
            agent_id = int(agent_id) if agent_id else None
        except (TypeError, ValueError):
            agent_id = None

        record_uploaded_file(
            file_hash=file_hash,
            file_name=form.get('file_name') or f.filename,
            file_size=len(file_bytes),
            stored_path=stored_path,
            source_ip=form.get('source_ip'),
            username=form.get('username'),
            password=form.get('password'),
            request_headers=form.get('request_headers'),
            agent_id=agent_id,
            service_type=form.get('service_type', 'ftp'),
        )

        return jsonify({'success': True, 'new': is_new, 'hash': file_hash}), 200

    except Exception as e:
        print(f"Error in agent_upload: {e}")
        return jsonify({'success': False, 'error': 'internal server error'}), 500


@agent_create_bp.route("/report", methods=['POST'])
@agent_jwt_required
def agent_report() -> tuple[Response, int] | Response:
    """
    Receive and process attack reports from honeypot agents.

    This endpoint is protected by JWT authentication and processes attack data
    based on the service type (SSH, FTP, SMTP, port_scan, etc.).

    Required fields in JSON body:
    - source_ip: The attacker's IP address
    - service_type: The service being attacked (ssh, ftp, smtp, port_scan, etc.)

    Optional fields vary by service type:
    - For SSH/FTP: username_attempt, password_attempt
    - For SMTP: sender_email, recipient_email, subject, message_content, attachments
    - For port_scan: ports_scanned, scan_count

    Returns:
        JSON response with success status and message.
        HTTP status codes: 200 (success), 400 (missing fields), 500 (database error).
    """
    try:
        data = request.json or {}

        # Validate that essential fields are present
        required_fields = ['source_ip', 'service_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        # Build a normalized report and hand it to the async ingestion worker.
        # The heavy DB work (IP upsert, attack log, credentials) is done off the
        # request thread, with attack_logs written in batches.
        report = {
            'agent_id': data.get('agent_id'),
            'source_ip': data.get('source_ip'),
            'service_type': data.get('service_type'),
            'source_port': data.get('source_port'),
            'target_port': data.get('target_port'),
            'username_attempt': data.get('username_attempt'),
            'password_attempt': data.get('password_attempt'),
            'payload': data.get('payload'),
            'malware_hash': data.get('malware_hash'),
            'classification': data.get('classification'),
            'attack_type': data.get('attack_type', 'auth_attempt'),
            'country_code': data.get('country_code'),
            'country_name': data.get('country_name'),
            # SMTP-specific fields (ignored for other service types)
            'sender_email': data.get('sender_email'),
            'recipient_email': data.get('recipient_email'),
            'subject': data.get('subject'),
            'message_content': data.get('message_content'),
            'attachments': data.get('attachments'),
        }

        # Queue full = overload: return 503, the agent re-queues and retries.
        if not enqueue_report(report):
            return jsonify({'success': False, 'error': 'ingestion overloaded, retry later'}), 503

        return jsonify({'success': True, 'message': 'attack report queued'}), 200

    except Exception as e:
        print(f"Error in agent_report: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 200


@agent_create_bp.route("/download/<int:agent_id>", methods=['GET'])
def download_agent(agent_id: int) -> Tuple[Response, int]:
    """
    Generate and download the Python honeypot agent script for a specific agent.

    This endpoint creates a customized honeypot agent script based on a template,
    filling in the agent's specific configuration (ID, token, banner, etc.) and
    configuring features based on the agent's service type.

    Args:
        agent_id: The ID of the agent to generate a script for.

    Returns:
        A Python script file as download, or JSON error response.
        HTTP status codes: 200 (success), 404 (agent not found), 500 (generation error).
    """
    try:
        # Get agent details from database including service_type
        with DatabaseManagerHoneypot() as db:
            db.execute("""
                       SELECT agent_name, banner, ip_address, service_type, interactive, allow_upload,
                              auth_mode, auth_whitelist, port
                       FROM honey_agents
                       WHERE id = %s
                       """, (agent_id,))

            result = db.fetchone()

            if not result:
                return jsonify({'error': 'Agent not found'}), 404

            agent_name = result['agent_name']
            banner = result['banner']
            ip_address = result['ip_address']
            service_type = result['service_type']
            interactive = bool(result.get('interactive', 1))
            allow_upload = bool(result.get('allow_upload', 1))
            auth_mode = result.get('auth_mode') or 'any'
            auth_whitelist_raw = result.get('auth_whitelist')
            port_val = result.get('port')

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
        # Use request.url_root which includes protocol and host
        server_url = request.url_root.rstrip('/')

        # If server_url is empty or None, use a fallback
        if not server_url:
            # Try to construct from request
            scheme = request.scheme or 'https'
            host = request.host or 'localhost:5000'
            server_url = f"{scheme}://{host}"

        # Default configuration template
        default_config = {
            "agent_id": agent_id,
            "agent_token": secret_token,
            "server_url": server_url,
            "features": {
                "ssh_enabled": True,
                "ftp_enabled": False,
                "port_scan_detection": True,
                "auth_detection": True
            },
            "ssh": {
                "host": ip_address if ip_address else "0.0.0.0",
                "port": 22,
                "banner": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5",
                "host_key_file": "ssh_host_key.pem",
                "interactive": interactive,
                "allow_upload": allow_upload,
                "fetch_downloads": allow_upload,
                "hostname": "srv01"
            },
            "ftp": {
                "host": ip_address if ip_address else "0.0.0.0",
                "port": 21,
                "banner": "220 FTP server ready",
                "interactive": interactive,
                "allow_upload": allow_upload,
                "session_min_seconds": 600,
                "session_max_seconds": 900,
                "max_upload_bytes": 52428800,
                "public_ip": ""
            },
            "reporting": {
                "interval": 30,
                "endpoint": "/api/agent/report"
            },
            "port_scan": {
                "threshold": 5,
                "time_window": 10
            }
        }

        # Configure features based on service_type
        if service_type == 'ssh':
            # SSH only configuration
            default_config['features']['ssh_enabled'] = True
            default_config['features']['ftp_enabled'] = False
            if banner:
                default_config['ssh']['banner'] = banner

        elif service_type == 'ftp':
            # FTP only configuration
            default_config['features']['ssh_enabled'] = False
            default_config['features']['ftp_enabled'] = True
            if banner:
                default_config['ftp']['banner'] = banner

        else:
            # Default to SSH configuration for unknown types
            default_config['features']['ssh_enabled'] = True
            default_config['features']['ftp_enabled'] = False
            if banner:
                default_config['ssh']['banner'] = banner

        # Interactive-shell auth policy (credential capture is always on; this
        # only controls which credentials may enter the fake shell).
        import json
        auth_allow = []
        if auth_whitelist_raw:
            try:
                parsed = json.loads(auth_whitelist_raw)
                if isinstance(parsed, list):
                    auth_allow = [e for e in parsed if isinstance(e, dict)]
            except Exception:
                auth_allow = []
        default_config['auth'] = {
            'mode': auth_mode if auth_mode in ('any', 'whitelist') else 'any',
            'allow': auth_allow,
        }

        # Apply the user-chosen listening port(s) to the active service. The DB
        # stores a comma-separated list; the agent listens on all of them.
        default_p = 21 if service_type == 'ftp' else 22
        eff_ports = []
        for c in str(port_val or '').replace(',', ' ').split():
            try:
                pi = int(c)
            except (TypeError, ValueError):
                continue
            if 1 <= pi <= 65535 and pi not in eff_ports:
                eff_ports.append(pi)
        if not eff_ports:
            eff_ports = [default_p]
        svc_key = 'ftp' if service_type == 'ftp' else 'ssh'
        default_config[svc_key]['ports'] = eff_ports
        default_config[svc_key]['port'] = eff_ports[0]

        # Serialize config as JSON. The template parses it with json.loads(r\"\"\"...\"\"\"),
        # so plain JSON (lowercase true/false/null) is correct and user-supplied
        # strings (passwords) are embedded safely.
        config_json = json.dumps(default_config, indent=4)

        # Load template and substitute placeholders with actual values
        with open(template_path, 'r') as f:
            template_content = f.read()

        # Use Template for safe variable substitution
        t = Template(template_content)

        try:
            agent_content = t.substitute(
                default_config_json=config_json
            )
        except KeyError as ke:
            print(f"Missing template variable: {ke}")
            print(f"Config JSON: {config_json[:200]}...")
            raise

        # Write to temporary file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(agent_content)
        temp_file.close()

        filename = f"agent_{agent_name.replace(' ', '_')}.py"

        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='text/x-python'
        )

        return response

    except Exception as e:
        import traceback
        print(f"Error generating agent download: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to generate agent file: {str(e)}'}), 500

@agent_create_bp.route("/about/<int:agent_id>", methods=['GET'])
def about_agent(agent_id: int) -> Tuple[Response, int]:
    """
    Get detailed information about a specific honeypot agent.

    Args:
        agent_id: The ID of the agent.

    Returns:
        JSON with agent details, stats, attacks, and country ranking.
    """
    try:
        # Members can only inspect their own honeypots (returns 404 otherwise).
        data = get_agent_about(agent_id, viewer_id=current_user_id(), is_admin=is_admin())
        if data is None:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        return jsonify({'success': True, 'agent': data}), 200
    except Exception as e:
        print(f"Error in about_agent: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@agent_create_bp.route("/install/<int:agent_id>", methods=['GET'])
def install_agent(agent_id: int) -> Tuple[Response, int]:
    """
    Generate and download a bash install script for deploying a honeypot agent.

    Args:
        agent_id: The ID of the agent to generate the install script for.

    Returns:
        A bash script file as download.
    """
    try:
        with DatabaseManagerHoneypot() as db:
            db.execute("""
                SELECT agent_name, banner, ip_address, service_type, port
                FROM honey_agents
                WHERE id = %s
            """, (agent_id,))
            result = db.fetchone()

            if not result:
                return jsonify({'error': 'Agent not found'}), 404

        # Generate a fresh JWT token
        secret_token = generate_jwt(agent_id)

        # Build server URL
        server_url = request.url_root.rstrip('/')
        if not server_url:
            scheme = request.scheme or 'https'
            host = request.host or 'localhost:5000'
            server_url = f"{scheme}://{host}"

        # Pick the installer for the target OS: bash (.sh) for Linux (default),
        # PowerShell (.ps1) for Windows. Both share the same {{PLACEHOLDER}} contract.
        os_target = (request.args.get('os') or 'linux').lower()
        if os_target in ('windows', 'win', 'ps', 'powershell'):
            template_name, ext, mimetype = 'install_agent.ps1', 'ps1', 'text/plain'
        else:
            template_name, ext, mimetype = 'install_agent.sh', 'sh', 'text/x-shellscript'

        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'module', 'templates', template_name
        )

        with open(template_path, 'r') as f:
            script_content = f.read()

        # Inject values
        script_content = script_content.replace('{{AGENT_ID}}', str(agent_id))
        script_content = script_content.replace('{{AGENT_TOKEN}}', secret_token)
        script_content = script_content.replace('{{SERVER_URL}}', server_url)
        script_content = script_content.replace('{{SERVICE_TYPE}}', result['service_type'] or 'ssh')
        script_content = script_content.replace('{{AGENT_NAME}}', result['agent_name'] or f'agent-{agent_id}')
        script_content = script_content.replace('{{BANNER}}', result['banner'] or 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5')
        _svc = result['service_type'] or 'ssh'
        _default_p = 21 if _svc == 'ftp' else 22
        _ports = []
        for c in str(result.get('port') or '').replace(',', ' ').split():
            try:
                pi = int(c)
            except (TypeError, ValueError):
                continue
            if 1 <= pi <= 65535 and pi not in _ports:
                _ports.append(pi)
        if not _ports:
            _ports = [_default_p]
        # Space-separated list, e.g. "22 2222" — used by the installer for -p / EXPOSE.
        script_content = script_content.replace('{{PORTS}}', ' '.join(str(p) for p in _ports))

        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.' + ext, delete=False)
        temp_file.write(script_content)
        temp_file.close()

        filename = f"install_{result['agent_name'].replace(' ', '_')}.{ext}"

        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )

        return response

    except Exception as e:
        import traceback
        print(f"Error generating install script: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to generate install script: {str(e)}'}), 500