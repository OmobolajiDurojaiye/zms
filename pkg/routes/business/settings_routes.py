from flask import render_template, session, redirect, url_for, flash, request, current_app
from . import business_bp
from pkg.models import db, BusinessOwner, Service
from pkg.routes.main.auth import business_owner_required
from decimal import Decimal, InvalidOperation
import os
import secrets
from werkzeug.utils import secure_filename

# A categorized list of business types for use in forms
BUSINESS_CATEGORIES = {
    "Beauty & Personal Care": [
        "Hairdresser", "Barber", "Nail Technician", "Makeup Artist", "Spa & Massage Therapist",
        "Skincare Specialist", "Eyelash Technician", "Pedicure/Manicure Specialist", "Personal Trainer / Fitness Coach"
    ],
    "Fashion & Clothing": [
        "Tailor / Fashion Designer", "Aso-Ebi Vendor", "Shoe/Bag Repair", "Bead Maker", "Thrift/Okirika Seller", "Cap/Hat Designer"
    ],
    "Food & Drinks": [
        "Home Cook / Chef", "Caterer", "Small Chops Vendor", "Grill Master (Suya, Asun)", "Zobo / Smoothie / Juice Seller",
        "Palm Wine Tapper/Distributor", "Baker (Cake, Pastries)", "Food Tray / Platter Services"
    ],
    "Home & Cleaning Services": [
        "House Cleaner", "Car Wash Operator", "Laundry/Ironing Services", "Pest Control", "Plumber", "Electrician",
        "AC Repair Technician", "Painter"
    ],
    "Media & Creative": [
        "Photographer", "Videographer", "Graphic Designer", "Social Media Manager", "Content Creator / Influencer",
        "MC / Event Host", "DJ", "Event Decorator / Balloon Artist"
    ],
    "Professional Services": [
        "Freelance Writer / Copywriter", "Virtual Assistant", "Business Consultant", "Digital Marketer", "UI/UX Designer",
        "Web Developer", "Typist / Document Preparer", "CV/Resume Writer"
    ],
    "Logistics & Delivery": [
        "Bike Delivery Rider", "Errand Runner", "Dispatch Rider", "Personal Shopper"
    ],
    "Tech & Repair": [
        "Phone Repair Technician", "Laptop Repair Technician", "Solar Panel Installer", "Generator Repairer"
    ],
    "Event & Rentals": [
        "Event Planner", "Party Chair/Table Rental", "Tent/Canopy Rental", "Costume Rental", "Sound System Rental", "Makeup Chair Rental"
    ],
    "Education & Training": [
        "Home Tutor", "Language Tutor", "Lesson Teacher (WAEC/JAMB)", "Coding Tutor", "Music Instructor (e.g. Piano, Guitar)"
    ],
    "Pet & Miscellaneous": [
        "Pet Groomer", "Dog Walker", "Animal Breeder", "Mobile Market Vendor"
    ]
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _save_service_image(file, owner):
    """Saves a service image and returns the new filename."""
    if not file or file.filename == '' or not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    random_hex = secrets.token_hex(6) # Using 6 random chars
    owner_name_safe = "".join(c for c in owner.full_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_').lower()
    new_filename = f"{owner_name_safe}_{random_hex}.{filename.rsplit('.', 1)[1].lower()}"
    
    upload_path = os.path.join(current_app.root_path, 'static/uploads')
    os.makedirs(upload_path, exist_ok=True) # Ensure directory exists
    file.save(os.path.join(upload_path, new_filename))

    return new_filename

def _delete_service_image(filename):
    """Deletes an image file from the uploads folder."""
    if not filename:
        return
    try:
        file_path = os.path.join(current_app.root_path, 'static/uploads', filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Log this error but don't fail the request
        print(f"Error deleting image file {filename}: {e}")
        flash(f'Could not delete old image file: {filename}', 'warning')


@business_bp.route('/settings', methods=['GET'])
@business_owner_required
def settings():
    owner_id = session.get('user_id')
    current_business_owner = BusinessOwner.query.get(owner_id)
    services = Service.query.filter_by(business_owner_id=owner_id).order_by(Service.name).all()
    
    return render_template(
        'business/settings.html',
        current_business_owner=current_business_owner,
        services=services,
        business_categories=BUSINESS_CATEGORIES,
        page_title="Business Settings"
    )

@business_bp.route('/settings/business-info', methods=['POST'])
@business_owner_required
def update_business_info():
    owner_id = session.get('user_id')
    owner = BusinessOwner.query.get(owner_id)
    
    if owner:
        owner.business_name = request.form.get('business_name', owner.business_name)
        owner.business_type = request.form.getlist('business_type')
        owner.phone_number = request.form.get('phone_number', owner.phone_number)
        owner.full_address = request.form.get('full_address', owner.full_address)
        owner.state = request.form.get('state', owner.state)
        try:
            db.session.commit()
            flash('Business information updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'error')
    else:
        flash('Could not find your business profile.', 'error')
        
    return redirect(url_for('business.settings'))

@business_bp.route('/settings/services/add', methods=['POST'])
@business_owner_required
def add_service():
    owner_id = session.get('user_id')
    owner = BusinessOwner.query.get(owner_id)
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        price = Decimal(request.form.get('price'))

        duration_str = request.form.get('duration_minutes')
        duration_minutes = int(duration_str) if duration_str and duration_str.strip().isdigit() else None

        if not name or price is None:
            flash('Service Name and Price are required.', 'error')
            return redirect(url_for('business.settings', _anchor='services-section'))

        image_file = request.files.get('image')
        image_filename = _save_service_image(image_file, owner)

        new_service = Service(
            business_owner_id=owner_id,
            name=name,
            description=description,
            duration_minutes=duration_minutes,
            price=price,
            image_filename=image_filename
        )
        db.session.add(new_service)
        db.session.commit()
        flash(f'Service "{name}" added successfully!', 'success')

    except (ValueError, TypeError):
        flash('Invalid input. Please ensure price is a number.', 'error')
    except InvalidOperation:
         flash('Invalid price format. Please enter a valid number.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'error')
        
    return redirect(url_for('business.settings', _anchor='services-section'))


@business_bp.route('/settings/services/edit/<int:service_id>', methods=['POST'])
@business_owner_required
def edit_service(service_id):
    owner_id = session.get('user_id')
    service = Service.query.filter_by(id=service_id, business_owner_id=owner_id).first_or_404()
    
    try:
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.price = Decimal(request.form.get('price'))
        service.is_active = 'is_active' in request.form
        
        duration_str = request.form.get('duration_minutes')
        service.duration_minutes = int(duration_str) if duration_str and duration_str.strip().isdigit() else None
        
        if not all([service.name, service.price is not None]):
             flash('Service Name and Price are required.', 'error')
             return redirect(url_for('business.settings', _anchor='services-section'))

        image_file = request.files.get('image')
        if image_file:
            _delete_service_image(service.image_filename)
            service.image_filename = _save_service_image(image_file, service.business_owner)

        db.session.commit()
        flash(f'Service "{service.name}" updated successfully!', 'success')

    except (ValueError, TypeError):
        flash('Invalid input. Please ensure price is a number.', 'error')
    except InvalidOperation:
         flash('Invalid price format. Please enter a valid number.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'error')

    return redirect(url_for('business.settings', _anchor='services-section'))


@business_bp.route('/settings/services/delete/<int:service_id>', methods=['POST'])
@business_owner_required
def delete_service(service_id):
    owner_id = session.get('user_id')
    service = Service.query.filter_by(id=service_id, business_owner_id=owner_id).first_or_404()

    try:
        service_name = service.name
        image_to_delete = service.image_filename
        
        db.session.delete(service)
        db.session.commit()

        # Delete the associated image file after a successful db transaction
        _delete_service_image(image_to_delete)

        flash(f'Service "{service_name}" has been deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting service: {e}', 'error')

    return redirect(url_for('business.settings', _anchor='services-section'))