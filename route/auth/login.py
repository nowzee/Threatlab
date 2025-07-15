from flask import Blueprint, render_template, request, redirect, url_for, session
from module.database.auth import auth_user, a2f_active
import pyotp

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():

    if session.get('logged_in'):
        if not a2f_active(session['username']):
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.a2f'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

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

    return render_template("auth/login.html")

@auth_bp.route("/a2f", methods=['GET', 'POST'])
def a2f():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    # If user already passed A2F, redirect to dashboard
    if session.get('a2f'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        code = request.form.get('code')
        # Get the user's secret key from the database or session
        # This is a placeholder - in a real app, you would retrieve the user's secret key
        secret = "JBSWY3DPEHPK3PXP"  # Example secret key

        # Create a TOTP object
        totp = pyotp.TOTP(secret)

        # Verify the code
        if totp.verify(code):
            session['a2f'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template("auth/a2f.html", error="Invalid verification code")

    return render_template("auth/a2f.html")


@auth_bp.route("/logout")
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('auth.login'))
