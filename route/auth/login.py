from flask import Blueprint, jsonify, session, request
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