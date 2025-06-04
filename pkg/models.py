from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time as dt_time, date as dt_date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import CheckConstraint, UniqueConstraint # Added for BusinessAvailability

db = SQLAlchemy()


class BusinessOwner(db.Model):
    __tablename__ = 'business_owners'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    business_name = db.Column(db.String(150), nullable=False)
    business_type = db.Column(db.String(100), nullable=False) # e.g., Nail Tech, Barber
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

    def __repr__(self):
        return f'<BusinessOwner {self.username} - {self.business_name}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self): # Example, adjust as needed
        return {
            'id': self.id,
            'full_name': self.full_name,
            'business_name': self.business_name,
            'business_type': self.business_type,
            'email': self.email,
            'phone_number': self.phone_number,
            'country': self.country,
            'state': self.state,
            'lga_province': self.lga_province,
            'full_address': self.full_address,
            'username': self.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
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

    def __repr__(self):
        return f'<Client {self.full_name} ({self.email})>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self): # Example, adjust as needed
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'gender': self.gender,
            'country': self.country,
            'state': self.state,
            'lga_area': self.lga_area,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
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
            'signed_up_at': self.signed_up_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# --- NEW MODELS FOR BOOKING SYSTEM ---

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

    business_owner = db.relationship('BusinessOwner', backref=db.backref('services', lazy=True))

    def __repr__(self):
        return f'<Service {self.name} (Owner ID: {self.business_owner_id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'business_owner_id': self.business_owner_id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'price': str(self.price), # Convert Decimal to string for JSON
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
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
    service = db.relationship('Service', backref=db.backref('all_bookings', lazy=True))

    @hybrid_property
    def client_display_name(self):
        if self.guest_full_name:
            return self.guest_full_name
        if self.client:
            return self.client.full_name
        return "Guest"

    def __repr__(self):
        return f'<Booking ID {self.id} for {self.client_display_name} at {self.start_datetime.strftime("%Y-%m-%d %H:%M")}>'

    def to_dict(self, include_service=False, include_client_details=False):
        data = {
            'id': self.id,
            'business_owner_id': self.business_owner_id,
            'client_id': self.client_id,
            'service_id': self.service_id,
            'start_datetime': self.start_datetime.isoformat(),
            'end_datetime': self.end_datetime.isoformat(),
            'guest_full_name': self.guest_full_name,
            'guest_email': self.guest_email,
            'guest_phone_number': self.guest_phone_number,
            'status': self.status,
            'notes_owner': self.notes_owner,
            'notes_client': self.notes_client,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
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
        CheckConstraint('start_time < end_time', name='chk_start_before_end_time'),
        UniqueConstraint('business_owner_id', 'day_of_week', 'start_time', 'specific_date', name='uq_availability_slot'),
    )

    def __repr__(self):
        if self.specific_date:
            return (f'<Availability Override Owner ID {self.business_owner_id} on {self.specific_date.strftime("%Y-%m-%d")} '
                    f'{self.start_time.strftime("%H:%M")}-{self.end_time.strftime("%H:%M")} ({self.slot_type})>')
        else:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            return (f'<Recurring Availability Owner ID {self.business_owner_id} on {days[self.day_of_week]} '
                    f'{self.start_time.strftime("%H:%M")}-{self.end_time.strftime("%H:%M")} ({self.slot_type})>')

    def to_dict(self):
        return {
            'id': self.id,
            'business_owner_id': self.business_owner_id,
            'day_of_week': self.day_of_week,
            'specific_date': self.specific_date.isoformat() if self.specific_date else None,
            'start_time': self.start_time.strftime('%H:%M'), # Ensure HH:MM format
            'end_time': self.end_time.strftime('%H:%M'),   # Ensure HH:MM format
            'slot_type': self.slot_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }