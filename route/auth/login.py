"""
Authentication Route Module.

This module provides Flask routes for user authentication, including
login, two-factor authentication (A2F), session management, and logout.
"""

from typing import Tuple
from flask import Blueprint, jsonify, session, request, Response
from module.database.auth import auth_user, a2f_active, get_otp_secret
from module.database.account import log_attempt_account
import pyotp

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/session', methods=['GET'])
def session_state() -> Tuple[Response, int]:
    """
    Check the current session authentication state.

    Returns:
        A JSON response containing:
        - authenticated: Whether the user is fully authenticated
        - requires_a2f: Whether two-factor authentication is pending
        - username: The authenticated username (or None)
        HTTP status code 200.
    """
    authenticated = bool(session.get('logged_in'))
    requires_a2f = session.get('a2f_validate') is False
    username = session.get('username') if authenticated else None
    return jsonify({
        "authenticated": authenticated and not requires_a2f,
        "requires_a2f": requires_a2f,
        "username": username
    }), 200


@auth_bp.route("/login", methods=['GET', 'POST'])
def login() -> Tuple[Response, int]:
    """
    Handle user login with optional two-factor authentication.

    This endpoint accepts username and password credentials and initiates
    the login process. If A2F is enabled for the user, a second step is required.

    Returns:
        JSON response with authentication status and A2F requirement if applicable.
        HTTP status codes: 200 (success), 401 (authentication failed).
    """
    if request.is_json:
        if session.get('logged_in'):
            if session.get('a2f_validate') is False:
                return jsonify({"requires_a2f": True}), 200
            return jsonify({"authenticated": True}), 200

        data = request.get_json(silent=True) or {}
        username = (data.get('username') or "").strip()
        password = data.get('password') or ""
        # Validate input length to prevent DoS and ensure reasonable limits (140 chars max)
        if not username or not password or len(username) > 140 or len(password) > 140:
            return jsonify({"error": "Invalid username or password"}), 401
        # Attempt authentication with provided credentials
        if not auth_user(username, password):
            # Log failed attempt for security monitoring
            log_attempt_account(username, request.remote_addr, 'Failed login')
            return jsonify({"error": "Invalid username or password"}), 401


        # Credentials valid - establish session
        session['logged_in'] = True
        session['username'] = username

        # Check if user has 2FA enabled
        if a2f_active(username):
            # Mark session as requiring 2FA verification before full access
            session['a2f_validate'] = False
            log_attempt_account(username, request.remote_addr, 'A2F required')
            return jsonify({"authenticated": True, "requires_a2f": True}), 200

        # No 2FA required - grant full access
        log_attempt_account(username, request.remote_addr, 'Successful login')
        return jsonify({"authenticated": True}), 200


@auth_bp.route("/a2f", methods=['GET', 'POST'])
def a2f() -> Tuple[Response, int]:
    """
    Handle two-factor authentication verification.

    This endpoint validates the TOTP code provided by the user after
    initial login when A2F is enabled.

    Returns:
        JSON response indicating A2F validation success or failure.
        HTTP status codes: 200 (success), 400 (invalid code), 401 (not authenticated).
    """
    # Check if the user is logged in
    if not session.get('logged_in'):
        if request.is_json:
            return jsonify({"error": "Non authentifié"}), 401

    # If the user has already passed A2F, redirect to dashboard
    if session.get('a2f_validate'):
        if request.is_json:
            return jsonify({"authenticated": True, "requires_a2f": False}), 200

    if request.method == 'POST':
        if request.is_json:
            # Processing for JSON requests (Vue.js)
            data = request.get_json(silent=True) or {}
            code = data.get('code', '').strip()

            if not code:
                return jsonify({"error": "Veuillez entrer un code de vérification"}), 400

            # Retrieve the encrypted OTP secret from database and decrypt it
            secret = get_otp_secret(session['username'])

            # Create TOTP verifier using the secret (6-digit codes, 30-second window)
            totp = pyotp.TOTP(secret)

            # Verify the 6-digit code - allows for time drift tolerance
            if totp.verify(code):
                # Code valid - complete authentication process
                session['a2f_validate'] = True
                log_attempt_account(session['username'], request.remote_addr, 'A2F validated')
                return jsonify({"authenticated": True, "requires_a2f": False}), 200
            else:
                # Code invalid - log failed attempt for security monitoring
                log_attempt_account(session['username'], request.remote_addr, 'A2F failed')
                return jsonify({"error": "Code de vérification invalide"}), 400


@auth_bp.route("/logout")
def logout() -> Response:
    """
    Clear the user session and log out.

    Returns:
        JSON response confirming session has been cleared.
    """
    session.clear()
    return jsonify({"clear": True})