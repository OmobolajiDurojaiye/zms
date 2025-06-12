from flask import render_template, request, jsonify, flash, session, redirect, url_for, current_app
from . import business_bp  # Assuming business_bp is defined in __init__.py of the 'business' blueprint folder
from pkg.models import db, BusinessOwner, Booking, Service, Client, BusinessAvailability
from pkg.routes.main.auth import business_owner_required # Assuming this decorator is correctly defined
from datetime import datetime, date as dt_date, timedelta, time as dt_time
from sqlalchemy import or_, and_, not_
# import collections # Not strictly needed with current implementation but kept if used elsewhere

# Helper function to get current business owner
def get_current_business_owner():
    owner_id = session.get('user_id')
    if owner_id:
        return BusinessOwner.query.get(owner_id)
    return None

# Helper function to render the list of date overrides as HTML (for AJAX updates in manage_availability.html)
def _render_overrides_list_html(owner_id):
    overrides = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner_id,
        BusinessAvailability.specific_date.isnot(None)
    ).order_by(BusinessAvailability.specific_date.asc(), BusinessAvailability.start_time.asc()).all()
    # Assumes you have a partial template: 'business/partials/availability_overrides_list.html'
    # If this partial does not exist, this function will error or you'll need to create it.
    # For now, we'll assume it exists or this function is primarily for the manage_availability page.
    try:
        return render_template("business/partials/availability_overrides_list.html", date_overrides=overrides)
    except Exception as e:
        current_app.logger.error(f"Error rendering overrides partial: {e}")
        return "<p>Error loading overrides list.</p>"


@business_bp.route('/dashboard/bookings', methods=['GET'])
@business_owner_required
def bookings_overview():
    owner = get_current_business_owner()
    if not owner:
        flash('Business owner not found. Please login again.', 'danger')
        return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='login'))

    today_obj = dt_date.today()
    start_of_today = datetime.combine(today_obj, dt_time.min)
    end_of_today = datetime.combine(today_obj, dt_time.max)

    todays_bookings = Booking.query.filter(
        Booking.business_owner_id == owner.id,
        Booking.start_datetime >= start_of_today,
        Booking.start_datetime <= end_of_today,
        Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client'])
    ).order_by(Booking.start_datetime.asc()).all()

    # Services might still be needed if you have other ways to create bookings or for other UI elements.
    services = Service.query.filter_by(business_owner_id=owner.id, is_active=True).order_by(Service.name).all()

    current_calendar_month_name = today_obj.strftime("%B")
    current_calendar_year_val = today_obj.year

    return render_template('business/bookings.html',
                           page_title="Booking Management",
                           todays_bookings=todays_bookings,
                           services=services,
                           current_calendar_month_name=current_calendar_month_name,
                           current_calendar_year_val=current_calendar_year_val,
                           current_business_owner=owner,
                           today_date_iso=today_obj.isoformat())

