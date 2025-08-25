from flask import Flask, render_template, request, session, jsonify, send_from_directory
import os
from route.auth.login import auth_bp
from route.config.security import config_account_bp
from route.agent.api_agent import agent_create_bp
from module.database.db_manager import DatabaseManagerHoneypot, DatabaseManagerUser
import secrets

app = Flask(__name__, static_folder='./frontend/dist', static_url_path='')
app.config['SECRET_KEY'] = secrets.token_hex(4096)
app.config['DATABASE'] = os.path.join(app.root_path, 'honeypot.db')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(agent_create_bp)
app.register_blueprint(config_account_bp)

@app.before_request
def before_request():
    # Liste des endpoints accessibles sans authentification
    public_endpoints = ["static", "auth.login", 'serve_static_or_index', 'auth.session_state', 'serve_vue_app']
    a2f_endpoints = ['auth.a2f', 'static', 'serve_static_or_index', 'serve_vue_app']

    print(request.endpoint)

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



# API Routes
@app.route("/api/honeypots", methods=["GET"])
def get_honeypots():
    # Data simulé
    honeypots = [
        {"id": 1, "name": "Web-Honeypot-1", "type": "Web Server", "status": "online", "alerts": 12},
        {"id": 2, "name": "SSH-Trap", "type": "SSH", "status": "online", "alerts": 5},
        {"id": 3, "name": "FTP-Decoy", "type": "FTP", "status": "offline", "alerts": 0}
    ]
    return jsonify({"honeypots": honeypots})

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    # données simulées
    alerts = [
        {"id": 1, "timestamp": "2023-07-10 15:42", "honeypot": "Web-Honeypot-1", "type": "SQL Injection", "source_ip": "198.51.100.42", "severity": "high"},
        {"id": 2, "timestamp": "2023-07-10 14:28", "honeypot": "SSH-Trap", "type": "Brute Force", "source_ip": "203.0.113.45", "severity": "medium"},
        {"id": 3, "timestamp": "2023-07-10 12:15", "honeypot": "Web-Honeypot-1", "type": "XSS", "source_ip": "192.0.2.18", "severity": "medium"}
    ]
    return jsonify({"alerts": alerts})

# Gestionnaire d'erreur 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Gestionnaire d'erreur 500
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialisation de la base de données
    if not os.path.exists('db'):
        os.makedirs('db')

        with DatabaseManagerUser() as db:
            db.create_db()

        with DatabaseManagerHoneypot() as db:
            db.create_db()



    app.run(host='0.0.0.0', port=5000, debug=False)
