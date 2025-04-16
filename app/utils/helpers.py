"""
Helper utilities for the facial emotion recognition application.

This module provides utility functions used throughout the application.
"""
import os
import json
import time
import uuid
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, current_app, g, session
from werkzeug.security import generate_password_hash

# Authentication helpers
def generate_token():
    """Generate a random token."""
    return str(uuid.uuid4())

def hash_password(password):
    """Generate a secure password hash."""
    return generate_password_hash(password)

def generate_session_id():
    """Generate a unique session ID."""
    return hashlib.sha256(os.urandom(24)).hexdigest()

# Time and date helpers
def get_timestamp():
    """Get current timestamp in seconds."""
    return time.time()

def get_formatted_date(timestamp=None, format="%Y-%m-%d %H:%M:%S"):
    """
    Convert timestamp to formatted date string.
    
    Args:
        timestamp (float, optional): Unix timestamp. If None, uses current time.
        format (str, optional): Date format string.
    
    Returns:
        str: Formatted date string
    """
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).strftime(format)

def get_date_range(days=7):
    """
    Get start and end dates for a range.
    
    Args:
        days (int, optional): Number of days in the range.
    
    Returns:
        tuple: (start_date, end_date) as ISO format strings
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()

# JSON helpers
def load_json_file(file_path):
    """
    Load JSON data from a file.
    
    Args:
        file_path (str): Path to the JSON file
    
    Returns:
        dict: Loaded JSON data or empty dict if file doesn't exist
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {str(e)}")
        return {}

def save_json_file(data, file_path):
    """
    Save data to a JSON file.
    
    Args:
        data (dict): Data to save
        file_path (str): Path to the JSON file
    
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON file {file_path}: {str(e)}")
        return False

# Validation helpers
def validate_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_username(username):
    """
    Validate username format.
    
    Args:
        username (str): Username to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Usernames should be 3-20 characters, alphanumeric with underscore
    import re
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username))

def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Password should be at least 8 characters
    if len(password) < 8:
        return False
    return True

# Error handling helpers
def api_error(message, status_code=400):
    """
    Create a standardized API error response.
    
    Args:
        message (str): Error message
        status_code (int, optional): HTTP status code
    
    Returns:
        tuple: (jsonify(response), status_code)
    """
    response = {
        'error': message,
        'status': 'error',
        'timestamp': get_timestamp()
    }
    return jsonify(response), status_code

def handle_exception(e):
    """
    Handle exceptions in a standardized way.
    
    Args:
        e (Exception): The exception to handle
    
    Returns:
        tuple: (jsonify(response), status_code)
    """
    # Log the error
    print(f"Error: {str(e)}")
    
    # Return standardized error response
    return api_error(str(e), 500)

# File and directory helpers
def ensure_dir_exists(directory):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (str): Directory path
    """
    os.makedirs(directory, exist_ok=True)

def get_file_extension(filename):
    """
    Get the extension of a file.
    
    Args:
        filename (str): Filename to check
    
    Returns:
        str: File extension (without the dot)
    """
    return os.path.splitext(filename)[1][1:].lower()

def is_valid_image(filename):
    """
    Check if a file is a valid image based on extension.
    
    Args:
        filename (str): Filename to check
    
    Returns:
        bool: True if valid image, False otherwise
    """
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
    return get_file_extension(filename) in valid_extensions

# Performance monitoring
def timed_execution(f):
    """
    Decorator to measure execution time of a function.
    
    Usage:
        @timed_execution
        def my_function():
            # function code
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        execution_time = time.time() - start_time
        print(f"Function {f.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper

# Color utilities for emotion visualization
def get_emotion_color(emotion):
    """
    Get a color for an emotion.
    
    Args:
        emotion (str): Emotion name
    
    Returns:
        str: Hex color code
    """
    emotion_colors = {
        'angry': '#FF0000',    # Red
        'disgust': '#FF8C00',  # Orange
        'fear': '#FFFF00',     # Yellow
        'happy': '#00FF00',    # Green
        'neutral': '#808080',  # Gray
        'sad': '#0000FF',      # Blue
        'surprise': '#FF00FF'  # Magenta
    }
    
    return emotion_colors.get(emotion.lower(), '#FFFFFF')  # Default: white