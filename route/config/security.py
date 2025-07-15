from flask import Blueprint, request, session, jsonify
from module.database.account import change_password_account
from module.database.auth import auth_user
import re
import pyotp


config_account_bp = Blueprint('account', __name__, url_prefix='/account')

@config_account_bp.route("/change-password", methods=['POST'])
def change_password():
    old_password = str(request.form.get('old_password'))
    new_password = str(request.form.get('new_password'))
    confirm_password = str(request.form.get('confirm_password'))

    if not old_password or not new_password or not confirm_password:
        return jsonify({'success': False, 'error': 'Tous les champs sont obligatoires'})

    # Vérification de la longueur minimale
    if len(new_password) < 12:
        return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 12 caractères'})

    # Vérification de la longueur maximale
    if len(new_password) > 140:
        return jsonify({'success': False, 'error': 'Le mot de passe ne doit pas dépasser 140 caractères'})

    # Vérification que les mots de passe correspondent
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'Les mots de passe ne correspondent pas'})

    # Vérification de la robustesse avec regex
    # Au moins une lettre minuscule, une majuscule, un chiffre et un caractère spécial
    password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).*$')

    if not password_pattern.match(new_password):
        return jsonify({
            'success': False, 
            'error': 'Le mot de passe doit contenir au moins une lettre minuscule, une majuscule, un chiffre et un caractère spécial'
        })

    if change_password_account(session['username'], old_password, new_password):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

# Requete pour activer ou désactiver l'a2f
@config_account_bp.route("/active_a2f", methods=['POST'])
def active_a2f():

    activated = request.form.get('active')
    password = request.form.get('password')

    if request.form.get('password') is None or request.form.get('active') is None:
        return jsonify({'success': False})

    if not auth_user(session['username'], password):
        return jsonify({'success': False})

    if activated == 'true':
        # création de la clé otp avec le Qr code

        secret = pyotp.random_hex(2048)
        totp = pyotp.TOTP(secret)
        return jsonify({'success': True, 'secret': secret, 'url': totp.provisioning_uri(name=session['username'], issuer_name='Threatlab')})
    elif activated == 'false':
        # Désactivation de l'a2f avec demande de du code temporaire pour valider la désactivation
        code = request.form.get('code')
        secret = pyotp.random_hex(2048)
        if pyotp.TOTP(secret).verify(code):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Code incorrect'})


    return jsonify({'success': False})