"""
Main blueprint for handling core web routes.

This module defines views for:
- Home/landing page
- Login
- Registration 
- About
- Error pages
"""
from flask import (
    Blueprint, flash, g, redirect, render_template, 
    request, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from app.database.db import get_db
from app.database.models import User
from app.routes import login_required
from app.factory import AppContextManager

# Create blueprint
main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    """Render the landing page."""
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@main_bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register a new user."""
    # If user is already logged in, redirect to dashboard
    if g is not None and hasattr(g, 'user') and g.user is not None:
        return redirect(url_for('dashboard_bp.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        error = None
        
        # Validate input
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
            
        # Check if username or email already exists
        if error is None:
            db = get_db()
            existing_user = db.execute(
                'SELECT id FROM users WHERE username = ? OR email = ?',
                (username, email)
            ).fetchone()
            
            if existing_user:
                error = 'Username or email already registered.'
        
        # Create new user
        if error is None:
            try:
                db = get_db()
                db.execute(
                    'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, generate_password_hash(password))
                )
                db.commit()
                
                # Redirect to login page after successful registration
                flash('Registration successful! Please log in.')
                return redirect(url_for('main_bp.login'))
            except Exception as e:
                error = str(e)
        
        # If there was an error, flash it and re-render the registration page
        flash(error)
    
    return render_template('register.html')

# ... existing imports ...

@main_bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in a user."""
    # If user is already logged in, redirect to dashboard
    if g is not None and hasattr(g, 'user') and g.user is not None:
        return redirect(url_for('dashboard_bp.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        error = None
        
        # Get database connection
        db = get_db()
        
        try:
            # Try to find the user
            user = db.execute(
                'SELECT * FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            
            if user is None:
                error = 'Invalid username or password.'
            elif not check_password_hash(user['password_hash'], password):
                error = 'Invalid username or password.'
            
            if error is None:
                # Store user_id in session
                session.clear()
                session['user_id'] = user['id']
                
                # Set g.user for the current request
                g.user = user
                
                # Update last login time
                try:
                    db.execute(
                        'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                        (user['id'],)
                    )
                    db.commit()
                    print(f"User {username} (ID: {user['id']}) logged in successfully")
                except Exception as e:
                    print(f"Error updating last login: {str(e)}")
                
                # Redirect to dashboard
                return redirect(url_for('dashboard_bp.dashboard'))
        
        except Exception as e:
            print(f"Error during login: {str(e)}")
            error = "An error occurred during login. Please try again."
        
        flash(error)
    
    return render_template('login.html')

# Make sure this function runs before each request to populate g.user
@main_bp.before_app_request
def load_logged_in_user():
    """Load the logged-in user for each request."""
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        try:
            db = get_db()
            g.user = db.execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone()
            
            # If user doesn't exist in database, clear session
            if g.user is None:
                session.clear()
        except Exception as e:
            print(f"Error loading user: {str(e)}")
            g.user = None

@main_bp.route('/logout')
def logout():
    """Log out a user."""
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('main_bp.index'))

@main_bp.route('/emotion_recognition')
@login_required
def emotion_recognition():
    """Render the emotion recognition page."""
    return render_template('emotion_recognition.html')