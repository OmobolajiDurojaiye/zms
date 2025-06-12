from flask import render_template, session, jsonify
from . import business_bp
from pkg.routes.main.auth import business_owner_required
from pkg.models import db, Client, Booking, Message
from flask_socketio import join_room
from sqlalchemy import func, case, and_
from sqlalchemy.orm import aliased
from datetime import datetime, date

try:
    from pkg import socketio
except ImportError:
    print("WARNING: Real-time messaging disabled. `flask_socketio` not found or `socketio` object not available.")
    class MockSocketIO:
        def on(self, *args, **kwargs): return lambda f: f
        def emit(self, *args, **kwargs): pass
    socketio = MockSocketIO()


@business_bp.route('/dashboard/customers')
@business_owner_required
def customers():
    owner_id = session.get('user_id')

    # Subquery to find the timestamp of the last message for each client conversation
    last_message_subquery = db.session.query(
        Message.client_id,
        func.max(Message.timestamp).label('last_message_time')
    ).filter(Message.business_owner_id == owner_id)\
     .group_by(Message.client_id)\
     .subquery()

    # Alias for the Message table to join for the last message content
    LastMessage = aliased(Message)

    # Main query to get clients, their last message, and unread count
    customers_data = db.session.query(
        Client,
        LastMessage,
        func.sum(case((and_(Message.is_read == False, Message.sender_role == 'client'), 1), else_=0)).label('unread_count')
    ).join(Booking, Client.id == Booking.client_id)\
     .outerjoin(Message, and_(Client.id == Message.client_id, Message.business_owner_id == owner_id))\
     .outerjoin(last_message_subquery, Client.id == last_message_subquery.c.client_id)\
     .outerjoin(LastMessage, and_(
         LastMessage.client_id == last_message_subquery.c.client_id,
         LastMessage.timestamp == last_message_subquery.c.last_message_time,
         LastMessage.business_owner_id == owner_id
     ))\
     .filter(Booking.business_owner_id == owner_id)\
     .group_by(Client, LastMessage)\
     .order_by(
        # Sort by whether the timestamp IS NULL first (pushes NULLs to the bottom)
        func.isnull(last_message_subquery.c.last_message_time),
        # Then sort by the timestamp in descending order
        last_message_subquery.c.last_message_time.desc(),
        # Finally, sort by name as a tie-breaker
        Client.full_name
     )\
     .all()

    # Pass today's date to the template context for comparison
    today = date.today()

    return render_template(
        'business/customers.html', 
        customers=customers_data, 
        page_title="Customer Management",
        today=today
    )

@business_bp.route('/api/customers/<int:client_id>/messages')
@business_owner_required
def get_messages(client_id):
    owner_id = session.get('user_id')

    has_booking = db.session.query(Booking.id).filter_by(
        business_owner_id=owner_id, 
        client_id=client_id
    ).first()

    if not has_booking:
        return jsonify({"error": "Unauthorized access to customer messages."}), 403

    messages = Message.query.filter_by(
        business_owner_id=owner_id,
        client_id=client_id
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark messages as read when fetched by the owner
    Message.query.filter(
        Message.business_owner_id == owner_id,
        Message.client_id == client_id,
        Message.sender_role == 'client',
        Message.is_read == False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify([msg.to_dict() for msg in messages])

@business_bp.route('/api/customers/<int:client_id>/details')
@business_owner_required
def get_customer_details(client_id):
    owner_id = session.get('user_id')

    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    # Security check: Ensure owner has a relationship with this client
    has_booking = db.session.query(Booking.id).filter_by(
        business_owner_id=owner_id, 
        client_id=client_id
    ).first()
    if not has_booking:
        return jsonify({"error": "Unauthorized"}), 403

    # Fetch relevant details
    total_bookings = Booking.query.filter_by(client_id=client_id, business_owner_id=owner_id).count()
    last_booking = Booking.query.filter_by(client_id=client_id, business_owner_id=owner_id)\
        .order_by(Booking.start_datetime.desc()).first()
    
    client_data = client.to_dict()
    client_data['stats'] = {
        'total_bookings': total_bookings,
        'member_since': client.created_at.strftime('%B %d, %Y'),
        'last_booking_date': last_booking.start_datetime.strftime('%B %d, %Y') if last_booking else 'N/A'
    }

    return jsonify(client_data)


### SOCKET.IO EVENT HANDLERS (CENTRALIZED) ###

@socketio.on('join_chat', namespace='/business')
def handle_join_chat_event(data):
    """Handles user (owner or client) joining a chat room."""
    user_id = session.get('user_id')
    user_type = session.get('user_type')

    if not user_id or not user_type:
        return

    if user_type == 'business_owner':
        owner_id = user_id
        client_id = data.get('client_id')
    elif user_type == 'client':
        client_id = user_id
        owner_id = data.get('business_owner_id')
    else:
        return # Invalid user type

    if not client_id or not owner_id:
        return # Missing participant ID
        
    # The room name is the unique identifier for the conversation
    room = f"chat_owner{owner_id}_client{client_id}"
    join_room(room)


@socketio.on('send_message', namespace='/business')
def handle_send_message_event(data):
    """Handles a message sent by either a business owner or a client."""
    user_id = session.get('user_id')
    user_type = session.get('user_type')
    content = data.get('content')

    if not all([user_id, user_type, content]):
        return # Invalid session or empty message

    if user_type == 'business_owner':
        owner_id = user_id
        client_id = data.get('client_id')
        sender_role = 'owner'
    elif user_type == 'client':
        client_id = user_id
        owner_id = data.get('business_owner_id')
        sender_role = 'client'
    else:
        return # Unknown user type

    if not client_id or not owner_id:
        return # Missing participant ID in data payload

    # Security check: A booking relationship must exist to allow messaging
    has_booking = db.session.query(Booking.id).filter_by(
        business_owner_id=owner_id, 
        client_id=client_id
    ).first()
    if not has_booking:
        return # No relationship, silently drop message

    new_message = Message(
        business_owner_id=int(owner_id),
        client_id=int(client_id),
        sender_role=sender_role,
        content=content.strip()
    )
    db.session.add(new_message)
    db.session.commit()

    room = f"chat_owner{owner_id}_client{client_id}"
    # Broadcast to all members of the room (the client and the owner)
    socketio.emit('message_received', new_message.to_dict(), room=room, namespace='/business')