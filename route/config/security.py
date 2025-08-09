from flask import Blueprint, request, session, jsonify
from module.database.account import change_password_account
from module.database.auth import auth_user, get_otp_secret, update_otp_status, a2f_active
import re
import pyotp
import qrcode
import io
import base64


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
        return jsonify({'success': False, 'error': 'Informations manquantes'})

    if not auth_user(session['username'], password):
        return jsonify({'success': False, 'error': 'Mot de passe incorrect'})

    if activated == 'true':
        # Création de la clé otp avec génération du QR code
        # Utiliser un secret de taille raisonnable pour compatibilité avec les applications TOTP
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Créer l'URL pour le QR code
        provisioning_url = totp.provisioning_uri(name=session['username'], issuer_name='Threatlab')

        # Générer le QR code côté serveur
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_url)
        qr.make(fit=True)

        # Créer une image à partir du QR code
        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir l'image en base64 pour l'envoyer au client
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Stocker le secret dans la base de données
        if update_otp_status(session['username'], 1, secret):
            return jsonify({
                'success': True,
                'secret': secret,
                'qrcode': f"data:image/png;base64,{qr_code_base64}"
            })
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'activation de l\'A2F'})

    elif activated == 'false':
        # Désactivation de l'a2f avec vérification du code temporaire
        code = request.form.get('code')
        if not code:
            return jsonify({'success': False, 'error': 'Code de vérification manquant'})

        # Récupérer le secret existant pour vérifier le code
        secret = get_otp_secret(session['username'])
        if not secret:
            return jsonify({'success': False, 'error': 'Configuration A2F non trouvée'})

        # Vérifier le code TOTP
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            # Désactiver l'A2F pour cet utilisateur
            if update_otp_status(session['username'], 0):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Erreur lors de la désactivation de l\'A2F'})
        else:
            return jsonify({'success': False, 'error': 'Code incorrect'})

    return jsonify({'success': False, 'error': 'Opération non reconnue'})

@config_account_bp.route("/check_a2f_status", methods=['GET'])
def check_a2f_status():
    """
    Endpoint pour vérifier si l'authentification à deux facteurs est activée pour l'utilisateur connecté
    """
    if not session.get('logged_in') or not session.get('username'):
        return jsonify({'success': False, 'error': 'Non authentifié'}), 401

    try:
        is_active = a2f_active(session['username'])
        if is_active == 1:
            is_active = True
        elif is_active == 0 :
            is_active = False
        else:
            is_active = True
        return jsonify({'success': True, 'active': is_active})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@config_account_bp.route("/validation_a2f", methods=['POST'])
def valide_a2f():
    """
    Endpoint pour confirmer que l'utilisateur a bien stocké son secret et qu'il puisse le prouver avec son code TOTP
    """

    code = request.form.get('code')
    secret = get_otp_secret(session['username'])

    totp = pyotp.TOTP(secret)

    # Vérifier le code
    if totp.verify(code):
        update_otp_status(session['username'], 2, secret)
        return jsonify({'success': True})
    else:
        update_otp_status(session['username'], active_code=0)
        return jsonify({'success': False})