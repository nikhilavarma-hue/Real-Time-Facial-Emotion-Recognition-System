"""
WSGI entry point for the facial emotion recognition application.

This module creates the application instance and serves as the entry point
for WSGI servers like Gunicorn.
"""
import os
from app.factory import create_app

# Get the environment from the environment variable (default: development)
env = os.getenv('FLASK_ENV', 'development')

# Create application instance
app = create_app(env)

# Register Jinja2 custom filters
from datetime import datetime

@app.template_filter('tojson')
def tojson_filter(obj):
    """Convert an object to a JSON string."""
    import json
    return json.dumps(obj)

@app.template_filter('formatdate')
def formatdate_filter(date_str, format='%Y-%m-%d %H:%M:%S'):
    """Format a date string."""
    if isinstance(date_str, str):
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            # Handle different date formats
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return date_str
    else:
        date = date_str
    return date.strftime(format)

@app.template_filter('timeago')
def timeago_filter(date_str):
    """Convert a date to a 'time ago' string."""
    if isinstance(date_str, str):
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            # Handle different date formats
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return date_str
    else:
        date = date_str
    
    now = datetime.now()
    diff = now - date
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    elif seconds < 604800:
        return f"{int(seconds / 86400)} days ago"
    else:
        return date.strftime('%Y-%m-%d')

@app.context_processor
def utility_processor():
    """Add utility functions to Jinja2 context."""
    def now(format='%Y-%m-%d %H:%M:%S'):
        return datetime.now().strftime(format)
    
    return dict(now=now)

# Ensure the API blueprint gets properly registered
with app.app_context():
    from app.api.routes import api_bp
    # Check if the blueprint is registered
    if api_bp.name not in [bp.name for bp in app.blueprints.values()]:
        app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    # Run the application (for development only)
    app.run(host='0.0.0.0', port=5000, debug=True)