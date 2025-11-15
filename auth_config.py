"""
Authentication configuration
Supports both development (SQLite) and production (PostgreSQL) environments
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    # For development: use SQLite
    # For production: use PostgreSQL from environment variable
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///education_dashboard.db'

    # PostgreSQL URL fix for Heroku/cloud platforms
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # Login configuration
    LOGIN_DISABLED = os.environ.get('LOGIN_DISABLED', 'False').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///education_dashboard.db'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Ensure SECRET_KEY is set in production
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY environment variable must be set in production")


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
