from . import users_bp
from flask import render_template

@users_bp.route('/dashboard')
def dashboard():
    return render_template('users/dashboard.html') 