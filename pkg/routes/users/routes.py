from . import users_bp
from flask import render_template, session, redirect, url_for, flash, request, jsonify
from functools import wraps
from pkg.models import db, Client, Service, BusinessOwner, BusinessAvailability
from sqlalchemy import or_, and_, func, desc, case
from datetime import datetime as dt_parser
import traceback

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
def dashboard(current_client):
    client_location_prefs = {
        'country': current_client.country, 
        'state': current_client.state,
        'lga_area': current_client.lga_area
    }

    location_filter_options = NIGERIA_STATES if current_client.country and current_client.country.lower() == 'nigeria' else []
    
    try:
        all_types = db.session.query(BusinessOwner.business_type).filter(BusinessOwner.business_type.isnot(None)).distinct().all()
        # Flatten the list of lists and get unique, sorted values
        quick_categories = sorted(list(set(t for types_list in all_types for t in types_list[0] if t)))
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

@users_bp.route('/search')
@client_required
def search_results(current_client):
    try:
        search_params = {
            'q': request.args.get('q', '', type=str),
            'category': request.args.get('category', '', type=str),
            'location': request.args.get('location', 'all', type=str),
            'date': request.args.get('date', '', type=str),
            'time': request.args.get('time', '', type=str),
            'sortBy': request.args.get('sortBy', 'relevance', type=str)
        }
        page = request.args.get('page', 1, type=int)
        per_page = 12

        query = Service.query.join(BusinessOwner, Service.business_owner_id == BusinessOwner.id)\
                             .filter(Service.is_active == True)

        if search_params['q']:
            search_term = f"%{search_params['q']}%"
            query = query.filter(or_(
                Service.name.ilike(search_term),
                Service.description.ilike(search_term),
                BusinessOwner.business_name.ilike(search_term),
                db.cast(BusinessOwner.business_type, db.String).ilike(search_term)
            ))

        if search_params['category']:
            if db.engine.dialect.name == 'postgresql':
                 query = query.filter(BusinessOwner.business_type.op('?')(search_params['category']))
            else:
                 query = query.filter(db.cast(BusinessOwner.business_type, db.String).ilike(f"%{search_params['category']}%"))

        if search_params['location'] and search_params['location'] != 'all':
            query = query.filter(BusinessOwner.state == search_params['location'])
        
        if search_params['date']:
            target_date = dt_parser.strptime(search_params['date'], '%Y-%m-%d').date()
            target_dow = target_date.weekday()

            available_owners_subquery = db.session.query(BusinessAvailability.business_owner_id)\
                .filter(BusinessAvailability.slot_type == 'available')\
                .filter(or_(
                    BusinessAvailability.specific_date == target_date,
                    and_(BusinessAvailability.specific_date.is_(None), BusinessAvailability.day_of_week == target_dow)
                ))

            if search_params['time']:
                target_time = dt_parser.strptime(search_params['time'], '%H:%M').time()
                available_owners_subquery = available_owners_subquery.filter(
                    BusinessAvailability.start_time <= target_time,
                    BusinessAvailability.end_time >= target_time
                )
            
            blocked_owners_subquery = db.session.query(BusinessAvailability.business_owner_id)\
                .filter(BusinessAvailability.slot_type != 'available')\
                .filter(BusinessAvailability.specific_date == target_date)

            query = query.filter(Service.business_owner_id.in_(available_owners_subquery))
            query = query.filter(Service.business_owner_id.notin_(blocked_owners_subquery))

        sort_by = search_params['sortBy']
        if sort_by == 'price-low':
            query = query.order_by(Service.price.asc())
        elif sort_by == 'price-high':
            query = query.order_by(Service.price.desc())
        elif sort_by == 'rating':
            query = query.order_by(Service.created_at.desc()) # Placeholder
        else: # 'relevance'
            relevance_order = []
            if current_client.state:
                relevance_order.append(case((BusinessOwner.state == current_client.state, 0), else_=1).asc())
            if search_params['q']:
                search_term = f"%{search_params['q']}%"
                relevance_order.append(case((Service.name.ilike(search_term), 0), else_=1).asc())
                relevance_order.append(case((BusinessOwner.business_name.ilike(search_term), 0), else_=2).asc())
            relevance_order.append(Service.id.desc())
            query = query.order_by(*relevance_order)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        services = [s.to_dict_for_client_view() for s in pagination.items]

        location_filter_options = NIGERIA_STATES if current_client.country and current_client.country.lower() == 'nigeria' else []
        
        all_types = db.session.query(BusinessOwner.business_type).filter(BusinessOwner.business_type.isnot(None)).distinct().all()
        quick_categories = sorted(list(set(t for types_list in all_types for t in types_list[0] if t)))

        return render_template(
            'users/search_result.html', 
            current_user=current_client,
            results=services,
            pagination=pagination,
            search_params=search_params,
            location_filter_options=location_filter_options,
            quick_categories=quick_categories
        )
    except Exception as e:
        traceback.print_exc()
        return "An error occurred during your search. Please try again later.", 500

