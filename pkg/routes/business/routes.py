# pkg/business/routes.py

from . import business_bp
from flask import render_template, session
from pkg.models import db, BusinessOwner
from pkg.routes.main.auth import business_owner_required

@business_bp.route('/dashboard')
@business_owner_required
def dashboard():
    owner_id = session.get('user_id')
    current_business_owner = BusinessOwner.query.get(owner_id)
    
    # Placeholder stats - replace with real data queries later
    stats = {
        'total_revenue': {'value': 45230, 'change': 12.5, 'change_type': 'positive'},
        'total_bookings': {'value': 127, 'change': 8.2, 'change_type': 'positive'},
        'active_customers': {'value': 89, 'change': 15.3, 'change_type': 'positive'},
        'low_stock_items': {'value': 12, 'change_text': '3 items need attention', 'change_type': 'negative'},
    }
    recent_activities = [
        {'icon': 'fas fa-shopping-cart', 'text': '<strong>New booking</strong> from Maria Johnson', 'time_ago': '2 minutes ago'},
        {'icon': 'fas fa-exclamation-triangle', 'text': '<strong>Low stock alert</strong> for Nail Polish #45', 'time_ago': '15 minutes ago'},
        {'icon': 'fas fa-money-bill', 'text': '<strong>Payment received</strong> ₦3,500 from Sarah Lee', 'time_ago': '1 hour ago'}
    ]

    return render_template(
        'business/dashboard.html',
        current_business_owner=current_business_owner,
        stats=stats,
        recent_activities=recent_activities,
        page_title="Dashboard Overview"
    )
