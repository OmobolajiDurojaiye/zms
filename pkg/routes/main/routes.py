from flask import render_template, request, redirect, url_for, flash
from . import main_bp # Corrected: main_bp is defined in pkg/main/__init__.py
from pkg.models import db, Waitlist 

@main_bp.route('/')
def zms_index():
    return render_template('main/home.html')

@main_bp.route('/join-waitlist', methods=['POST'])
def join_waitlist():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        user_type = request.form.get('user_type')

        if not email:
            flash('Email is required to join the waitlist.', 'error')
            return redirect(url_for('main.zms_index', _anchor='waitlist'))

        existing_signup = Waitlist.query.filter_by(email=email).first()
        if existing_signup:
            flash('This email is already on our waitlist!', 'info')
            return redirect(url_for('main.zms_index', _anchor='waitlist'))

        try:
            new_signup = Waitlist(
                email=email,
                name=name,
                user_type=user_type
            )
            db.session.add(new_signup)
            db.session.commit()
            flash('Thank you for joining our waitlist! We\'ll keep you updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            # Log the error e for debugging
            print(f"Error adding to waitlist: {e}")


        return redirect(url_for('main.zms_index', _anchor='waitlist'))
    
    # Should not be reached via GET if form is set up correctly
    return redirect(url_for('main.zms_index'))