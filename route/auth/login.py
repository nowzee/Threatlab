from flask import Blueprint, render_template, request, redirect, url_for, session
from module.database.auth import auth_user, a2f_active, get_otp_secret
import pyotp

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():

    if session.get('logged_in'):
        if not a2f_active(session['username']):
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.a2f'))

    if request.method == 'POST' and request.content_length < 400:
        username = request.form.get('username')
        password = request.form.get('password')

        if len(username) > 140 or len(password) > 140:
            return render_template("auth/login.html", error="Invalid username or password")

        if auth_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            if a2f_active(session['username']):
                session['a2f_validate'] = False
                return redirect(url_for('auth.a2f'))
            else:
                return redirect(url_for('dashboard'))
        else:
            return render_template("auth/login.html", error="Invalid username or password")
    elif request.method == 'POST' and request.content_length > 400:
        return render_template("auth/login.html", error="Invalid username or password")
    return render_template("auth/login.html")

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
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('auth.login'))
