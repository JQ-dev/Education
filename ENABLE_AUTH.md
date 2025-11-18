# 🔐 Enabling Authentication

Your SABER Analytics dashboard now has **optional authentication** built-in. It's disabled by default, but you can enable it easily.

## ⚡ Quick Start

### Local Development:
```bash
# Install auth dependencies
pip install flask-login flask-sqlalchemy

# Enable authentication
export ENABLE_AUTH=true

# Run the app
python app.py
```

### Cloud Deployment (Render/Railway/Fly.io):

Add this environment variable in your service settings:
```
ENABLE_AUTH=true
```

## 🎯 Features When Enabled

✅ **Login page** at `/login`
✅ **Individual registration** at `/register`
✅ **Institution registration** at `/register-institution`
✅ **Default admin account**: username=`admin`, password=`admin123`
✅ **SQLite database** for development (auto-created)
✅ **PostgreSQL ready** for production

## 🚀 Access the Auth Pages

Once enabled, visit:

- **Login**: `http://localhost:8052/login`
- **Register (Individual)**: `http://localhost:8052/register`
- **Register (Institution)**: `http://localhost:8052/register-institution`

## 👥 User Types

### 1. Individual Users
- Independent researchers
- Government analysts
- Educators
- Students

### 2. Institutional Users
- Government agencies (Ministerio de Educación, ICFES, etc.)
- Universities and research centers
- NGOs working in education
- Multiple users per institution

## 🔑 Default Admin Account

When authentication is first enabled, a default admin account is created:

- **Username**: `admin`
- **Email**: `admin@saber.gov.co`
- **Password**: `admin123`

**⚠️ IMPORTANT**: Change this password immediately after first login in production!

## 📊 Production Deployment

### Step 1: Install Dependencies

Add to your `requirements.txt`:
```txt
flask-login>=0.6.3
flask-sqlalchemy>=3.1.1
```

Or install directly:
```bash
pip install -r requirements_auth.txt
```

### Step 2: Configure Environment Variables

On **Render**:
1. Go to your service settings
2. Environment → Add Environment Variable
3. Key: `ENABLE_AUTH`, Value: `true`
4. (Optional) Key: `DATABASE_URL`, Value: your PostgreSQL URL
5. (Optional) Key: `SECRET_KEY`, Value: your secret key
6. Click "Save Changes"

On **Railway**:
1. Click on your service
2. Variables tab
3. Add: `ENABLE_AUTH=true`
4. Railway auto-provides `DATABASE_URL` for PostgreSQL

On **Fly.io**:
```bash
flyctl secrets set ENABLE_AUTH=true
```

### Step 3: Deploy

Your authentication system will automatically activate on next deployment!

## 🗄️ Database

### Development (SQLite)
```python
# Auto-created at: education_dashboard.db
# Located in your project root
```

### Production (PostgreSQL)
```python
# Set DATABASE_URL environment variable
# Example: postgresql://user:pass@host:5432/dbname
```

## 🔧 Testing Authentication

### 1. Test Individual Registration
```bash
# Go to http://localhost:8052/register
# Fill form:
#   - Full Name: Test User
#   - Username: testuser
#   - Email: test@example.com
#   - Password: password123
#   - Confirm Password: password123
# Click "Register"
```

### 2. Test Login
```bash
# Go to http://localhost:8052/login
# Enter credentials:
#   - Username: testuser (or email: test@example.com)
#   - Password: password123
# Click "Sign In"
# You should be redirected to /dashboard
```

### 3. Test Institution Registration
```bash
# Go to http://localhost:8052/register-institution
# Fill institution info:
#   - Institution Name: Ministerio de Educación
#   - Type: Government Agency
#   - Contact Email: contact@mineducacion.gov.co
# Fill admin info:
#   - Full Name: Admin User
#   - Username: minedu_admin
#   - Email: admin@mineducacion.gov.co
#   - Password: securepass123
# Click "Register Institution"
```

## 🛡️ Security Best Practices

1. **Change default admin password** immediately in production
2. **Use strong SECRET_KEY** in production:
   ```bash
   export SECRET_KEY="your-very-long-random-secret-key-here"
   ```
3. **Use HTTPS** in production (Render/Railway provide this automatically)
4. **Use PostgreSQL** in production (not SQLite)
5. **Regular backups** of user database
6. **Monitor audit logs** (feature included in auth_models.py)

## 🎨 Customizing Auth Pages

The authentication pages are in `auth_pages.py`. You can customize:

- Logos and branding
- Colors and styles
- Form fields
- Validation rules
- Email templates
- Password requirements

Example:
```python
# In auth_pages.py, modify create_login_layout():
html.H2("SABER Educational Dashboard", ...)  # Change to your title
html.H5("Sign In", ...)  # Change heading
```

## ❌ Disabling Authentication

To disable authentication:

### Local:
```bash
unset ENABLE_AUTH
# or
export ENABLE_AUTH=false
```

### Cloud:
Remove the `ENABLE_AUTH` environment variable or set it to `false`

## 🐛 Troubleshooting

### "Login button doesn't work"
**Problem**: Authentication not enabled
**Solution**: Set `ENABLE_AUTH=true` environment variable

### "Registration fails silently"
**Problem**: Database not initialized
**Solution**: Check logs for errors, ensure write permissions

### "Can't access dashboard after login"
**Problem**: Session configuration
**Solution**: Set `SECRET_KEY` environment variable

### "Database locked (SQLite)"
**Problem**: SQLite doesn't handle concurrent users well
**Solution**: Use PostgreSQL for production

### View logs:
```bash
# Local
python app.py  # Check console output

# Render
Dashboard → Logs tab

# Railway
Service → Deployments → Click deployment → View logs
```

## 📚 Additional Resources

- **AUTH_README.md**: Detailed authentication guide
- **INTEGRATION_GUIDE.md**: Step-by-step integration
- **auth_models.py**: Database models
- **auth_config.py**: Configuration options
- **init_database.py**: Manual database initialization

## 💡 Next Steps

1. ✅ Enable authentication with `ENABLE_AUTH=true`
2. ✅ Test login/registration locally
3. ✅ Configure PostgreSQL for production
4. ✅ Change default admin password
5. ✅ Deploy to cloud with auth enabled
6. ✅ Create institutional accounts
7. ✅ Add your team members
8. ✅ Monitor audit logs

## 🎉 You're Ready!

Authentication is now integrated and ready to use. Enable it whenever you're ready to control access to your educational analytics platform!

---

**Questions?** Check the existing auth documentation files or reach out for support.
