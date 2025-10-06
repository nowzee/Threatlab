"""
Security Configuration Route Module.

This module provides Flask routes for security-related account settings,
including password changes and two-factor authentication (A2F) management.
"""

from typing import Tuple, Dict, Any
from flask import Blueprint, request, session, jsonify, Response
from module.database.account import change_password_account
from module.database.auth import auth_user, get_otp_secret, update_otp_status, a2f_active
import re
import pyotp
import qrcode
import io
import base64


config_account_bp = Blueprint('account', __name__, url_prefix='/account')


@config_account_bp.route("/change-password", methods=['POST'])
def change_password() -> Response:
    """
    Handle password change requests.

    Validates password requirements (length, complexity) and updates
    the user's password if all checks pass.

    Returns:
        JSON response with success status and error message if applicable.
    """
    old_password = str(request.form.get('old_password'))
    new_password = str(request.form.get('new_password'))
    confirm_password = str(request.form.get('confirm_password'))

    if not old_password or not new_password or not confirm_password:
        return jsonify({'success': False, 'error': 'Tous les champs sont obligatoires'})

    # Minimum length verification
    if len(new_password) < 12:
        return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 12 caractères'})

    # Maximum length verification
    if len(new_password) > 140:
        return jsonify({'success': False, 'error': 'Le mot de passe ne doit pas dépasser 140 caractères'})

    # Verify passwords match
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'Les mots de passe ne correspondent pas'})

    # Strength verification with regex
    # At least one lowercase letter, one uppercase, one digit and one special character
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


@config_account_bp.route("/active_a2f", methods=['POST'])
def active_a2f() -> Response:
    """
    Enable or disable two-factor authentication for the user.

    When enabling A2F, generates a TOTP secret and QR code for the user.
    When disabling, requires verification of a TOTP code.

    Returns:
        JSON response with success status, and for activation:
        - secret: The TOTP secret
        - qrcode: Base64-encoded QR code image
    """
    activated = request.form.get('active')
    password = request.form.get('password')


    if request.form.get('password') is None or request.form.get('active') is None:
        return jsonify({'success': False, 'error': 'Informations manquantes'})

    if not auth_user(session['username'], password):
        return jsonify({'success': False, 'error': 'Mot de passe incorrect'})

    if activated == 'true':
        # Create OTP key with QR code generation
        # Use a reasonable secret size for TOTP app compatibility
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Create the URL for the QR code
        provisioning_url = totp.provisioning_uri(name=session['username'], issuer_name='Threatlab')

        # Generate QR code server-side
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_url)
        qr.make(fit=True)

        # Create an image from the QR code
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert the image to base64 to send to client
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Store the secret in the database
        if update_otp_status(session['username'], 1, secret):
            return jsonify({
                'success': True,
                'secret': secret,
                'qrcode': f"data:image/png;base64,{qr_code_base64}"
            })
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'activation de l\'A2F'})

    elif activated == 'false':
        # Disable A2F with temporary code verification
        code = request.form.get('code')
        if not code:
            return jsonify({'success': False, 'error': 'Code de vérification manquant'})

        # Retrieve existing secret to verify the code
        secret = get_otp_secret(session['username'])
        if not secret:
            return jsonify({'success': False, 'error': 'Configuration A2F non trouvée'})

        # Verify TOTP code
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            # Disable A2F for this user
            if update_otp_status(session['username'], 0):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Erreur lors de la désactivation de l\'A2F'})
        else:
            return jsonify({'success': False, 'error': 'Code incorrect'})

    return jsonify({'success': False, 'error': 'Opération non reconnue'})


@config_account_bp.route("/check_a2f_status", methods=['GET'])
def check_a2f_status() -> Tuple[Response, int]:
    """
    Check if two-factor authentication is enabled for the logged-in user.

    Returns:
        JSON response with A2F activation status.
        HTTP status codes: 200 (success), 401 (not authenticated), 500 (error).
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
def valide_a2f() -> Response:
    """
    Validate that the user has stored their A2F secret correctly.

    Confirms that the user can provide a valid TOTP code from their
    authenticator app, proving they have saved the secret.

    Returns:
        JSON response indicating validation success or failure.
    """
    code = request.form.get('code')
    secret = get_otp_secret(session['username'])

    totp = pyotp.TOTP(secret)

    # Verify the code
    if totp.verify(code):
        update_otp_status(session['username'], 2, secret)
        return jsonify({'success': True})
    else:
        update_otp_status(session['username'], active_code=0)
        return jsonify({'success': False})