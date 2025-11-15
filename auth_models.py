"""
Database models for user authentication and institution management
Supports both SQLite (development) and PostgreSQL (production)
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class Institution(db.Model):
    """Institution/Organization model"""
    __tablename__ = 'institutions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    institution_type = db.Column(db.String(100))  # e.g., 'government', 'university', 'ngo'
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship
    users = db.relationship('User', backref='institution', lazy=True)

    def __repr__(self):
        return f'<Institution {self.name}>'


class User(UserMixin, db.Model):
    """User model - supports both institutional and individual users"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # User type and institution
    user_type = db.Column(db.String(20), nullable=False)  # 'individual' or 'institutional'
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True)

    # Role-based access control
    role = db.Column(db.String(20), default='user')  # 'user', 'admin', 'institution_admin'

    # User metadata
    full_name = db.Column(db.String(200))
    department = db.Column(db.String(100))  # For institutional users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)

    def is_institution_admin(self):
        """Check if user is an institution admin"""
        return self.role == 'institution_admin'

    def is_system_admin(self):
        """Check if user is a system admin"""
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class AuditLog(db.Model):
    """Audit log for tracking user actions"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100))  # e.g., 'login', 'logout', 'view_kpi', 'export_data'
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)  # JSON string with additional details

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.user_id} {self.action} {self.timestamp}>'


def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


def create_default_admin(app, username='admin', email='admin@example.com', password='admin123'):
    """Create default admin user if not exists"""
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(username=username).first()
        if not admin:
            admin = User(
                username=username,
                email=email,
                user_type='individual',
                role='admin',
                full_name='System Administrator',
                is_active=True
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Default admin user created: {username} / {password}")
            print("⚠️  IMPORTANT: Change the default password immediately!")
        else:
            print(f"Admin user '{username}' already exists")