@business_bp.route('/dashboard/bookings/create', methods=['POST'])
@business_owner_required
def create_booking():
    # This route is no longer directly triggered by the calendar click on bookings.html
    # but is kept for potential other uses (e.g., a dedicated "Create Booking" page or admin action).
    owner = get_current_business_owner()
    if not owner:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.form
    try:
        service_id = int(data.get('service_id'))
        booking_date_str = data.get('booking_date')
        booking_time_str = data.get('booking_time')

        guest_full_name = data.get('guest_full_name', "").strip()
        guest_email = data.get('guest_email', "").strip()
        guest_phone_number = data.get('guest_phone_number', "").strip()
        notes_owner = data.get('notes_owner', "").strip()

        if not all([service_id, booking_date_str, booking_time_str, guest_full_name]):
            return jsonify({'success': False, 'message': 'Service, date, time, and client name are required.'}), 400

        service = Service.query.filter_by(id=service_id, business_owner_id=owner.id, is_active=True).first()
        if not service:
            return jsonify({'success': False, 'message': 'Service not found or not active.'}), 404

        booking_date_obj = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        booking_time_obj = datetime.strptime(booking_time_str, '%H:%M').time()

        start_datetime = datetime.combine(booking_date_obj, booking_time_obj)
        end_datetime = start_datetime + timedelta(minutes=service.duration_minutes)

        # TODO: Implement robust availability check using a function like is_timeslot_available(owner.id, start_datetime, end_datetime)
        # This function would consider BusinessAvailability model (weekly and overrides)
        # and also check for existing bookings. This is crucial for a production system.

        conflicting_booking = Booking.query.filter(
            Booking.business_owner_id == owner.id,
            Booking.start_datetime < end_datetime,
            Booking.end_datetime > start_datetime,
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client', 'no_show'])
        ).first()

        if conflicting_booking:
            return jsonify({'success': False, 'message': f'This time slot conflicts with an existing booking (ID: {conflicting_booking.id}) for {conflicting_booking.service.name} with {conflicting_booking.client_display_name}.'}), 409

        new_booking = Booking(
            business_owner_id=owner.id,
            service_id=service.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            guest_full_name=guest_full_name or None,
            guest_email=guest_email or None,
            guest_phone_number=guest_phone_number or None,
            notes_owner=notes_owner or None,
            status='confirmed' # Or 'pending_confirmation' if owner needs to approve
        )
        db.session.add(new_booking)
        db.session.commit()
        flash('New booking created successfully!', 'success')
        return jsonify({'success': True, 'message': 'Booking created successfully!', 'booking': new_booking.to_dict(include_service=True)})

    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(f"ValueError during booking creation: {e}")
        return jsonify({'success': False, 'message': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Exception during booking creation: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'An unexpected error occurred. Please try again.'}), 500

@business_bp.route('/dashboard/bookings/calendar_data', methods=['GET'])
@business_owner_required
def get_calendar_bookings_data():
    owner = get_current_business_owner()
    if not owner:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    start_str = request.args.get('start')
    end_str = request.args.get('end')

    if not start_str or not end_str:
        return jsonify({'success': False, 'message': 'Start and end dates are required.'}), 400

    try:
        # Handle both ISO format with timezone and simple date strings
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00') if 'T' in start_str else start_str + "T00:00:00+00:00")
        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00') if 'T' in end_str else end_str + "T00:00:00+00:00")

        bookings_raw = Booking.query.filter(
            Booking.business_owner_id == owner.id,
            Booking.start_datetime >= start_dt,
            Booking.start_datetime < end_dt, # Use < end_dt for full day coverage if end_dt is start of next day
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client'])
        ).order_by(Booking.start_datetime.asc()).all()

        calendar_events = []
        for booking in bookings_raw:
            event_title = f"{booking.client_display_name}" # Simplified title
            calendar_events.append({
                'id': str(booking.id),
                'title': event_title,
                'start': booking.start_datetime.isoformat(),
                'end': booking.end_datetime.isoformat(),
                'status': booking.status,
                'extendedProps': { # Store extra data here for FullCalendar v5+
                    'serviceName': booking.service.name,
                    'clientName': booking.client_display_name,
                    'notes': booking.notes_owner,
                    'status': booking.status
                },
                'className': f'event-status-{booking.status.lower().replace("_", "-")}' # For custom styling
            })
        return jsonify(calendar_events)
    except Exception as e:
        current_app.logger.error(f"Error fetching calendar data: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@business_bp.route('/dashboard/bookings/<int:booking_id>/cancel', methods=['POST'])
@business_owner_required
def cancel_booking(booking_id):
    owner = get_current_business_owner()
    if not owner:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    booking = Booking.query.filter_by(id=booking_id, business_owner_id=owner.id).first_or_404()

    if booking.status.startswith('cancelled'):
        return jsonify({'success': False, 'message': 'Booking is already cancelled.'}), 400

    booking.status = 'cancelled_by_owner'
    booking.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Booking cancelled successfully.', 'success')
    return jsonify({'success': True, 'message': 'Booking cancelled successfully.'})


# --- Availability Management Routes ---

@business_bp.route('/dashboard/availability', methods=['GET'])
@business_owner_required
def manage_availability():
    owner = get_current_business_owner()
    if not owner:
        flash('Business owner not found. Please login again.', 'danger')
        return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='login'))

    weekly_slots_raw = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner.id,
        BusinessAvailability.day_of_week.isnot(None)
    ).order_by(BusinessAvailability.day_of_week, BusinessAvailability.start_time).all()

    weekly_availability_structured = []
    for _ in range(7): # Monday to Sunday
        weekly_availability_structured.append({
            "is_closed": True,
            "slots": []
        })

    days_of_week_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for slot_from_db in weekly_slots_raw:
        day_index = slot_from_db.day_of_week
        if 0 <= day_index < 7: # Ensure day_index is valid (0=Mon, 6=Sun)
            weekly_availability_structured[day_index]['is_closed'] = False
            weekly_availability_structured[day_index]['slots'].append({
                'id': slot_from_db.id,
                'start_time': slot_from_db.start_time.strftime('%H:%M'),
                'end_time': slot_from_db.end_time.strftime('%H:%M'),
                'slot_type': slot_from_db.slot_type
            })

    date_overrides = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner.id,
        BusinessAvailability.specific_date.isnot(None)
    ).order_by(BusinessAvailability.specific_date.asc(), BusinessAvailability.start_time.asc()).all()

    return render_template('business/manage_availability.html',
                           page_title="Manage Availability",
                           current_business_owner=owner,
                           weekly_availability=weekly_availability_structured,
                           date_overrides=date_overrides,
                           days_of_week_names=days_of_week_names
                           )

