from . import users_bp
from flask import request, jsonify, render_template, flash, current_app
from .routes import client_required
from pkg.routes.main.auth import send_email # <-- IMPORT THE SEND_EMAIL FUNCTION
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

# MODIFIED: Endpoint to get available time slots for a service on a specific date
# or find the next available date.
@users_bp.route('/service/<int:service_id>/availability')
@client_required
def get_service_availability(current_client, service_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "Date parameter is required"}), 400

    try:
        initial_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    service = Service.query.get_or_404(service_id)
    if not service.duration_minutes:
        return jsonify({
            'date': initial_date.isoformat(),
            'slots': [],
            'message': 'This service has no duration set and cannot be booked online.'
        }), 400

    owner = service.business_owner
    duration = timedelta(minutes=service.duration_minutes)

    # Search for availability for up to 90 days from the initial requested date
    for i in range(91):
        current_search_date = initial_date + timedelta(days=i)
        
        # 1. Find all availability rules for the owner on that day
        day_of_week = current_search_date.weekday()
        owner_availability = BusinessAvailability.query.filter(
            BusinessAvailability.business_owner_id == owner.id,
            or_(
                BusinessAvailability.specific_date == current_search_date,
                and_(
                    BusinessAvailability.day_of_week == day_of_week,
                    BusinessAvailability.specific_date.is_(None)
                )
            )
        ).all()

        # 2. Get all existing bookings for the owner on that day
        start_of_day = datetime.combine(current_search_date, time.min)
        end_of_day = datetime.combine(current_search_date, time.max)
        existing_bookings = Booking.query.filter(
            Booking.business_owner_id == owner.id,
            Booking.start_datetime >= start_of_day,
            Booking.start_datetime <= end_of_day,
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client', 'no_show'])
        ).all()
        booked_slots = [(b.start_datetime, b.end_datetime) for b in existing_bookings]

        # 3. Handle blocked override slots for that day
        blocked_periods = [
            (datetime.combine(current_search_date, avail.start_time), datetime.combine(current_search_date, avail.end_time))
            for avail in owner_availability if avail.slot_type != 'available' and avail.specific_date == current_search_date
        ]
        
        # 4. Generate potential slots based on availability rules
        available_slots = []
        specific_day_avail = [a for a in owner_availability if a.specific_date is not None and a.slot_type == 'available']
        if not specific_day_avail:
            specific_day_avail = [a for a in owner_availability if a.day_of_week is not None and a.slot_type == 'available']

        for avail in specific_day_avail:
            slot_start = datetime.combine(current_search_date, avail.start_time)
            slot_end = datetime.combine(current_search_date, avail.end_time)
            current_time = slot_start
            while current_time + duration <= slot_end:
                is_available = True
                potential_end_time = current_time + duration
                
                # Check against existing bookings
                for booked_start, booked_end in booked_slots:
                    if current_time < booked_end and potential_end_time > booked_start:
                        is_available = False; break
                if not is_available:
                    current_time += duration; continue
                
                # Check against blocked periods
                for blocked_start, blocked_end in blocked_periods:
                    if current_time < blocked_end and potential_end_time > blocked_start:
                        is_available = False; break
                
                if is_available:
                    available_slots.append(current_time.strftime('%H:%M'))
                
                current_time += duration
        
        final_slots = sorted(list(set(available_slots)))

        # 5. Filter out slots that are in the past for today's date
        if current_search_date == datetime.today().date():
            now_time = datetime.now().time()
            final_slots = [s for s in final_slots if datetime.strptime(s, '%H:%M').time() >= now_time]

        if final_slots:
            # We found available slots! Prepare a response.
            message = ""
            if current_search_date > initial_date:
                message = f"No slots on {initial_date.strftime('%b %d')}. Showing next available day."
            
            return jsonify({
                'date': current_search_date.isoformat(),
                'slots': final_slots,
                'message': message
            })

    # If the loop completes, no slots were found in the search range
    return jsonify({
        'date': initial_date.isoformat(),
        'slots': [],
        'message': 'No available slots found in the next 90 days for this service.'
    })


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
        # MODIFIED: Check if service duration is present before creating booking
        if not service.duration_minutes:
            return jsonify({'status': 'error', 'message': 'Cannot book a service with no duration.'}), 400
        end_datetime = start_datetime + timedelta(minutes=service.duration_minutes)

        # --- CONCURRENCY CHECK ---
        overlapping_booking = Booking.query.filter(
            Booking.business_owner_id == service.business_owner_id,
            Booking.end_datetime > start_datetime,
            Booking.start_datetime < end_datetime,
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client', 'no_show'])
        ).first()

        if overlapping_booking:
            return jsonify({
                'status': 'error', 
                'message': 'This time slot has just been booked by someone else. Please select another time.'
            }), 409

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

        # --- SEND BOOKING NOTIFICATION EMAILS (AFTER COMMIT) ---
        try:
            send_email(
                to=new_booking.client.email,
                subject='Your Booking is Confirmed!',
                template='emails/client_booking.html',
                booking=new_booking
            )
            send_email(
                to=new_booking.business_owner.email,
                subject=f'New Booking Notification: {new_booking.service.name}',
                template='emails/bo_bookings.html',
                booking=new_booking
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send booking confirmation email: {e}")

        return jsonify({'status': 'success', 'message': 'Your booking is confirmed!'}), 201

    except exc.SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'A database error occurred. Please try again.'}), 500
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred.'}), 500