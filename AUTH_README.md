# Authentication System for SABER Education Dashboard

## Overview

This authentication system provides secure user login with support for:
- **Individual User Accounts** - For individual researchers, analysts, etc.
- **Institutional Accounts** - For organizations with multiple users
- **Role-Based Access Control** - Admin, Institution Admin, and Regular User roles
- **Cloud-Ready** - Works with SQLite (development) and PostgreSQL (production)

## Features

### User Types
1. **Individual Users**: Independent accounts for single users
2. **Institutional Users**: Multiple users belonging to an institution
3. **Institution Admins**: Can manage users within their institution
4. **System Admins**: Full system access and management

### Security Features
- Secure password hashing with bcrypt
- Session management with Flask-Login
- SQL injection protection via SQLAlchemy ORM
- CSRF protection
- Secure cookie settings
- Audit logging for compliance

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements_auth.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your configuration
nano .env
```

### 3. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and set it as `SECRET_KEY` in your .env file.

### 4. Initialize Database

```python
python init_database.py
```

This will:
- Create all necessary database tables
- Create a default admin user (username: admin, password: admin123)

**⚠️ IMPORTANT:** Change the default admin password immediately after first login!

## Usage

### Running the Authenticated Dashboard

```bash
# Development mode
python app_with_auth.py

# Production mode
FLASK_ENV=production python app_with_auth.py
```

### Default Credentials

- **Username**: admin
- **Password**: admin123

**Change these immediately!**

### Registering New Users

#### Individual Users
1. Go to http://localhost:8052/
2. Click "Register as Individual"
3. Fill in the registration form
4. Login with your new credentials

#### Institutional Users
1. Go to http://localhost:8052/
2. Click "Register as Institution"
3. Fill in institution details and admin account info
4. The admin can then add more users to the institution

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email
- `password_hash`: Hashed password
- `user_type`: 'individual' or 'institutional'
- `institution_id`: Foreign key to institutions (nullable)
- `role`: 'user', 'admin', or 'institution_admin'
- `full_name`: User's full name
- `department`: Department (for institutional users)
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp
- `is_active`: Account status

### Institutions Table
- `id`: Primary key
- `name`: Institution name
- `institution_type`: Type (government, university, etc.)
- `contact_email`: Contact email
- `created_at`: Creation timestamp
- `is_active`: Institution status

### Audit Logs Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `action`: Action performed
- `ip_address`: User IP address
- `timestamp`: Action timestamp
- `details`: Additional details (JSON)

## Cloud Deployment

### Environment Variables for Production

Set these in your cloud platform (Heroku, AWS, Google Cloud, etc.):

```bash
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@host:port/database
```

### PostgreSQL Setup

The system automatically handles PostgreSQL connection strings. For cloud platforms:

**Heroku:**
```bash
heroku addons:create heroku-postgresql:mini
# DATABASE_URL is set automatically
```

**AWS RDS:**
```bash
DATABASE_URL=postgresql://username:password@rds-endpoint:5432/dbname
```

**Google Cloud SQL:**
```bash
DATABASE_URL=postgresql://username:password@/dbname?host=/cloudsql/project:region:instance
```

## API Endpoints (Future Enhancement)

The system is designed to support REST API endpoints:

- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/register` - User registration
- `GET /api/users` - List users (admin only)
- `POST /api/institutions` - Create institution (admin only)

## Security Best Practices

1. **Always use HTTPS in production**
2. **Change default admin password immediately**
3. **Keep SECRET_KEY secret and unique**
4. **Regularly update dependencies**
5. **Enable audit logging**
6. **Use strong passwords (min 8 characters)**
7. **Implement rate limiting for login attempts**
8. **Regular security audits**

## Troubleshooting

### Database Connection Issues

```python
# Check database connection
python -c "from auth_models import db; from auth_config import get_config; print(get_config().SQLALCHEMY_DATABASE_URI)"
```

### Reset Admin Password

```python
from auth_models import db, User
from app_with_auth import app

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('new_password')
    db.session.commit()
    print("Password updated!")
```

### View All Users

```python
from auth_models import db, User
from app_with_auth import app

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"{user.username} - {user.email} - {user.role}")
```

## License

Same as the main SABER Education Dashboard project.

## Support

For issues or questions, please open an issue on the GitHub repository.
