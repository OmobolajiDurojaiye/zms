from flask import render_template
from . import business_bp
from pkg.routes.main.auth import business_owner_required

@business_bp.route('/dashboard/customers')
@business_owner_required
def customers():
    return render_template('business/customers.html')