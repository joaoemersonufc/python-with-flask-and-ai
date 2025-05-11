"""
Routes for authentication.
"""
import logging
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import db, User
from forms import LoginForm, RegistrationForm

logger = logging.getLogger(__name__)

# Create a blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find the user by username
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check if user exists and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
            
        # Log the user in
        login_user(user, remember=form.remember_me.data)
        logger.info(f"User {user.username} logged in")
        
        # Redirect to the page the user was trying to access
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('chat.index')
            
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('chat.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create a new user
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        
        # Add to database
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.username}")
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='Register', form=form)