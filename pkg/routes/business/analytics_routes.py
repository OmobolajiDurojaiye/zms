from flask import render_template
from . import business_bp
from pkg.routes.main.auth import business_owner_required 

@business_bp.route('/dashboard/analytics')
@business_owner_required
def analytics():
    return render_template('business/analytics.html')