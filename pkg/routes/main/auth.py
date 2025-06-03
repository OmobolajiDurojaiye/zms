from flask import render_template, request, redirect, url_for, flash, session
from functools import wraps
from . import main_bp
from pkg.models import db, BusinessOwner, Client

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'user_type' not in session:
            flash('You need to be logged in to access this page.', 'warning')
            # Redirect to the main auth page, passing the intended destination
            return redirect(url_for('main.auth_page_get', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Page Rendering ---
@main_bp.route('/auth', methods=['GET'])
def auth_page_get():
    return render_template('main/auth.html')


# --- Business Owner Authentication ---
@main_bp.route('/auth/bo/signup', methods=['POST'])
def bo_signup_post():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        business_name = request.form.get('business_name')
        business_type = request.form.get('business_type')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        country = request.form.get('country')
        state = request.form.get('state')
        lga_province = request.form.get('lga_province')
        full_address = request.form.get('full_address')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([full_name, business_name, business_type, email, phone_number, country, state, full_address, username, password, confirm_password]):
            flash('All fields are required.', 'error') # Simplified message
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='signup'))

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='signup'))

        existing_user_email = BusinessOwner.query.filter_by(email=email).first()
        if existing_user_email:
            flash('Email address already registered.', 'error')
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='signup'))
        
        existing_user_username = BusinessOwner.query.filter_by(username=username).first()
        if existing_user_username:
            flash('Username already taken.', 'error')
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='signup'))

        new_bo = BusinessOwner(
            full_name=full_name, business_name=business_name, business_type=business_type,
            email=email, phone_number=phone_number, country=country, state=state,
            lga_province=lga_province, full_address=full_address, username=username
        )
        new_bo.set_password(password)

        try:
            db.session.add(new_bo)
            db.session.commit()
            flash('Business Owner account created successfully! Please login.', 'success')
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during signup: {str(e)}', 'error')
            print(f"Error BO signup: {e}")
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='signup'))

    return redirect(url_for('main.auth_page_get'))

@main_bp.route('/auth/bo/login', methods=['POST'])
def bo_login_post():
    if request.method == 'POST':
        email = request.form.get('email') 
        password = request.form.get('password')
        next_url = request.form.get('next') # Get 'next' from hidden form field

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='login', next=next_url or ''))

        user = BusinessOwner.query.filter_by(email=email).first()
        # Optionally, allow login with username:
        # user = BusinessOwner.query.filter((BusinessOwner.email == email) | (BusinessOwner.username == email)).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_type'] = 'business_owner'
            session.permanent = True # Make session persistent (requires app.permanent_session_lifetime configuration)
            flash('Login successful!', 'success')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('main.zms_index')) # Placeholder redirect to a dashboard
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('main.auth_page_get', tab='businessOwnerTab', form='login', next=next_url or ''))
            
    return redirect(url_for('main.auth_page_get'))

# --- Client Authentication ---
@main_bp.route('/auth/client/signup', methods=['POST'])
def client_signup_post():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        gender = request.form.get('gender')
        country = request.form.get('country')
        state = request.form.get('state')
        lga_area = request.form.get('lga_area')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([full_name, email, phone_number, country, state, lga_area, password, confirm_password]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='signup'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='signup'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='signup'))

        existing_client = Client.query.filter_by(email=email).first()
        if existing_client:
            flash('Email address already registered.', 'error')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='signup'))

        new_client = Client(
            full_name=full_name, email=email, phone_number=phone_number,
            gender=gender if gender else None, country=country, state=state,
            lga_area=lga_area if lga_area else None
        )
        new_client.set_password(password)

        try:
            db.session.add(new_client)
            db.session.commit()
            flash('Client account created successfully! Please login.', 'success')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during signup: {str(e)}', 'error')
            print(f"Error Client signup: {e}")
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='signup'))

    return redirect(url_for('main.auth_page_get'))

@main_bp.route('/auth/client/login', methods=['POST'])
def client_login_post():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        next_url = request.form.get('next') # Get 'next' from hidden form field


        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='login', next=next_url or ''))

        client = Client.query.filter_by(email=email).first()

        if client and client.check_password(password):
            session['user_id'] = client.id
            session['user_type'] = 'client'
            session.permanent = True
            flash('Login successful!', 'success')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('main.zms_index')) # Placeholder redirect
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('main.auth_page_get', tab='clientTab', form='login', next=next_url or ''))
            
    return redirect(url_for('main.auth_page_get'))


@main_bp.route('/logout')
@login_required # Apply the custom login_required decorator
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    # session.clear() # Alternatively, clear the whole session
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.zms_index'))