@business_bp.route('/dashboard/availability/weekly', methods=['POST'])
@business_owner_required
def save_weekly_availability():
    owner = get_current_business_owner()
    if not owner:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401
        
    form_data = request.form
    days_of_week_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    try:
        # Fetch existing weekly slots for this owner to compare
        existing_db_slots = BusinessAvailability.query.filter(
            BusinessAvailability.business_owner_id == owner.id,
            BusinessAvailability.day_of_week.isnot(None)
        ).all()
        existing_db_slot_ids = {slot.id for slot in existing_db_slots}
        form_slot_ids = set() # Track IDs of slots submitted in the form (for updates/presence)

        for day_idx in range(7): # Iterate 0 (Monday) through 6 (Sunday)
            day_prefix = f"days[{day_idx}]"
            is_closed = form_data.get(f"{day_prefix}[is_closed]") == 'on'

            if is_closed:
                # If day is marked closed, any existing weekly slots for this day
                # (that are not explicitly part of the form submission, if any)
                # will be removed by the deletion logic at the end.
                continue # Move to next day, no slots to process for this day

            slot_idx = 0
            while True:
                slot_prefix = f"{day_prefix}[slots][{slot_idx}]"
                start_time_str = form_data.get(f"{slot_prefix}[start_time]")
                
                if start_time_str is None: # No more slots for this day in the form
                    break

                end_time_str = form_data.get(f"{slot_prefix}[end_time]")
                slot_type = form_data.get(f"{slot_prefix}[slot_type]", 'available') # Default to 'available'
                slot_id_str = form_data.get(f"{slot_prefix}[id]") # For existing slots being updated
                slot_id = int(slot_id_str) if slot_id_str and slot_id_str.isdigit() else None

                if not start_time_str or not end_time_str: # Should be caught by 'required' on frontend ideally
                    slot_idx += 1
                    continue

                start_time_obj = dt_time.fromisoformat(start_time_str)
                end_time_obj = dt_time.fromisoformat(end_time_str)

                if start_time_obj >= end_time_obj:
                    db.session.rollback() # Important to rollback before returning error
                    return jsonify({'success': False, 'message': f'Error for {days_of_week_names[day_idx]}: Start time ({start_time_str}) must be before end time ({end_time_str}).'}), 400

                if slot_id and slot_id in existing_db_slot_ids:
                    # Update existing slot
                    slot_to_update = next((s for s in existing_db_slots if s.id == slot_id), None)
                    if slot_to_update:
                        slot_to_update.day_of_week = day_idx
                        slot_to_update.start_time = start_time_obj
                        slot_to_update.end_time = end_time_obj
                        slot_to_update.slot_type = slot_type
                        slot_to_update.specific_date = None # Ensure it's a weekly slot
                        form_slot_ids.add(slot_id) # Mark this ID as processed from the form
                else:
                    # Create new slot
                    new_slot = BusinessAvailability(
                        business_owner_id=owner.id,
                        day_of_week=day_idx,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        slot_type=slot_type,
                        specific_date=None # Explicitly None for weekly
                    )
                    db.session.add(new_slot)
                    # If you needed the ID right away, you'd flush and then could add new_slot.id to form_slot_ids.
                    # For deletion logic, we only care about existing IDs that were NOT in the form.
                slot_idx += 1
        
        # Delete slots that were in DB but not in the form submission (implies removal by user)
        slots_to_delete_ids = existing_db_slot_ids - form_slot_ids
        if slots_to_delete_ids:
            BusinessAvailability.query.filter(
                BusinessAvailability.id.in_(slots_to_delete_ids),
                BusinessAvailability.business_owner_id == owner.id, # Ensure owner context for deletion
                BusinessAvailability.day_of_week.isnot(None) # Ensure we only delete weekly slots here
            ).delete(synchronize_session=False) # 'False' is often fine, 'fetch' or 'evaluate' can be safer depending on session state.

        db.session.commit()
        flash('Weekly schedule updated successfully!', 'success')
        return jsonify({'success': True, 'message': 'Weekly schedule saved!'})

    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(f"ValueError saving weekly availability: {e}")
        return jsonify({'success': False, 'message': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving weekly availability: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred.'}), 500


@business_bp.route('/dashboard/availability/override', methods=['POST'])
@business_owner_required
def save_date_override_availability():
    owner = get_current_business_owner()
    if not owner:
         return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    form_data = request.form
    try:
        override_date_str = form_data.get('override_date')
        override_type = form_data.get('override_type') # 'available' or 'blocked_override'

        if not override_date_str or not override_type:
            return jsonify({'success': False, 'message': 'Date and override type are required.'}), 400

        specific_date_obj = dt_date.fromisoformat(override_date_str)

        # First, remove any existing overrides for this specific date for this owner to simplify logic.
        # This makes the operation idempotent for the given date.
        BusinessAvailability.query.filter_by(
            business_owner_id=owner.id,
            specific_date=specific_date_obj
        ).delete(synchronize_session='fetch') # 'fetch' ensures objects are loaded for potential further processing if needed.

        if override_type == 'blocked_override':
            # Create a single entry marking the whole day as blocked
            blocked_slot = BusinessAvailability(
                business_owner_id=owner.id,
                specific_date=specific_date_obj,
                start_time=dt_time(0, 0, 0), # Represents start of the day
                end_time=dt_time(23, 59, 59), # Represents end of the day
                slot_type='blocked_override',
                day_of_week=None # Important: this is a specific date override
            )
            db.session.add(blocked_slot)
        elif override_type == 'available':
            slot_idx = 0
            has_valid_slots = False
            while True:
                slot_prefix = f"override_slots[{slot_idx}]"
                start_time_str = form_data.get(f"{slot_prefix}[start_time]")
                if start_time_str is None: # No more slots submitted for this override
                    break

                end_time_str = form_data.get(f"{slot_prefix}[end_time]")
                # Slot type for individual slots within an "available" override can be 'available' or 'break'
                slot_type_individual = form_data.get(f"{slot_prefix}[slot_type]", 'available')

                if not start_time_str or not end_time_str:
                    slot_idx += 1
                    continue

                start_time_obj = dt_time.fromisoformat(start_time_str)
                end_time_obj = dt_time.fromisoformat(end_time_str)

                if start_time_obj >= end_time_obj:
                    db.session.rollback()
                    return jsonify({'success': False, 'message': f'For date {override_date_str}: Start time ({start_time_str}) must be before end time ({end_time_str}).'}), 400

                new_override_slot = BusinessAvailability(
                    business_owner_id=owner.id,
                    specific_date=specific_date_obj,
                    start_time=start_time_obj,
                    end_time=end_time_obj,
                    slot_type=slot_type_individual, # e.g. 'available' or 'break'
                    day_of_week=None
                )
                db.session.add(new_override_slot)
                has_valid_slots = True
                slot_idx += 1
            
            if not has_valid_slots: # No actual time slots provided for "available" type
                 db.session.rollback()
                 return jsonify({'success': False, 'message': 'For "Set Custom Hours", at least one time slot is required.'}), 400
        else:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Invalid override type specified.'}), 400


        db.session.commit()
        overrides_html = _render_overrides_list_html(owner.id) # For updating the list on manage_availability page
        flash('Date override saved successfully!', 'success')
        return jsonify({'success': True, 'message': 'Date override saved!', 'overrides_html': overrides_html})

    except ValueError as e:
        db.session.rollback()
        current_app.logger.error(f"ValueError saving date override: {e}")
        return jsonify({'success': False, 'message': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving date override: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'An unexpected error occurred.'}), 500


@business_bp.route('/dashboard/availability/delete/<int:availability_id>', methods=['DELETE', 'POST']) # Allow POST for simpler forms/links
@business_owner_required
def delete_availability_slot(availability_id):
    owner = get_current_business_owner()
    if not owner:
         return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    slot = BusinessAvailability.query.filter_by(id=availability_id, business_owner_id=owner.id).first_or_404()

    try:
        is_date_override = slot.specific_date is not None
        db.session.delete(slot)
        db.session.commit()

        if is_date_override:
            overrides_html = _render_overrides_list_html(owner.id) # Regenerate list for manage_availability page
            flash('Date override slot deleted successfully!', 'success')
            return jsonify({'success': True, 'message': 'Availability slot deleted.', 'overrides_html': overrides_html})
        else: # It was a weekly slot
             flash('Weekly availability slot deleted. The page may need to be refreshed to see all changes to the weekly schedule.', 'success')
             # For weekly, a full page reload or more complex JS update on manage_availability.html would be needed.
             # For simplicity, this just returns success; the manage_availability page would refetch on next load.
             return jsonify({'success': True, 'message': 'Weekly availability slot deleted.'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting availability slot {availability_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to delete slot.'}), 500

@business_bp.route('/dashboard/availability/on_date', methods=['GET'])
@business_owner_required
def get_availability_for_date():
    owner = get_current_business_owner()
    if not owner:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'success': False, 'message': 'Date parameter is required.'}), 400

    try:
        target_date = dt_date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Please use YYYY-MM-DD.'}), 400

    # MODIFIED: Fetch bookings for the day, to be included in every response.
    start_of_day = datetime.combine(target_date, dt_time.min)
    end_of_day = datetime.combine(target_date, dt_time.max)
    todays_bookings_query = Booking.query.filter(
        Booking.business_owner_id == owner.id,
        Booking.start_datetime.between(start_of_day, end_of_day),
        Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client'])
    ).options(db.joinedload(Booking.service)).order_by(Booking.start_datetime.asc()).all()
    bookings_data = [b.to_dict(include_service=True) for b in todays_bookings_query]


    # 1. Check for specific date overrides for the target_date
    specific_overrides = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner.id,
        BusinessAvailability.specific_date == target_date
    ).order_by(BusinessAvailability.start_time.asc()).all()

    if specific_overrides:
        if any(slot.slot_type == 'blocked_override' for slot in specific_overrides):
            return jsonify({
                'success': True,
                'date': date_str,
                'type': 'specific_override_blocked',
                'message': f'This day ({target_date.strftime("%A, %b %d")}) is set as unavailable/blocked.',
                'slots': [slot.to_dict() for slot in specific_overrides],
                'bookings': bookings_data
            })
        else: # Custom hours
            return jsonify({
                'success': True,
                'date': date_str,
                'type': 'specific_override_custom_hours',
                'message': f'Custom availability for {target_date.strftime("%A, %b %d")}:',
                'slots': [slot.to_dict() for slot in specific_overrides],
                'bookings': bookings_data
            })

    # 2. If no specific overrides, fall back to the weekly schedule
    day_of_week_num = target_date.weekday()  # Monday is 0 and Sunday is 6

    weekly_slots = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner.id,
        BusinessAvailability.day_of_week == day_of_week_num
    ).order_by(BusinessAvailability.start_time.asc()).all()

    if weekly_slots:
        return jsonify({
            'success': True,
            'date': date_str,
            'day_of_week': day_of_week_num,
            'type': 'weekly_schedule',
            'message': f'Weekly availability for {target_date.strftime("%A, %b %d")}:',
            'slots': [slot.to_dict() for slot in weekly_slots],
            'bookings': bookings_data
        })
    else: # No weekly slots defined, so it's closed.
        return jsonify({
            'success': True,
            'date': date_str,
            'day_of_week': day_of_week_num,
            'type': 'weekly_closed',
            'message': f'{target_date.strftime("%A, %b %d")} is closed according to the weekly schedule.',
            'slots': [],
            'bookings': bookings_data
        })