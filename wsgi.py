# WSGI Configuration for Production Deployment
# wsgi.py

"""
WSGI configuration file for AI Comment Analysis Platform

This file is used by WSGI servers like Gunicorn, uWSGI, or mod_wsgi
to serve the Flask application in production environments.

Usage:
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
    waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Set environment variables
os.environ.setdefault('FLASK_ENV', 'production')

try:
    from app import app
    
    # Configure for production
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory
        log_dir = project_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Set up file handler
        file_handler = RotatingFileHandler(
            log_dir / 'app.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('AI Comment Analysis Platform startup')
    
    # Production configuration
    app.config.update(
        # Security
        SECRET_KEY=os.environ.get('SECRET_KEY', 'production-secret-key-change-this'),
        
        # File upload settings
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
        UPLOAD_FOLDER=str(project_dir / 'static' / 'uploads'),
        
        # Database (if using)
        # DATABASE_URL=os.environ.get('DATABASE_URL'),
        
        # Cache settings
        SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1 year
        
        # Security headers
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # Create necessary directories
    for directory in ['static/uploads', 'static/exports', 'static/wordclouds']:
        (project_dir / directory).mkdir(parents=True, exist_ok=True)

except ImportError as e:
    print(f"Error importing Flask app: {e}")
    print("Make sure all dependencies are installed and app.py exists")
    sys.exit(1)

if __name__ == "__main__":
    # For development only
    app.run(debug=False, host='0.0.0.0', port=5000)