from . import users_bp
from flask import render_template, request
from .routes import client_required, NIGERIA_STATES # Import decorator and states
from pkg.models import db, Service, BusinessOwner, BusinessAvailability
from sqlalchemy import or_, and_, func, desc, case
from datetime import datetime as dt_parser
import traceback

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

        # --- 2. BASE QUERY ---
        query = Service.query.join(BusinessOwner, Service.business_owner_id == BusinessOwner.id)\
                             .filter(Service.is_active == True)

        # --- 3. APPLY FILTERS based on search_params ---
        if search_params['q']:
            search_term = f"%{search_params['q']}%"
            query = query.filter(or_(
                Service.name.ilike(search_term),
                Service.description.ilike(search_term),
                BusinessOwner.business_name.ilike(search_term),
                BusinessOwner.business_type.ilike(search_term)
            ))

        if search_params['category']:
            query = query.filter(BusinessOwner.business_type == search_params['category'])

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

        # --- 4. APPLY SORTING ---
        sort_by = search_params['sortBy']
        if sort_by == 'price-low':
            query = query.order_by(Service.price.asc())
        elif sort_by == 'price-high':
            query = query.order_by(Service.price.desc())
        elif sort_by == 'name':
            query = query.order_by(Service.name.asc())
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

        # --- 5. PAGINATE RESULTS ---
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        services = [s.to_dict_for_client_view() for s in pagination.items]

        # --- 6. GET FILTER OPTIONS FOR THE VIEW ---
        location_filter_options = []
        if current_client.country and current_client.country.lower() == 'nigeria':
            location_filter_options = NIGERIA_STATES
            
        top_business_types_query = db.session.query(BusinessOwner.business_type)\
            .filter(BusinessOwner.business_type.isnot(None), BusinessOwner.business_type != '')\
            .group_by(BusinessOwner.business_type)\
            .order_by(func.count(BusinessOwner.id).desc()).limit(10).all()
        quick_categories = [bt[0] for bt in top_business_types_query]

        # --- 7. RENDER TEMPLATE ---
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