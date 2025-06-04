from flask import render_template
from . import business_bp
from pkg.routes.main.auth import business_owner_required 

@business_bp.route('/dashboard/payments')
@business_owner_required
def payments():
    return render_template('business/payments.html')