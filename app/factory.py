import os
from flask import Flask, current_app
# Assuming db functions are correctly importable like this
# You might need adjustments based on your exact db setup file structure
from app.database.db import init_db, get_db
from app.config import config_by_name
# Import the routes module
from . import routes 

class AppContextManager:
    """Context manager for handling Flask application context."""

    def __init__(self, app=None):
        """
        Initialize the context manager.

        Args:
            app: Flask application instance, defaults to current_app if None
        """
        self.app = app if app is not None else current_app._get_current_object()
        self.ctx = None

    def __enter__(self):
        """Enter the application context."""
        self.ctx = self.app.app_context()
        return self.ctx.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the application context."""
        if self.ctx is not None:
            return self.ctx.__exit__(exc_type, exc_val, exc_tb)

def create_app(config_name="development"):
    """
    Create and configure the Flask application.

    Args:
        config_name (str): Configuration environment name
                          (development, testing, production)

    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__, instance_relative_config=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Folder already exists

    # Load configuration
    # Consider adding error handling if config_name is invalid
    try:
        app.config.from_object(config_by_name[config_name])
    except KeyError:
        raise ValueError(f"Invalid configuration name: {config_name}")

    # Initialize database (ensure this handles potential errors)
    try:
        with app.app_context():
            init_db()
    except Exception as e:
        # Log error and potentially raise it or handle gracefully
        app.logger.error(f"Database initialization failed: {e}")
        # Depending on severity, you might want to raise e here

    # Register teardown context to close DB connection
    app.teardown_appcontext(close_db)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register the before_request handler
    routes.register_routes(app)

    # Add a app_context_manager method to the app for easier access
    app.app_context_manager = lambda: AppContextManager(app)

    # You might have other registrations here (CLI commands, extensions, etc.)

    app.logger.info(f"Flask app created with '{config_name}' configuration.")
    return app

def close_db(e=None):
    """Close database connection at the end of a request."""
    # This assumes get_db() correctly retrieves the request-specific connection
    # possibly stored in g by get_db itself.
    db = get_db()
    if hasattr(db, 'close'): # Check if it's a closable connection object
        db.close()


def register_blueprints(app):
    """Register Flask blueprints."""
    # It's often cleaner to import blueprints inside the function
    # to avoid circular dependencies if blueprints import from factory or app.
    from app.blueprints.main import main_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.settings import settings_bp
    from app.api.routes import api_bp # Ensure this path is correct

    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.logger.info("Blueprints registered.")

def register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template, current_app # Import current_app for logging

    @app.errorhandler(404)
    def page_not_found(e):
        # Passing the exception 'e' might expose internal details, usually avoided.
        return render_template('error.html', error_code=404, error_message="Page Not Found", title='Page Not Found'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        # Log the actual exception
        current_app.logger.error(f"500 Internal Server Error: {e}", exc_info=True)
        # Avoid passing the raw exception 'e' to the template in production
        return render_template('error.html', error_code=500, error_message="Internal Server Error", title='Internal Server Error'), 500

    # Add handlers for other common errors like 403, 401 if needed
    app.logger.info("Error handlers registered.")