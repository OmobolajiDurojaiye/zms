from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time as dt_time, date as dt_date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import CheckConstraint, UniqueConstraint, Index

db = SQLAlchemy()


class BusinessOwner(db.Model):
    __tablename__ = 'business_owners'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    business_name = db.Column(db.String(150), nullable=False)
    # MODIFIED: Changed from String to JSON to support multiple business types
    business_type = db.Column(db.JSON, nullable=True) # e.g., ["Nail Tech", "Barber"]
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(30), nullable=False) # Consider E.164 format

    # Location fields
    country = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    lga_province = db.Column(db.String(100), nullable=True) # LGA or Province
    full_address = db.Column(db.Text, nullable=False) # Street/Area

    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships are implicitly defined by backrefs from Service, Booking, BusinessAvailability, Message

    def __repr__(self):
        return f'<BusinessOwner {self.username} - {self.business_name}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'business_name': self.business_name,
            'business_type': self.business_type, # Will be a list or null
            'email': self.email,
            'phone_number': self.phone_number,
            'country': self.country,
            'state': self.state,
            'lga_province': self.lga_province,
            'full_address': self.full_address,
            'username': self.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(30), nullable=False)
    gender = db.Column(db.String(20), nullable=True) # Male, Female, Other, Prefer not to say

    # Location fields
    country = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    lga_area = db.Column(db.String(100), nullable=True) # Province / LGA / Area

    password_hash = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships defined in Booking and Message models via backref

    def __repr__(self):
        return f'<Client {self.full_name} ({self.email})>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'gender': self.gender,
            'country': self.country,
            'state': self.state,
            'lga_area': self.lga_area,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    business_owner_id = db.Column(db.Integer, db.ForeignKey('business_owners.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Who sent this specific message: 'owner' or 'client'
    sender_role = db.Column(db.String(20), nullable=False) 
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    business_owner = db.relationship('BusinessOwner', backref=db.backref('messages', lazy='dynamic', cascade="all, delete-orphan"))
    client = db.relationship('Client', backref=db.backref('messages', lazy='dynamic', cascade="all, delete-orphan"))

    # An index on the conversation pair for faster lookups
    __table_args__ = (Index('idx_conversation', 'business_owner_id', 'client_id'),)

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_role}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'business_owner_id': self.business_owner_id,
            'client_id': self.client_id,
            'sender_role': self.sender_role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read
        }


