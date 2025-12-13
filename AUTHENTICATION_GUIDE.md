# SABER Dashboard Authentication Guide

## Overview

The SABER Educational Results Dashboard now includes **partial authentication** that protects detailed corporate information while keeping aggregate public data accessible to everyone.

## Authentication Model

### Public Access (No Login Required)
Anyone can view aggregate statistics and performance data:
- 📊 **National Overview** - National statistics, subject comparisons, grade-level analysis
- 🗺️ **Department Analysis** - Performance by all 32 departments, municipality rankings
- 🏘️ **Municipality Analysis** - Municipal-level statistics for 1,100+ municipalities

### Protected Access (Corporate Login Required)
Detailed information and advanced analytics require authentication:
- 🏫 **School Analysis** - Individual school profiles, detailed performance data
- 💰 **Socioeconomic Analysis** - Impact analysis, equity gaps, detailed demographics
- 🤖 **Advanced Analytics** - ML models, value-added analysis, predictions
- 📋 **Policy KPIs Dashboard** - Government KPIs, policy recommendations, intervention priorities

## Quick Start

### 1. Enable Authentication

Set the environment variable before running the app:

```bash
export ENABLE_AUTH=true
python app_enhanced.py
```

Or in Windows:
```cmd
set ENABLE_AUTH=true
python app_enhanced.py
```

### 2. Access the Dashboard

Open your browser to: `http://127.0.0.1:8052`

You'll see:
- **Public tabs** are immediately accessible
- **Protected tabs** show a login prompt when clicked
- **Login/Register buttons** in the top-right corner

### 3. First Time Setup

When you first enable authentication, a default admin account is created:

**Default Credentials:**
- Username: `admin`
- Email: `admin@saber.gov.co`
- Password: `admin123`

⚠️ **IMPORTANT:** Change the default password immediately in production!

## User Registration

### Individual Users

1. Click **Register** button
2. Fill in the form:
   - Full Name
   - Username (unique)
   - Email (unique)
   - Password (min 8 characters)
   - Confirm Password
3. Click **Register**
4. Login with your credentials

### Institutional Users

For organizations (government agencies, universities, NGOs):

1. Click **Register** → **Register Institution**
2. Fill in institution details:
   - Institution Name
   - Institution Type (Government, University, NGO, etc.)
   - Contact Email
3. Fill in admin account details:
   - Full Name
   - Username
   - Email
   - Password
4. Click **Register**
5. The institution admin can now manage users

## User Roles

### Regular User (`user`)
- Access to all protected tabs
- Can view detailed school data and analytics
- Cannot manage other users

### Institution Admin (`institution_admin`)
- All regular user permissions
- Can manage users within their institution
- Associated with a specific institution

### System Admin (`admin`)
- Full system access
- Can manage all users and institutions
- System-wide administration

## Access Control Summary

| Tab | Public Access | Requires Login |
|-----|--------------|----------------|
| 📊 National Overview | ✅ Yes | ❌ No |
| 🗺️ Department Analysis | ✅ Yes | ❌ No |
| 🏘️ Municipality Analysis | ✅ Yes | ❌ No |
| 🏫 School Analysis | ❌ No | ✅ Yes |
| 💰 Socioeconomic Analysis | ❌ No | ✅ Yes |
| 🤖 Advanced Analytics | ❌ No | ✅ Yes |
| 📋 Policy KPIs | ❌ No | ✅ Yes |

## Database

### Development (Default)
Uses SQLite for easy setup:
- Database file: `instance/saber_auth.db`
- Automatically created on first run
- Suitable for development and testing

### Production
Configure PostgreSQL for production:

```bash
export DATABASE_URL="postgresql://user:password@localhost/saber_db"
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV=production
export ENABLE_AUTH=true
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_AUTH` | `false` | Enable/disable authentication system |
| `SECRET_KEY` | Auto-generated | Session encryption key (set in production!) |
| `DATABASE_URL` | SQLite | Database connection string |
| `FLASK_ENV` | `development` | Environment mode |
| `SESSION_LIFETIME_HOURS` | `24` | How long sessions last |

## Security Features

### Password Security
- Passwords hashed with Werkzeug (bcrypt)
- Minimum 8 characters required
- Never stored in plain text

### Session Management
- Secure session cookies
- 24-hour default session lifetime
- "Remember Me" option available

### Audit Logging
All authentication events are logged:
- User logins/logouts
- Page access attempts
- Admin actions
- IP addresses recorded

### CSRF Protection
- SameSite cookie policy
- Session cookie security
- HTTPOnly flags on cookies

## Disabling Authentication

To run without authentication (all tabs public):

```bash
export ENABLE_AUTH=false
python app_enhanced.py
```

Or simply don't set `ENABLE_AUTH` (defaults to false).

## Troubleshooting

### Cannot login after enabling auth

**Solution:** Make sure the database is initialized:
```bash
python init_database.py
```

### Forgot admin password

**Solution:** Reset via database or recreate:
```bash
rm instance/saber_auth.db
python app_enhanced.py  # Will create new admin
```

### Getting "Login Required" on public tabs

**Solution:** Check that `ENABLE_AUTH` is set correctly. Public tabs should always be accessible.

### Database errors on startup

**Solution:** Install auth dependencies:
```bash
pip install flask-login flask-sqlalchemy
```

## Architecture

### Files

- `auth_integration_enhanced.py` - Enhanced authentication with partial protection
- `auth_models.py` - Database models (User, Institution, AuditLog)
- `auth_config.py` - Configuration management
- `auth_pages.py` - Login/registration UI layouts
- `app_enhanced.py` - Main dashboard with integrated auth

### How It Works

1. **Startup**: `setup_authentication()` initializes Flask-Login and database
2. **Routing**: URL-based routing handles login/register pages
3. **Access Control**: Each protected tab callback checks `is_tab_accessible()`
4. **Session**: Flask-Login manages user sessions
5. **Public Tabs**: Always accessible, no authentication check
6. **Protected Tabs**: Show login prompt if user not authenticated

## Production Deployment

### Heroku

```bash
# Set environment variables
heroku config:set ENABLE_AUTH=true
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set DATABASE_URL=<your-postgres-url>

# Deploy
git push heroku main
```

### Docker

```dockerfile
ENV ENABLE_AUTH=true
ENV SECRET_KEY=your-secret-key
ENV DATABASE_URL=postgresql://...
```

### Render.com

Add environment variables in dashboard:
- `ENABLE_AUTH` = `true`
- `SECRET_KEY` = (generate secure key)
- `DATABASE_URL` = (auto-provided by Render)

## Best Practices

1. **Always change default admin password** in production
2. **Use PostgreSQL** for production (not SQLite)
3. **Set strong SECRET_KEY** (use `secrets.token_hex(32)`)
4. **Enable HTTPS** in production
5. **Review audit logs** regularly
6. **Backup database** regularly
7. **Monitor failed login attempts**

## Support

For questions or issues:
- Check existing documentation in `/docs` folder
- Review `AUTH_README.md` for technical details
- Check GitHub issues

## Version History

- **v1.1** (Current) - Added partial authentication with public/protected tabs
- **v1.0** - Initial authentication system (all-or-nothing)
