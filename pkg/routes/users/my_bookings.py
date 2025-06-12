from . import users_bp
from flask import render_template, session, request, jsonify
from .routes import client_required
from pkg.models import db, BusinessOwner, Booking, Message
from sqlalchemy import func, desc
from datetime import datetime

# Main page route for "My Bookings"
@users_bp.route('/my-bookings')
@client_required
def my_bookings(current_client):
    bookings_query = Booking.query.options(
        db.joinedload(Booking.service),
        db.joinedload(Booking.business_owner)
    ).filter(
        Booking.client_id == current_client.id
    ).order_by(desc(Booking.start_datetime)).all()

    # Get unread message counts from each business owner
    unread_counts = db.session.query(
        Message.business_owner_id,
        func.count(Message.id).label('unread')
    ).filter(
        Message.client_id == current_client.id,
        Message.sender_role == 'owner',
        Message.is_read == False
    ).group_by(Message.business_owner_id).all()
    
    unread_map = {owner_id: count for owner_id, count in unread_counts}

    now = datetime.utcnow()
    upcoming, past, cancelled = [], [], []

    for booking in bookings_query:
        # Attach unread count to booking object for easy access in template
        booking.unread_messages = unread_map.get(booking.business_owner_id, 0)
        
        if booking.status.startswith('cancelled'):
            cancelled.append(booking)
        elif booking.start_datetime > now:
            upcoming.append(booking)
        else:
            past.append(booking)

    return render_template(
        'users/my_bookings.html',
        current_user=current_client,
        upcoming_bookings=upcoming,
        past_bookings=past,
        cancelled_bookings=cancelled,
    )

# API to get messages for a conversation
@users_bp.route('/api/conversations/<int:business_owner_id>/messages')
@client_required
def get_client_messages(current_client, business_owner_id):
    # Security check: ensure the client has a booking with this business
    if not Booking.query.filter_by(client_id=current_client.id, business_owner_id=business_owner_id).first():
        return jsonify({"error": "Unauthorized access to messages."}), 403

    messages = Message.query.filter_by(
        business_owner_id=business_owner_id, 
        client_id=current_client.id
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark incoming messages as read when the client opens the chat
    Message.query.filter(
        Message.business_owner_id == business_owner_id, 
        Message.client_id == current_client.id,
        Message.sender_role == 'owner', 
        Message.is_read == False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify([msg.to_dict() for msg in messages])


# API to get business details for the modal
@users_bp.route('/api/business/<int:business_owner_id>/details')
@client_required
def get_business_details(current_client, business_owner_id):
    owner = BusinessOwner.query.get_or_404(business_owner_id)
    # The client has a booking, so it's okay to return contact details.
    return jsonify(owner.to_dict())


# API for a client to cancel their own booking
@users_bp.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
@client_required
def cancel_client_booking(current_client, booking_id):
    booking = Booking.query.filter_by(id=booking_id, client_id=current_client.id).first_or_404()

    if booking.status.startswith('cancelled'):
        return jsonify({'success': False, 'message': 'This booking is already cancelled.'}), 400
    
    # Optional: You could add logic here to prevent cancellation too close to the appointment time
    # e.g., if booking.start_datetime < datetime.utcnow() + timedelta(hours=24): ...

    booking.status = 'cancelled_by_client'
    booking.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Your booking has been cancelled.'})