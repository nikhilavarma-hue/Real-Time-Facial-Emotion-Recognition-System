"""
Main application routes for the facial emotion recognition app.

This module defines the base routes and the application entry points.
"""
import os
from flask import redirect, url_for, current_app, render_template, session, g
from functools import wraps
from app.database.db import get_db
from app.database.models import User  # SQLAlchemy model

def login_required(f):
    """Decorator to require login for web routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

def load_logged_in_user():
    """Load user data if logged in."""
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        try:
            # Try SQLAlchemy query first
            try:
                g.user = User.query.get(user_id)
            except Exception as e:
                # Fall back to direct database query
                db = get_db()
                g.user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                
            # If user not found, clear session
            if g.user is None:
                session.clear()
        except Exception as e:
            print(f"Error loading user: {e}")
            g.user = None
            session.clear()

def register_routes(app):
    """Register base application routes."""
    
    # Register before_request handler
    @app.before_request
    def before_request():
        load_logged_in_user()
    
    # Register error handlers
    register_error_handlers(app)

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error=e, title='Page Not Found'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error=e, title='Internal Server Error'), 500