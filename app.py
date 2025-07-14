from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from route.auth.login import auth_bp
from route.config.security import config_account_bp
from module.database.setup_db import setup_dbs
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(2048)
app.config['DATABASE'] = os.path.join(app.root_path, 'honeypot.db')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(config_account_bp)

@app.before_request
def before_request():
    # Liste des endpoints accessibles sans authentification
    public_endpoints = ["static", "auth.login"]
    a2f_endpoints = ['auth.a2f']

    # Redirection vers login si non connecté et endpoint non public
    if not session.get('logged_in') and request.endpoint not in public_endpoints:
        return redirect(url_for('auth.login'))

@app.route("/", methods=["GET"])
def index():
    # Redirection vers le dashboard si l'utilisateur est connecté
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    # Sinon, redirection vers la page de connexion
    return redirect(url_for('auth.login'))

@app.route("/dashboard")
def dashboard():
    # Rendu de la page du tableau de bord
    return render_template("dashboard/dashboard.html")

@app.route("/manage")
def manage():
    # Page pour gérer les honeypots
    # Dans une version future, cela pourrait avoir son propre template
    return render_template("dashboard/base.html", page_title="Gérer les Honeypots")

@app.route("/deploy")
def deploy():
    # Page pour déployer de nouveaux honeypots
    return render_template("dashboard/deploy.html")

@app.route("/config")
def config():
    # Page de configuration système
    return render_template("dashboard/settings.html")

# API Routes
@app.route("/api/honeypots", methods=["GET"])
def get_honeypots():
    # Exemple de données simulées - Dans une vraie application, récupérer depuis la base de données
    honeypots = [
        {"id": 1, "name": "Web-Honeypot-1", "type": "Web Server", "status": "online", "alerts": 12},
        {"id": 2, "name": "SSH-Trap", "type": "SSH", "status": "online", "alerts": 5},
        {"id": 3, "name": "FTP-Decoy", "type": "FTP", "status": "offline", "alerts": 0}
    ]
    return jsonify({"honeypots": honeypots})

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    # Exemple de données simulées
    alerts = [
        {"id": 1, "timestamp": "2023-07-10 15:42", "honeypot": "Web-Honeypot-1", "type": "SQL Injection", "source_ip": "198.51.100.32", "severity": "high"},
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
    setup_dbs()
    # Démarrage de l'application en mode production
    app.run(host='0.0.0.0', port=5000, debug=False)
