"""
Settings blueprint for the facial emotion recognition application.

This blueprint handles user settings, preferences, and application configuration.
"""
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app, g
)
from app.database.db import get_db
from app.routes import login_required

# Create blueprint
settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/')
@login_required
def settings():
    """Render the settings page."""
    user_id = session.get('user_id')
    
    # Get user settings
    db = get_db()
    user_settings = db.execute(
        'SELECT * FROM settings WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    
    # If no settings exist, create default settings
    if not user_settings:
        db.execute(
            'INSERT INTO settings (user_id, theme, notification_enabled, privacy_mode, analysis_frequency) '
            'VALUES (?, ?, ?, ?, ?)',
            (user_id, 'light', True, False, 5)
        )
        db.commit()
        
        user_settings = db.execute(
            'SELECT * FROM settings WHERE user_id = ?',
            (user_id,)
        ).fetchone()
    
    # Get user information
    user = db.execute(
        'SELECT * FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    
    return render_template(
        'settings.html',
        settings=user_settings,
        user=user
    )

@settings_bp.route('/update', methods=['POST'])
@login_required
def update_settings():
    """Update user settings."""
    user_id = session.get('user_id')
    
    # Get form data
    theme = request.form.get('theme', 'light')
    notification_enabled = 'notification_enabled' in request.form
    privacy_mode = 'privacy_mode' in request.form
    analysis_frequency = request.form.get('analysis_frequency', 5, type=int)
    
    try:
        # Update settings in database
        db = get_db()
        db.execute(
            'UPDATE settings SET theme = ?, notification_enabled = ?, '
            'privacy_mode = ?, analysis_frequency = ?, updated_at = CURRENT_TIMESTAMP '
            'WHERE user_id = ?',
            (theme, notification_enabled, privacy_mode, analysis_frequency, user_id)
        )
        db.commit()
        
        flash('Settings updated successfully.')
    except Exception as e:
        flash(f'Error updating settings: {str(e)}')
    
    return redirect(url_for('settings_bp.settings'))

@settings_bp.route('/account', methods=['POST'])
@login_required
def update_account():
    """Update user account information."""
    user_id = session.get('user_id')
    
    # Get form data
    email = request.form.get('email')
    
    # Validate input
    if not email:
        flash('Email is required.')
        return redirect(url_for('settings_bp.settings'))
    
    try:
        # Update user in database
        db = get_db()
        db.execute(
            'UPDATE users SET email = ? WHERE id = ?',
            (email, user_id)
        )
        db.commit()
        
        flash('Account information updated successfully.')
    except Exception as e:
        flash(f'Error updating account: {str(e)}')
    
    return redirect(url_for('settings_bp.settings'))

@settings_bp.route('/password', methods=['POST'])
@login_required
def update_password():
    """Update user password."""
    from werkzeug.security import check_password_hash, generate_password_hash
    
    user_id = session.get('user_id')
    
    # Get form data
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate input
    if not current_password:
        flash('Current password is required.')
        return redirect(url_for('settings_bp.settings'))
    
    if not new_password:
        flash('New password is required.')
        return redirect(url_for('settings_bp.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.')
        return redirect(url_for('settings_bp.settings'))
    
    # Check current password
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    
    if not check_password_hash(user['password_hash'], current_password):
        flash('Current password is incorrect.')
        return redirect(url_for('settings_bp.settings'))
    
    try:
        # Update password
        password_hash = generate_password_hash(new_password)
        db.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (password_hash, user_id)
        )
        db.commit()
        
        flash('Password updated successfully.')
    except Exception as e:
        flash(f'Error updating password: {str(e)}')
    
    return redirect(url_for('settings_bp.settings'))