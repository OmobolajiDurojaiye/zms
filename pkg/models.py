from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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