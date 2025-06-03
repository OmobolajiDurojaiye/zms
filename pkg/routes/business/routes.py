from . import business_bp
from flask import render_template

@business_bp.route('/dashboard')
def dashboard():
    return render_template('business/dashboard.html')