from flask import Flask, request, session, jsonify, send_from_directory
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
from module.database.db_manager import DatabaseManagerHoneypot, DatabaseManagerUser
import secrets
app = Flask(__name__, static_folder='./frontend/dist', static_url_path='')
app.config['SECRET_KEY'] = secrets.token_hex(4096)
app.config['DATABASE'] = os.path.join(app.root_path, 'honeypot.db')

# Register blueprints
app.register_blueprint(log_analyse_bp)
app.register_blueprint(alert_details_bp)
app.register_blueprint(threat_intel_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(agent_manage_bp)
app.register_blueprint(agent_create_bp)
app.register_blueprint(config_account_bp)
app.register_blueprint(agent_user_api_bp)
app.register_blueprint(config_api_key_bp)

@app.before_request
def before_request():
    # Liste des endpoints accessibles sans authentification
    public_endpoints = ["static", "auth.login", "serve_static_or_index", "auth.session_state", "serve_vue_app", "agent_create.agent_report"]
    a2f_endpoints = ['auth.a2f', 'static', 'serve_static_or_index', 'serve_vue_app']

    # Redirection vers login si non connecté et endpoint non public
    if not session.get('logged_in') and request.endpoint not in public_endpoints:
        return jsonify({'auth_required': False}), 200

    if session.get('a2f_validate') is not None:
        if session['a2f_validate'] == False and request.endpoint not in a2f_endpoints:
            return jsonify({"requires_a2f": True}), 200

@app.route('/')
def serve_vue_app():
    return send_from_directory(app.static_folder, 'index.html')

# Permet à Vue Router de fonctionner avec les routes personnalisées
@app.route('/<path>', methods=['GET', 'POST'])
def serve_static_or_index(path):
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Initialisation de la base de données
    if not os.path.exists('db'):
        os.makedirs('db')

        with DatabaseManagerUser() as db:
            db.create_db()

        with DatabaseManagerHoneypot() as db:
            db.create_db()


    app.run(host='0.0.0.0', port=5000, debug=False)
