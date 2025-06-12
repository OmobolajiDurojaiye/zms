from . import users_bp
from flask import render_template, session, redirect, url_for, flash, request, jsonify
from functools import wraps
from pkg.models import db, Client, Service, BusinessOwner
from sqlalchemy import func, desc

# For Nigerian states list
NIGERIA_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno",
    "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT", "Gombe",
    "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos",
    "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
    "Taraba", "Yobe", "Zamfara"
]

def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # An API request is one that is a JSON request or explicitly accepts JSON.
        is_api_request = request.is_json or 'application/json' in request.accept_mimetypes

        if 'user_id' not in session:
            if is_api_request:
                return jsonify({'status': 'error', 'message': 'Authentication required. Please log in again.'}), 401
            flash('You need to be logged in to access this page.', 'warning')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='login'))
        
        if session.get('user_type') != 'client':
            if is_api_request:
                return jsonify({'status': 'error', 'message': 'Access denied. This page is for clients only.'}), 403
            flash('Access denied. This page is for clients only.', 'danger')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='login'))
        
        user = Client.query.get(session['user_id'])
        if not user:
            if is_api_request:
                session.clear()
                return jsonify({'status': 'error', 'message': 'Your session has expired or is invalid. Please log in again.'}), 401
            flash('Your session has expired or is invalid. Please log in again.', 'warning')
            session.clear()
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='login'))

        kwargs['current_client'] = user
        return f(*args, **kwargs)
    return decorated_function

@users_bp.route('/dashboard')
@client_required
def dashboard(current_client): # Receives current_client from decorator
    client_location_prefs = {
        'country': current_client.country, 
        'state': current_client.state,
        'lga_area': current_client.lga_area
    }

    location_filter_options = []
    if current_client.country and current_client.country.lower() == 'nigeria':
        location_filter_options = NIGERIA_STATES
    
    # Get top distinct business types for quick categories
    try:
        top_business_types_query = db.session.query(
                BusinessOwner.business_type,
                func.count(BusinessOwner.business_type).label('type_count')
            )\
            .filter(BusinessOwner.business_type.isnot(None), BusinessOwner.business_type != '')\
            .join(Service, BusinessOwner.id == Service.business_owner_id)\
            .filter(Service.is_active == True)\
            .group_by(BusinessOwner.business_type)\
            .order_by(desc('type_count'), BusinessOwner.business_type.asc())\
            .limit(10)\
            .all()
        
        quick_categories = [bt[0] for bt in top_business_types_query]
    except Exception as e:
        print(f"Error fetching quick categories: {e}")
        quick_categories = []

    return render_template(
        'users/dashboard.html', 
        current_user=current_client, 
        client_location_prefs=client_location_prefs,
        location_filter_options=location_filter_options,
        quick_categories=quick_categories
    )