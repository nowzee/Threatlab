from flask import Blueprint, jsonify, session, request, redirect, url_for, render_template
from module.database.auth import auth_user, a2f_active, get_otp_secret
import pyotp

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/session', methods=['GET'])
def session_state():
    authenticated = bool(session.get('logged_in'))
    requires_a2f = session.get('a2f_validate') is False
    username = session.get('username') if authenticated else None
    return jsonify({
        "authenticated": authenticated and not requires_a2f,
        "requires_a2f": requires_a2f,
        "username": username
    }), 200

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.is_json:
        if session.get('logged_in'):
            if session.get('a2f_validate') is False:
                return jsonify({"requires_a2f": True}), 200
            return jsonify({"authenticated": True}), 200

        data = request.get_json(silent=True) or {}
        username = (data.get('username') or "").strip()
        password = data.get('password') or ""
        if not username or not password or len(username) > 140 or len(password) > 140:
            return jsonify({"error": "Invalid username or password"}), 401
        if not auth_user(username, password):
            return jsonify({"error": "Invalid username or password"}), 401

        session['logged_in'] = True
        session['username'] = username

        if a2f_active(username):
            session['a2f_validate'] = False
            return jsonify({"authenticated": True, "requires_a2f": True}), 200
        return jsonify({"authenticated": True}), 200

@auth_bp.route("/a2f", methods=['GET', 'POST'])
def a2f():
    # Vérifier si l'utilisateur est connecté
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    # Si l'utilisateur a déjà passé l'A2F, rediriger vers le tableau de bord
    if session.get('a2f_validate'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        code = request.form.get('code')
        if not code:
            return render_template("auth/a2f.html", error="Veuillez entrer un code de vérification")

        # Récupérer la clé secrète de l'utilisateur depuis la base de données
        secret = get_otp_secret(session['username'])
        if not secret:
            return render_template("auth/a2f.html", error="Erreur de configuration A2F. Contactez l'administrateur.")

        # Créer un objet TOTP pour vérification
        totp = pyotp.TOTP(secret)

        # Vérifier le code
        if totp.verify(code):
            session['a2f_validate'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template("auth/a2f.html", error="Code de vérification invalide")

    return render_template("auth/a2f.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return jsonify({"clear": True})