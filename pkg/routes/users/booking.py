from . import users_bp
from flask import request, jsonify, render_template, flash
from .routes import client_required
from pkg.models import db, Service, BusinessOwner, Booking, BusinessAvailability
from datetime import datetime, timedelta, time
from sqlalchemy import and_, or_, exc
import traceback

# Endpoint to get detailed service info for the modal
@users_bp.route('/service/<int:service_id>/details')
@client_required
def get_service_details(current_client, service_id):
    service = Service.query.get_or_404(service_id)
    return jsonify(service.to_dict_for_client_view())

# Endpoint to get available time slots for a service on a specific date
@users_bp.route('/service/<int:service_id>/availability')
@client_required
def get_service_availability(current_client, service_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "Date parameter is required"}), 400

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    service = Service.query.get_or_404(service_id)
    owner = service.business_owner
    duration = timedelta(minutes=service.duration_minutes)

    # 1. Find all availability slots for the owner on that day
    day_of_week = target_date.weekday()
    
    owner_availability = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner.id,
        or_(
            BusinessAvailability.specific_date == target_date,
            and_(
                BusinessAvailability.day_of_week == day_of_week,
                BusinessAvailability.specific_date.is_(None)
            )
        )
    ).all()

    # 2. Get all existing bookings for the owner on that day
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)

    existing_bookings = Booking.query.filter(
        Booking.business_owner_id == owner.id,
        Booking.start_datetime >= start_of_day,
        Booking.start_datetime <= end_of_day,
        Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client', 'no_show'])
    ).all()
    
    booked_slots = [(b.start_datetime, b.end_datetime) for b in existing_bookings]

    # Handle blocked override slots
    blocked_periods = [
        (datetime.combine(target_date, avail.start_time), datetime.combine(target_date, avail.end_time))
        for avail in owner_availability if avail.slot_type != 'available' and avail.specific_date == target_date
    ]
    
    available_slots = []
    
    # Prioritize specific date availability over recurring
    specific_day_avail = [a for a in owner_availability if a.specific_date is not None and a.slot_type == 'available']
    if not specific_day_avail:
        # if no specific override, use recurring
        specific_day_avail = [a for a in owner_availability if a.day_of_week is not None and a.slot_type == 'available']


    for avail in specific_day_avail:
        slot_start = datetime.combine(target_date, avail.start_time)
        slot_end = datetime.combine(target_date, avail.end_time)

        current_time = slot_start
        while current_time + duration <= slot_end:
            is_available = True
            potential_end_time = current_time + duration

            # Check against existing bookings
            for booked_start, booked_end in booked_slots:
                if current_time < booked_end and potential_end_time > booked_start:
                    is_available = False
                    break
            
            # Check against blocked periods
            if is_available:
                for blocked_start, blocked_end in blocked_periods:
                    if current_time < blocked_end and potential_end_time > blocked_start:
                        is_available = False
                        break

            if is_available:
                available_slots.append(current_time.strftime('%H:%M'))
            
            # ##### FIX APPLIED HERE #####
            # Move to the next potential slot based on the service's duration,
            # not a fixed interval. This creates clean, non-overlapping slots.
            current_time += duration

    return jsonify(sorted(list(set(available_slots)))) # Use set to remove duplicates

# Endpoint to create a booking (with concurrency check)
@users_bp.route('/book', methods=['POST'])
@client_required
def create_booking(current_client):
    data = request.get_json()
    service_id = data.get('service_id')
    date_str = data.get('date')
    time_str = data.get('time')

    if not all([service_id, date_str, time_str]):
        return jsonify({'status': 'error', 'message': 'Missing required booking information.'}), 400

    try:
        service = Service.query.get_or_404(service_id)
        start_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        end_datetime = start_datetime + timedelta(minutes=service.duration_minutes)

        # --- CONCURRENCY CHECK ---
        # Check for any booking for this OWNER that overlaps the requested time
        # This is the critical step to prevent double booking.
        overlapping_booking = Booking.query.filter(
            Booking.business_owner_id == service.business_owner_id,
            Booking.end_datetime > start_datetime,
            Booking.start_datetime < end_datetime,
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client', 'no_show'])
        ).first()

        if overlapping_booking:
            # This means someone booked it while the current user was deciding.
            return jsonify({
                'status': 'error', 
                'message': 'This time slot has just been booked by someone else. Please select another time.'
            }), 409 # 409 Conflict is the appropriate HTTP status code

        new_booking = Booking(
            business_owner_id=service.business_owner_id,
            client_id=current_client.id,
            service_id=service.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            status='confirmed'
        )
        db.session.add(new_booking)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Your booking is confirmed!'}), 201

    except exc.SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'A database error occurred. Please try again.'}), 500
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred.'}), 500