from flask import Blueprint, request, session, jsonify
from module.database.account import change_password_account


config_account_bp = Blueprint('account', __name__, url_prefix='/account')

@config_account_bp.route("/change-password", methods=['POST'])
def change_password():
    old_password = str(request.form.get('old_password'))
    new_password = str(request.form.get('new_password'))
    confirm_password = str(request.form.get('confirm_password'))

    if not old_password or not new_password or not confirm_password:
        return jsonify({'success': False})

    if len(new_password) < 12 or new_password != confirm_password:
        return jsonify({'success': False})

    if change_password_account(session['username'], old_password, new_password):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

