"""
Development server runner for the facial emotion recognition application.
"""
from wsgi import app

if __name__ == '__main__':
    # Run the application with debug mode enabled
    app.run(host='0.0.0.0', port=5002, debug=True)