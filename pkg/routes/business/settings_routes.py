from flask import render_template, session, redirect, url_for, flash, request
from . import business_bp
from pkg.models import db, BusinessOwner, Service
from pkg.routes.main.auth import business_owner_required
from decimal import Decimal, InvalidOperation

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
        # MODIFIED: Use getlist to handle multiple selections for business_type
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
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        duration_minutes = int(request.form.get('duration_minutes'))
        price = Decimal(request.form.get('price'))

        if not all([name, duration_minutes, price]):
            flash('Service Name, Duration, and Price are required.', 'error')
            return redirect(url_for('business.settings', _anchor='services-section'))

        new_service = Service(
            business_owner_id=owner_id,
            name=name,
            description=description,
            duration_minutes=duration_minutes,
            price=price
        )
        db.session.add(new_service)
        db.session.commit()
        flash(f'Service "{name}" added successfully!', 'success')

    except (ValueError, TypeError):
        flash('Invalid input. Please ensure duration and price are numbers.', 'error')
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
        service.duration_minutes = int(request.form.get('duration_minutes'))
        service.price = Decimal(request.form.get('price'))
        service.is_active = 'is_active' in request.form

        if not all([service.name, service.duration_minutes, service.price]):
             flash('Service Name, Duration, and Price are required.', 'error')
             return redirect(url_for('business.settings', _anchor='services-section'))

        db.session.commit()
        flash(f'Service "{service.name}" updated successfully!', 'success')

    except (ValueError, TypeError):
        flash('Invalid input. Please ensure duration and price are numbers.', 'error')
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
        db.session.delete(service)
        db.session.commit()
        flash(f'Service "{service_name}" has been deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting service: {e}', 'error')

    return redirect(url_for('business.settings', _anchor='services-section'))