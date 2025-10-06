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

    # Enforce minimum length of 12 characters for security
    if len(new_password) < 12:
        return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 12 caractères'})

    # Enforce maximum length to prevent DoS attacks
    if len(new_password) > 140:
        return jsonify({'success': False, 'error': 'Le mot de passe ne doit pas dépasser 140 caractères'})

    # Verify both password fields match to prevent typos
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'Les mots de passe ne correspondent pas'})

    # Enforce complexity requirements using regex with positive lookaheads
    # (?=.*[a-z]) - requires at least one lowercase letter
    # (?=.*[A-Z]) - requires at least one uppercase letter
    # (?=.*[0-9]) - requires at least one digit
    # (?=.*[!@#$%^&*(),.?":{}|<>]) - requires at least one special character
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
        # Generate a random base32-encoded secret for TOTP (standard 32-char length)
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Create provisioning URI for authenticator apps (Google Authenticator, Authy, etc.)
        # Format: otpauth://totp/Threatlab:username?secret=XXX&issuer=Threatlab
        provisioning_url = totp.provisioning_uri(name=session['username'], issuer_name='Threatlab')

        # Generate QR code image that encodes the provisioning URI
        qr = qrcode.QRCode(
            version=1,  # Size of QR code (1 is smallest)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # ~7% error correction
            box_size=10,  # Pixels per "box" in QR code
            border=4,  # Border width in boxes (minimum is 4)
        )
        qr.add_data(provisioning_url)
        qr.make(fit=True)

        # Render QR code as black and white image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to base64-encoded PNG for sending to browser
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Store encrypted secret in database with status 1 (pending verification)
        if update_otp_status(session['username'], 1, secret):
            return jsonify({
                'success': True,
                'secret': secret,
                'qrcode': f"data:image/png;base64,{qr_code_base64}"
            })
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'activation de l\'A2F'})

    elif activated == 'false':
        # User wants to disable 2FA - require TOTP code verification first
        code = request.form.get('code')
        if not code:
            return jsonify({'success': False, 'error': 'Code de vérification manquant'})

        # Retrieve and decrypt the user's OTP secret
        secret = get_otp_secret(session['username'])
        if not secret:
            return jsonify({'success': False, 'error': 'Configuration A2F non trouvée'})

        # Verify user still has access to their authenticator app before disabling
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            # Code valid - disable 2FA by setting status to 0
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