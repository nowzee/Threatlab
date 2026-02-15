"""
Threatlabs Flask Application.

Main application module for the Threatlabs honeypot management platform.
Handles authentication, agent management, threat intelligence and log analysis.
"""
from flask import Flask, request, session, jsonify, send_from_directory, Response
from typing import Tuple, Optional
import os
from route.auth.login import auth_bp
from route.config.security import config_account_bp
from route.agent.api_agent import agent_create_bp
from route.agent.api_user import agent_user_api_bp
from route.config.api_key import config_api_key_bp
from route.agent.manage_agent import agent_manage_bp
from route.log_analyse.alerte_dashboard import log_analyse_bp
from route.log_analyse.alerte_details import alert_details_bp
from route.CTI.threat_intelligence import threat_intel_bp
from module.database.db_manager import DatabaseManagerHoneypot, DatabaseManagerUser, DB_TYPE
import secrets

# Initialize Flask app with Vue.js frontend static files
app = Flask(__name__, static_folder='./frontend/dist', static_url_path='')

app.config['SECRET_KEY'] = secrets.token_hex(4096)

# Configure secure session cookies
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# Configure persistent agent authentication key
AGENT_KEY_FILE = os.path.join(app.root_path, '.agent_secret_key')
if os.path.exists(AGENT_KEY_FILE):
    with open(AGENT_KEY_FILE, 'r') as f:
        app.config['AGENT_SECRET_KEY'] = f.read().strip()
else:
    agent_key = secrets.token_hex(4096)
    with open(AGENT_KEY_FILE, 'w') as f:
        f.write(agent_key)
    app.config['AGENT_SECRET_KEY'] = agent_key

# Configure database path
app.config['DATABASE'] = os.path.join(app.root_path, 'honeypot.db')

# Register all application blueprints (routes modules)
app.register_blueprint(log_analyse_bp)
app.register_blueprint(alert_details_bp)
app.register_blueprint(threat_intel_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(agent_manage_bp)
app.register_blueprint(agent_create_bp)
app.register_blueprint(config_account_bp)
app.register_blueprint(agent_user_api_bp)
app.register_blueprint(config_api_key_bp)

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

@app.before_request
def before_request() -> tuple[Response, int] | None:
    """
    Execute authentication checks before each request.

    Checks if the user is authenticated and if 2FA validation is required.
    Public endpoints and agent report endpoints bypass authentication.

    Returns:
        Optional[Tuple[dict, int]]: JSON response with status code if authentication
                                    is required, None otherwise.
    """
    # Define endpoints that don't require authentication
    # Includes: static files, login, session check, Vue app, and agent reporting
    public_endpoints = ["static", "auth.login", "serve_static_or_index", "auth.session_state", "serve_vue_app", "agent_create.agent_report"]

    # Define endpoints accessible during 2FA validation process
    a2f_endpoints = ['auth.a2f', 'static', 'serve_static_or_index', 'serve_vue_app']

    # Redirect to login if user is not authenticated and trying to access protected endpoint
    if not session.get('logged_in') and request.endpoint not in public_endpoints:
        return jsonify({'auth_required': False}), 200

    # Check if 2FA validation is required
    if session.get('a2f_validate') is not None:
        # If 2FA is pending (a2f_validate=False) and endpoint requires 2FA, redirect to 2FA page
        if session['a2f_validate'] == False and request.endpoint not in a2f_endpoints:
            return jsonify({"requires_a2f": True}), 200

@app.route('/')
def serve_vue_app() -> Response:
    """
    Serve the main Vue.js application index page.

    Returns:
        str: The index.html file content.
    """
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path>', methods=['GET', 'POST'])
def serve_static_or_index(path) -> Response:
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Initialize user database (accounts, API keys, login attempts)
    with DatabaseManagerUser() as db:
        db.create_db()

    # Initialize honeypot database (agents, attack logs, malicious IPs, payloads)
    with DatabaseManagerHoneypot() as db:
        db.create_db()

    # Start Flask development server
    # Listen on all interfaces (0.0.0.0) on port 5000
    # Debug mode disabled for production-like behavior
    app.run(host='0.0.0.0', port=5000, debug=False, ssl_context='adhoc' )
