from flask import Blueprint, request, session, jsonify
from module.database.account import change_password_account
import re


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

