import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-do-not-use-in-prod")
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")
    CLEANED_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cleaned_files")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # Allowed Extensions
    ALLOWED_EXTENSIONS = {"csv", "xlsx"}
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://" # Change to redis:// in production if needed

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Ensure a strong secret key is used in production
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    # Stronger session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# Dictionary to easily map environment names to config classes
config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
