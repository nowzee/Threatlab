"""
Security Configuration Route Module.

This module provides Flask routes for security-related account settings,
including password changes and two-factor authentication (A2F) management.
"""

from typing import Tuple
from flask import Blueprint, request, session, jsonify, Response
from module.database.account import change_password_account
from module.database.auth import auth_user, get_otp_secret, update_otp_status, a2f_active
from module.auth.password_policy import validate_password
from module.database.audit import log_audit
from module.auth.session_helpers import current_user_id
import pyotp
import qrcode
import io
import base64


config_account_bp = Blueprint('account', __name__, url_prefix='/account')


@config_account_bp.route("/change-password", methods=['POST'])
def change_password() -> Response:

    old_password = str(request.form.get('old_password'))
    new_password = str(request.form.get('new_password'))
    confirm_password = str(request.form.get('confirm_password'))

    if not old_password or not new_password or not confirm_password:
        return jsonify({'success': False, 'error': 'Tous les champs sont obligatoires'})

    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'Les mots de passe ne correspondent pas'})

    ok, msg = validate_password(new_password)
    if not ok:
        return jsonify({'success': False, 'error': msg})

    if change_password_account(session['username'], old_password, new_password):
        log_audit('account.password_changed', actor_id=current_user_id(),
                  actor_username=session.get('username'), ip_address=request.remote_addr)
        return jsonify({'success': True})
    else:
        log_audit('account.password_change_failed', actor_id=current_user_id(),
                  actor_username=session.get('username'), detail='Ancien mot de passe incorrect',
                  ip_address=request.remote_addr)
        return jsonify({'success': False})


@config_account_bp.route("/active_a2f", methods=['POST'])
def active_a2f() -> Response:
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
                log_audit('account.2fa_disabled', actor_id=current_user_id(),
                          actor_username=session.get('username'), ip_address=request.remote_addr)
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Erreur lors de la désactivation de l\'A2F'})
        else:
            return jsonify({'success': False, 'error': 'Code incorrect'})

    return jsonify({'success': False, 'error': 'Opération non reconnue'})


@config_account_bp.route("/check_a2f_status", methods=['GET'])
def check_a2f_status() -> Tuple[Response, int]:
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
    code = request.form.get('code')
    secret = get_otp_secret(session['username'])

    totp = pyotp.TOTP(secret)

    # Verify the code
    if totp.verify(code):
        update_otp_status(session['username'], 2, secret)
        log_audit('account.2fa_enabled', actor_id=current_user_id(),
                  actor_username=session.get('username'), ip_address=request.remote_addr)
        return jsonify({'success': True})
    else:
        update_otp_status(session['username'], active_code=0)
        return jsonify({'success': False})