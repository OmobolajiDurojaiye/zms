from flask import render_template, request, jsonify, flash, session, redirect, url_for, current_app
from . import business_bp
from pkg.models import db, BusinessOwner, Booking, Service, Client, BusinessAvailability
from pkg.routes.main.auth import business_owner_required
from datetime import datetime, date as dt_date, timedelta, time as dt_time
from sqlalchemy import or_, and_, not_
import collections # For defaultdict (though we simplified its direct use in one spot)

# Helper function to get current business owner
def get_current_business_owner():
    owner_id = session.get('user_id')
    if owner_id:
        return BusinessOwner.query.get(owner_id)
    return None

# Helper function to render the list of date overrides as HTML (for AJAX updates)
def _render_overrides_list_html(owner_id):
    overrides = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner_id,
        BusinessAvailability.specific_date.isnot(None)
    ).order_by(BusinessAvailability.specific_date.asc(), BusinessAvailability.start_time.asc()).all()
    # Assumes you have a partial template: 'business/partials/availability_overrides_list.html'
    return render_template("business/partials/availability_overrides_list.html", date_overrides=overrides)


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
        # and also check for existing bookings.

        # Basic conflict check for existing bookings (should be part of the more robust check later)
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
            status='confirmed'
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
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00') if 'T' in start_str else start_str + "T00:00:00+00:00")
        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00') if 'T' in end_str else end_str + "T00:00:00+00:00")

        bookings_raw = Booking.query.filter(
            Booking.business_owner_id == owner.id,
            Booking.start_datetime >= start_dt,
            Booking.start_datetime < end_dt,
            Booking.status.notin_(['cancelled_by_owner', 'cancelled_by_client'])
        ).order_by(Booking.start_datetime.asc()).all()

        calendar_events = []
        for booking in bookings_raw:
            event_title = f"{booking.service.name} - {booking.client_display_name}"
            calendar_events.append({
                'id': str(booking.id),
                'title': event_title,
                'start': booking.start_datetime.isoformat(),
                'end': booking.end_datetime.isoformat(),
                'status': booking.status,
                'serviceName': booking.service.name,
                'clientName': booking.client_display_name,
                'notes': booking.notes_owner,
                'className': f'event-status-{booking.status.lower().replace("_", "-")}'
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

    # Fetch existing weekly availability
    weekly_slots_raw = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner.id,
        BusinessAvailability.day_of_week.isnot(None)
    ).order_by(BusinessAvailability.day_of_week, BusinessAvailability.start_time).all()

    # Structure for the template: list of 7 days, each is a dictionary.
    # Each dictionary will have 'is_closed' (boolean) and 'slots' (list of slot dicts).
    weekly_availability_structured = []
    for _ in range(7):
        weekly_availability_structured.append({
            "is_closed": True,  # Default to closed
            "slots": []         # Always initialize 'slots' as an empty list
        })

    days_of_week_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for slot_from_db in weekly_slots_raw:
        day_index = slot_from_db.day_of_week
        if 0 <= day_index < 7: # Ensure day_index is valid
            # If we find any slot for a day, it means the day is not entirely closed.
            weekly_availability_structured[day_index]['is_closed'] = False
            
            # Append the current slot to the 'slots' list for that day
            weekly_availability_structured[day_index]['slots'].append({
                'id': slot_from_db.id,
                'start_time': slot_from_db.start_time.strftime('%H:%M'),
                'end_time': slot_from_db.end_time.strftime('%H:%M'),
                'slot_type': slot_from_db.slot_type
            })

    # Fetch existing date overrides
    date_overrides = BusinessAvailability.query.filter(
        BusinessAvailability.business_owner_id == owner.id,
        BusinessAvailability.specific_date.isnot(None)
    ).order_by(BusinessAvailability.specific_date.asc(), BusinessAvailability.start_time.asc()).all()

    return render_template('business/manage_availability.html',
                           page_title="Manage Availability",
                           current_business_owner=owner,
                           weekly_availability=weekly_availability_structured,
                           date_overrides=date_overrides,
                           days_of_week_names=days_of_week_names # Passed for potential use in template
                           )

@business_bp.route('/dashboard/availability/weekly', methods=['POST'])
@business_owner_required
def save_weekly_availability():
    owner = get_current_business_owner()
    form_data = request.form
    days_of_week_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


    try:
        existing_db_slots = BusinessAvailability.query.filter(
            BusinessAvailability.business_owner_id == owner.id,
            BusinessAvailability.day_of_week.isnot(None)
        ).all()
        existing_db_slot_ids = {slot.id for slot in existing_db_slots}
        form_slot_ids = set() # To track IDs of slots submitted in the form (for updates)

        for day_idx in range(7): # Iterate 0 through 6 for days
            day_prefix = f"days[{day_idx}]"
            is_closed = form_data.get(f"{day_prefix}[is_closed]") == 'on'

            if is_closed:
                # If day is marked closed, any existing weekly slots for this day
                # (that are not in form_slot_ids) will be deleted by the logic below.
                continue # Move to next day

            slot_idx = 0
            while True:
                slot_prefix = f"{day_prefix}[slots][{slot_idx}]"
                start_time_str = form_data.get(f"{slot_prefix}[start_time]")
                
                if start_time_str is None: # No more slots for this day in the form
                    break

                end_time_str = form_data.get(f"{slot_prefix}[end_time]")
                slot_type = form_data.get(f"{slot_prefix}[slot_type]", 'available')
                slot_id_str = form_data.get(f"{slot_prefix}[id]")
                slot_id = int(slot_id_str) if slot_id_str and slot_id_str.isdigit() else None

                if not start_time_str or not end_time_str: # Should be caught by 'required' on frontend
                    slot_idx += 1
                    continue

                start_time_obj = dt_time.fromisoformat(start_time_str)
                end_time_obj = dt_time.fromisoformat(end_time_str)

                if start_time_obj >= end_time_obj:
                    db.session.rollback()
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
                        form_slot_ids.add(slot_id)
                else:
                    # Create new slot
                    new_slot = BusinessAvailability(
                        business_owner_id=owner.id,
                        day_of_week=day_idx,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        slot_type=slot_type,
                        specific_date=None
                    )
                    db.session.add(new_slot)
                    # If you need the ID of the new slot immediately for some reason (e.g., to return it),
                    # you would db.session.flush() here and then add new_slot.id to form_slot_ids.
                    # However, for deletion logic, we only care about existing IDs.
                slot_idx += 1
        
        # Delete slots that were in DB but not in the form submission (implies removal)
        slots_to_delete_ids = existing_db_slot_ids - form_slot_ids
        if slots_to_delete_ids:
            BusinessAvailability.query.filter(
                BusinessAvailability.id.in_(slots_to_delete_ids),
                BusinessAvailability.business_owner_id == owner.id # extra safety
            ).delete(synchronize_session=False)

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
    form_data = request.form
    try:
        override_date_str = form_data.get('override_date')
        override_type = form_data.get('override_type') # 'available' or 'blocked_override'

        if not override_date_str or not override_type:
            return jsonify({'success': False, 'message': 'Date and override type are required.'}), 400

        specific_date_obj = dt_date.fromisoformat(override_date_str)

        # First, remove any existing overrides for this specific date for this owner to simplify logic
        BusinessAvailability.query.filter_by(
            business_owner_id=owner.id,
            specific_date=specific_date_obj
        ).delete(synchronize_session='fetch') # Using 'fetch' can be safer before adding new conflicting ones

        if override_type == 'blocked_override':
            # Create a single entry marking the whole day as blocked
            blocked_slot = BusinessAvailability(
                business_owner_id=owner.id,
                specific_date=specific_date_obj,
                start_time=dt_time(0, 0), # Represents start of the day
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
                slot_type = form_data.get(f"{slot_prefix}[slot_type]", 'available')

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
                    slot_type=slot_type, # Could be 'available' or 'break' within custom hours
                    day_of_week=None
                )
                db.session.add(new_override_slot)
                has_valid_slots = True
                slot_idx += 1
            
            if not has_valid_slots: # No slots submitted for "available" type
                 db.session.rollback()
                 return jsonify({'success': False, 'message': 'For "Set Custom Hours", at least one time slot is required.'}), 400


        db.session.commit()
        overrides_html = _render_overrides_list_html(owner.id)
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


@business_bp.route('/dashboard/availability/delete/<int:availability_id>', methods=['DELETE', 'POST']) # Allow POST for simpler forms if needed
@business_owner_required
def delete_availability_slot(availability_id):
    owner = get_current_business_owner()
    slot = BusinessAvailability.query.filter_by(id=availability_id, business_owner_id=owner.id).first_or_404()

    try:
        is_date_override = slot.specific_date is not None
        db.session.delete(slot)
        db.session.commit()

        if is_date_override:
            overrides_html = _render_overrides_list_html(owner.id)
            return jsonify({'success': True, 'message': 'Availability slot deleted.', 'overrides_html': overrides_html})
        else: # It was a weekly slot
             # For weekly slots, the frontend might need a more complex update or a page reload.
             # A simple success message is fine, but the UI might not reflect the change immediately without JS handling.
             flash('Weekly availability slot deleted. The page may need to be refreshed to see all changes to the weekly schedule.', 'success')
             return jsonify({'success': True, 'message': 'Weekly availability slot deleted.'})


    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting availability slot {availability_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to delete slot.'}), 500