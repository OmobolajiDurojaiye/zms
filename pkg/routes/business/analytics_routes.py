from flask import render_template, session, json
from . import business_bp
from pkg.routes.main.auth import business_owner_required
from pkg.models import db, Booking, Client, Service
from sqlalchemy import func, and_
from datetime import datetime, timedelta

@business_bp.route('/dashboard/analytics')
@business_owner_required
def analytics():
    """
    Renders the customer analytics page.
    Note: This analytics version focuses on registered clients with bookings,
    not guest checkouts, to ensure data consistency and simplicity.
    """
    owner_id = session.get('user_id')

    # Base query for all unique, registered clients who have booked with this owner
    clients_with_bookings_subquery = db.session.query(Client.id) \
        .join(Booking, Client.id == Booking.client_id) \
        .filter(Booking.business_owner_id == owner_id) \
        .distinct().subquery()

    # --- 1. Key Metrics (Stat Cards) ---
    total_customers = db.session.query(func.count(clients_with_bookings_subquery.c.id)).scalar() or 0

    # New customers in the last 30 days (based on their signup date)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_customers_30_days = db.session.query(func.count(clients_with_bookings_subquery.c.id)) \
        .join(Client, clients_with_bookings_subquery.c.id == Client.id) \
        .filter(Client.created_at >= thirty_days_ago) \
        .scalar() or 0

    # Repeat customer calculation
    booking_counts_subquery = db.session.query(
        Booking.client_id,
        func.count(Booking.id).label('booking_count')
    ).filter(Booking.business_owner_id == owner_id, Booking.client_id.isnot(None)) \
     .group_by(Booking.client_id).subquery()

    returning_customers_count = db.session.query(func.count(booking_counts_subquery.c.client_id)) \
        .filter(booking_counts_subquery.c.booking_count > 1) \
        .scalar() or 0

    repeat_customer_rate = (returning_customers_count / total_customers * 100) if total_customers > 0 else 0

    # Average spend per customer
    total_revenue_query = db.session.query(func.sum(Service.price)) \
        .join(Booking, Service.id == Booking.service_id) \
        .filter(Booking.business_owner_id == owner_id, Booking.client_id.isnot(None)) \
        .scalar() or 0
    
    avg_spend_per_customer = (total_revenue_query / total_customers) if total_customers > 0 else 0

    # --- 2. Top Customers by Revenue (List) ---
    top_customers_query = db.session.query(
        Client.full_name,
        Client.email,
        func.count(Booking.id).label('booking_count'),
        func.sum(Service.price).label('total_spent')
    ).join(Service, Booking.service_id == Service.id) \
     .join(Client, Booking.client_id == Client.id) \
     .filter(Booking.business_owner_id == owner_id, Booking.client_id.isnot(None)) \
     .group_by(Client.id, Client.full_name, Client.email) \
     .order_by(func.sum(Service.price).desc()) \
     .limit(5).all()
    
    top_customers = [{
        'name': r.full_name,
        'avatar_initials': ''.join(n[0] for n in r.full_name.split()[:2]).upper(),
        'booking_count': r.booking_count,
        'total_spent': float(r.total_spent or 0)
    } for r in top_customers_query]

    # --- 3. Recently Joined Customers (List) ---
    recent_clients_query = Client.query \
        .join(clients_with_bookings_subquery, clients_with_bookings_subquery.c.id == Client.id) \
        .order_by(Client.created_at.desc()) \
        .limit(5).all()

    recent_customers = [{
        'name': c.full_name,
        'avatar_initials': ''.join(n[0] for n in c.full_name.split()[:2]).upper(),
        'joined_at_display': c.created_at.strftime('%B %d, %Y')
    } for c in recent_clients_query]
    
    # --- 4. Gender Demographics Chart Data ---
    gender_data_query = db.session.query(
        Client.gender,
        func.count(Client.id).label('count')
    ).join(clients_with_bookings_subquery, clients_with_bookings_subquery.c.id == Client.id) \
     .filter(Client.gender.isnot(None), Client.gender != '') \
     .group_by(Client.gender).all()

    gender_chart_data = {
        'labels': [g[0] if g[0] else 'Not Specified' for g in gender_data_query],
        'data': [g[1] for g in gender_data_query]
    }
    
    # --- 5. New Customers per Month Chart Data (based on signup date) ---
    months = []
    today = datetime.utcnow()
    # Generate date objects for the start of the last 6 months
    for i in range(6):
        month_start = (today.replace(day=1) - timedelta(days=i*28)).replace(day=1)
        months.append(month_start)
    months.reverse()

    chart_labels = [m.strftime('%b %Y') for m in months]
    chart_values = []

    for i in range(len(months)):
        start_date = months[i]
        end_date = months[i+1] if i + 1 < len(months) else today + timedelta(days=1)
        
        count = db.session.query(func.count(Client.id)) \
            .join(clients_with_bookings_subquery, clients_with_bookings_subquery.c.id == Client.id) \
            .filter(and_(Client.created_at >= start_date, Client.created_at < end_date)) \
            .scalar() or 0
        chart_values.append(count)

    new_customers_chart_data = {
        'labels': chart_labels,
        'data': chart_values
    }

    # Assemble all stats for the template
    stats = {
        'total_customers': total_customers,
        'new_customers_30_days': new_customers_30_days,
        'repeat_customer_rate': round(repeat_customer_rate, 1),
        'avg_spend': float(avg_spend_per_customer or 0)
    }

    return render_template('business/analytics.html', 
                           stats=stats,
                           top_customers=top_customers,
                           recent_customers=recent_customers,
                           # Pass data as JSON for safe consumption by JavaScript
                           gender_chart_data_json=json.dumps(gender_chart_data),
                           new_customers_chart_data_json=json.dumps(new_customers_chart_data))