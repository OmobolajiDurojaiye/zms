from . import business_bp
from flask import render_template, session
# Imports for DB queries and date handling
from pkg.routes.main.auth import business_owner_required
from pkg.models import db, BusinessOwner, Booking, Service
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from decimal import Decimal

# Helper function for calculating percentage change to avoid repetitive code
def calculate_percentage_change(current, previous):
    """Calculates the percentage change between two values."""
    # Ensure values are numeric, default to 0 if None
    current_val = float(current or 0)
    previous_val = float(previous or 0)
    
    if previous_val == 0:
        # If the previous value was 0, any increase is technically infinite.
        # We can represent this as a 100% increase if the new value is > 0, or 0% if it's also 0.
        return 100.0 if current_val > 0 else 0.0
    
    change = ((current_val - previous_val) / previous_val) * 100
    return round(change, 1)

@business_bp.route('/dashboard')
@business_owner_required
def dashboard():
    owner_id = session.get('user_id')
    current_business_owner = BusinessOwner.query.get(owner_id)

    # --- Date Ranges for "This Month" vs "Last Month" Comparison ---
    today = datetime.utcnow()
    # This month starts on day 1 at midnight
    start_of_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # To get the start of next month, we handle the year change (e.g., Dec to Jan)
    if today.month == 12:
        start_of_next_month = start_of_this_month.replace(year=today.year + 1, month=1)
    else:
        start_of_next_month = start_of_this_month.replace(month=today.month + 1)
    
    # The start of last month is day 1 of the month before the current one
    start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)

    # --- 1. Total Revenue Calculation (from 'completed' bookings) ---
    # Revenue is recognized when a service is completed. We'll check the booking's end_datetime.
    revenue_this_month = db.session.query(func.sum(Service.price))\
        .join(Booking, Service.id == Booking.service_id)\
        .filter(
            Booking.business_owner_id == owner_id,
            Booking.status == 'completed',
            Booking.end_datetime.between(start_of_this_month, start_of_next_month)
        ).scalar() or Decimal('0.00')

    revenue_last_month = db.session.query(func.sum(Service.price))\
        .join(Booking, Service.id == Booking.service_id)\
        .filter(
            Booking.business_owner_id == owner_id,
            Booking.status == 'completed',
            Booking.end_datetime.between(start_of_last_month, start_of_this_month)
        ).scalar() or Decimal('0.00')

    revenue_change = calculate_percentage_change(revenue_this_month, revenue_last_month)

    # --- 2. Total Bookings Calculation (all non-cancelled bookings) ---
    # We count bookings based on when they were created.
    bookings_this_month = db.session.query(func.count(Booking.id))\
        .filter(
            Booking.business_owner_id == owner_id,
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client']),
            Booking.created_at.between(start_of_this_month, start_of_next_month)
        ).scalar() or 0
        
    bookings_last_month = db.session.query(func.count(Booking.id))\
        .filter(
            Booking.business_owner_id == owner_id,
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client']),
            Booking.created_at.between(start_of_last_month, start_of_this_month)
        ).scalar() or 0
        
    bookings_change = calculate_percentage_change(bookings_this_month, bookings_last_month)
    
    # --- 3. Active Customers Calculation (unique registered clients with bookings) ---
    active_customers_this_month = db.session.query(func.count(func.distinct(Booking.client_id)))\
        .filter(
            Booking.business_owner_id == owner_id,
            Booking.client_id.isnot(None), # Only count registered clients, not guests
            Booking.created_at.between(start_of_this_month, start_of_next_month)
        ).scalar() or 0

    active_customers_last_month = db.session.query(func.count(func.distinct(Booking.client_id)))\
        .filter(
            Booking.business_owner_id == owner_id,
            Booking.client_id.isnot(None),
            Booking.created_at.between(start_of_last_month, start_of_this_month)
        ).scalar() or 0
        
    customers_change = calculate_percentage_change(active_customers_this_month, active_customers_last_month)
    
    # --- Assemble the final stats dictionary for the template ---
    stats = {
        'total_revenue': {
            'value': float(revenue_this_month), 
            'change': revenue_change, 
            'change_type': 'positive' if revenue_change >= 0 else 'negative'
        },
        'total_bookings': {
            'value': bookings_this_month, 
            'change': bookings_change, 
            'change_type': 'positive' if bookings_change >= 0 else 'negative'
        },
        'active_customers': {
            'value': active_customers_this_month, 
            'change': customers_change, 
            'change_type': 'positive' if customers_change >= 0 else 'negative'
        },
        # Low stock items will remain a placeholder as it requires a separate Inventory model/logic
        'low_stock_items': {
            'value': 12, 
            'change_text': '3 items need attention', 
            'change_type': 'negative'
        },
    }
    
    # Placeholder recent activities
    recent_activities = [
        {'icon': 'fas fa-shopping-cart', 'text': '<strong>New booking</strong> from Maria Johnson', 'time_ago': '2 minutes ago'},
        {'icon': 'fas fa-exclamation-triangle', 'text': '<strong>Low stock alert</strong> for Nail Polish #45', 'time_ago': '15 minutes ago'},
        {'icon': 'fas fa-money-bill', 'text': '<strong>Payment received</strong> ₦3,500 from Sarah Lee', 'time_ago': '1 hour ago'},
        {'icon': 'fas fa-user-plus', 'text': '<strong>New customer signup:</strong> John Doe', 'time_ago': '3 hours ago'}
    ]

    return render_template(
        'business/dashboard.html',
        current_business_owner=current_business_owner,
        stats=stats,
        recent_activities=recent_activities,
        page_title="Dashboard Overview"
    )