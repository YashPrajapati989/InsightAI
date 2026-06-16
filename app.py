import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

# Initialize extensions
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()

def create_app(config_name="default"):
    """Application factory for InsightAI."""
    app = Flask(__name__)
    
    # Load configuration
    from config import config_dict
    app.config.from_object(config_dict[config_name])
    
    # Enforce SECRET_KEY requirement in production
    if config_name == "production" and not app.config.get("SECRET_KEY"):
        raise ValueError("No SECRET_KEY set for production application. Please set the SECRET_KEY environment variable.")
    
    # Ensure necessary folders exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["CLEANED_FOLDER"], exist_ok=True)
    
    # Setup Logging
    configure_logging(app)
    
    # Initialize extensions
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Apply Talisman for HTTP Security Headers (CSP, HTTPS, etc.)
    # In development, we might want to disable HTTPS enforcement if not using SSL locally.
    force_https = app.config.get("DEBUG") is False
    csp = {
        'default-src': [
            '\'self\'',
        ],
        'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',  # Allow inline scripts for development
        ],
        'style-src': [
            '\'self\'',
            '\'unsafe-inline\'', # Allowed for simple internal styles if needed
        ],
        'img-src': [
            '\'self\'',
            'data:',  # Allow base64 chart images from ChatEngine
        ],
        'connect-src': [
            '\'self\'',  # Allow fetch/XHR to same origin (e.g. /api/chat)
        ],
    }
    talisman.init_app(app, force_https=force_https, content_security_policy=csp)
    
    # Register Blueprints
    from routes.main import main_bp
    from routes.upload import upload_bp
    
    app.register_blueprint(main_bp)
    
    # Apply rate limiting specifically to the upload route
    limiter.limit(app.config.get("RATELIMIT_DEFAULT", "200 per day;50 per hour"))(upload_bp)
    app.register_blueprint(upload_bp)
    
    # Register Error Handlers
    register_error_handlers(app)
    
    # Start background cleanup thread
    from utils.cleanup import start_cleanup_thread
    start_cleanup_thread(app)
    
    app.logger.info("InsightAI Application Startup")
    
    return app

def configure_logging(app):
    """Configure structured and secure logging."""
    if not app.logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        
        # Log to file
        log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(os.path.join(log_dir, 'insightai.log'), maxBytes=10485760, backupCount=10)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)

def register_error_handlers(app):
    """Register global error handlers to prevent exposing stack traces."""
    
    @app.errorhandler(400)
    def bad_request(e):
        app.logger.warning(f"400 Bad Request: {e}")
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        app.logger.warning(f"413 Request Entity Too Large: {e}")
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"500 Internal Server Error: {e}")
        return render_template('errors/500.html'), 500

if __name__ == "__main__":
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    app.run(debug=app.config.get("DEBUG", True))
