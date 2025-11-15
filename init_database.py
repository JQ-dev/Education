"""
Database initialization script
Run this to create all tables and default admin user
"""

import os
from flask import Flask
from auth_models import db, init_db, create_default_admin
from auth_config import get_config

def initialize_database():
    """Initialize database with tables and default data"""

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    config = get_config()
    app.config.from_object(config)

    print("=" * 70)
    print("INITIALIZING EDUCATION DASHBOARD DATABASE")
    print("=" * 70)
    print(f"\nEnvironment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")

    # Initialize database
    init_db(app)

    # Create default admin user
    print("\nCreating default admin user...")
    admin_username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')

    create_default_admin(app, admin_username, admin_email, admin_password)

    print("\n" + "=" * 70)
    print("DATABASE INITIALIZATION COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Start the application: python app_with_auth.py")
    print(f"2. Login with: {admin_username} / {admin_password}")
    print("3. IMPORTANT: Change the admin password immediately!")
    print("\n")

if __name__ == '__main__':
    initialize_database()