class Waitlist(db.Model):
    __tablename__ = 'waitlist_signups'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=True)
    user_type = db.Column(db.String(50), nullable=True) # e.g., "business_owner", "client"
    signed_up_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Waitlist {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'user_type': self.user_type,
            'signed_up_at': self.signed_up_at.strftime('%Y-%m-%d %H:%M:%S') if self.signed_up_at else None
        }

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    business_owner_id = db.Column(db.Integer, db.ForeignKey('business_owners.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False) # e.g., 30, 60, 90
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business_owner = db.relationship('BusinessOwner', backref=db.backref('services', lazy='select'))
    # Relationship 'all_bookings' is defined in Booking model via backref

    def __repr__(self):
        return f'<Service {self.name} (Owner ID: {self.business_owner_id})>'

    def to_dict(self): # General purpose to_dict
        return {
            'id': self.id,
            'business_owner_id': self.business_owner_id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'price': str(self.price) if self.price is not None else None,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def to_dict_for_client_view(self):
        business = self.business_owner
        business_details = {
            'id': getattr(business, 'id', None),
            'name': getattr(business, 'business_name', 'N/A'),
            'type': getattr(business, 'business_type', 'N/A'),
            'country': getattr(business, 'country', 'N/A'),
            'state': getattr(business, 'state', 'N/A'),
            'lga_province': getattr(business, 'lga_province', 'N/A'),
            'full_address': getattr(business, 'full_address', 'N/A')
        } if business else { # Fallback if business somehow is None
            'id': None, 'name': 'N/A', 'type': 'N/A',
            'country': 'N/A', 'state': 'N/A', 'lga_province': 'N/A',
            'full_address': 'N/A'
        }
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'price': str(self.price) if self.price is not None else None,
            'is_active': self.is_active,
            'business': business_details,
            # Placeholders - these would typically come from aggregated data or other models
            'avg_rating': 4.5, # Placeholder
            'rating_count': 120, # Placeholder
            'image_url': None, # Placeholder - you might add an image field or derive one
        }

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    business_owner_id = db.Column(db.Integer, db.ForeignKey('business_owners.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)

    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)

    guest_full_name = db.Column(db.String(150), nullable=True)
    guest_email = db.Column(db.String(120), nullable=True)
    guest_phone_number = db.Column(db.String(30), nullable=True)

    status = db.Column(db.String(50), nullable=False, default='confirmed')
    # Options: 'pending_confirmation', 'confirmed', 'cancelled_by_owner',
    #          'cancelled_by_client', 'completed', 'no_show'

    notes_owner = db.Column(db.Text, nullable=True)
    notes_client = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business_owner = db.relationship('BusinessOwner', backref=db.backref('all_bookings', lazy='dynamic'))
    client = db.relationship('Client', backref=db.backref('all_bookings', lazy='dynamic'))
    service = db.relationship('Service', backref=db.backref('all_bookings', lazy='select')) # Changed to select for easier access in to_dict

    @hybrid_property
    def client_display_name(self):
        if self.guest_full_name:
            return self.guest_full_name
        if self.client:
            return self.client.full_name
        return "Guest"

    def __repr__(self):
        start_time_str = "Invalid time"
        if isinstance(self.start_datetime, datetime):
            start_time_str = self.start_datetime.strftime("%Y-%m-%d %H:%M")
        return f'<Booking ID {self.id} for {self.client_display_name} at {start_time_str}>'

    def to_dict(self, include_service=False, include_client_details=False, include_business_owner=False):
        data = {
            'id': self.id,
            'business_owner_id': self.business_owner_id,
            'client_id': self.client_id,
            'service_id': self.service_id,
            'start_datetime': self.start_datetime.isoformat() if isinstance(self.start_datetime, datetime) else None,
            'end_datetime': self.end_datetime.isoformat() if isinstance(self.end_datetime, datetime) else None,
            'guest_full_name': self.guest_full_name,
            'guest_email': self.guest_email,
            'guest_phone_number': self.guest_phone_number,
            'status': self.status,
            'notes_owner': self.notes_owner,
            'notes_client': self.notes_client,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else None,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None,
            'client_display_name': self.client_display_name
        }
        if include_service and self.service:
            data['service'] = self.service.to_dict()
        if include_client_details and self.client:
            data['client_details'] = {
                'id': self.client.id,
                'full_name': self.client.full_name,
                'email': self.client.email
            }
        if include_business_owner and self.business_owner:
            data['business_owner'] = self.business_owner.to_dict()
        return data

class BusinessAvailability(db.Model):
    __tablename__ = 'business_availability'
    id = db.Column(db.Integer, primary_key=True)
    business_owner_id = db.Column(db.Integer, db.ForeignKey('business_owners.id'), nullable=False)

    # For recurring weekly availability: 0 = Monday, ..., 6 = Sunday
    day_of_week = db.Column(db.Integer, nullable=True)
    # For specific date availability or override
    specific_date = db.Column(db.Date, nullable=True)

    start_time = db.Column(db.Time, nullable=False) # e.g., 09:00:00
    end_time = db.Column(db.Time, nullable=False)   # e.g., 17:00:00

    # Type of slot: 'available', 'break', 'blocked_override'
    slot_type = db.Column(db.String(50), default='available', nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business_owner = db.relationship('BusinessOwner', backref=db.backref('availability_slots', lazy='dynamic'))

    __table_args__ = (
        CheckConstraint(
            '(day_of_week IS NOT NULL AND specific_date IS NULL) OR '
            '(day_of_week IS NULL AND specific_date IS NOT NULL)',
            name='chk_availability_type_defined_exclusive'
        ),
        CheckConstraint('start_time < end_time', name='chk_start_before_end_time')
    )

    def __repr__(self):
        start_str = self.start_time.strftime("%H:%M") if isinstance(self.start_time, dt_time) else "Invalid Time"
        end_str = self.end_time.strftime("%H:%M") if isinstance(self.end_time, dt_time) else "Invalid Time"

        if self.specific_date:
            date_str = self.specific_date.strftime("%Y-%m-%d") if isinstance(self.specific_date, dt_date) else "Invalid Date"
            return (f'<Availability Override Owner ID {self.business_owner_id} on {date_str} '
                    f'{start_str}-{end_str} ({self.slot_type})>')
        else:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_str = "Invalid Day"
            if self.day_of_week is not None and 0 <= self.day_of_week < 7:
                day_str = days[self.day_of_week]
            return (f'<Recurring Availability Owner ID {self.business_owner_id} on {day_str} '
                    f'{start_str}-{end_str} ({self.slot_type})>')

    def to_dict(self):
        return {
            'id': self.id,
            'business_owner_id': self.business_owner_id,
            'day_of_week': self.day_of_week,
            'specific_date': self.specific_date.isoformat() if isinstance(self.specific_date, dt_date) else None,
            'start_time': self.start_time.strftime('%H:%M') if isinstance(self.start_time, dt_time) else None,
            'end_time': self.end_time.strftime('%H:%M') if isinstance(self.end_time, dt_time) else None,
            'slot_type': self.slot_type,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else None,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None
        }