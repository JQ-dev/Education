# Quick Guide: Enable Authentication

## For Corporate Users Only Login

The SABER Dashboard has **partial authentication**:
- ✅ **Public**: National, Department, Municipality averages (no login)
- 🔒 **Protected**: School details, Advanced analytics, Reports (login required)

## Enable in 3 Steps

### Step 1: Install Dependencies
```bash
pip install flask-login flask-sqlalchemy
```

### Step 2: Enable Authentication
```bash
export ENABLE_AUTH=true
```

### Step 3: Run the App
```bash
python app_enhanced.py
```

## First Login

When you first run with auth enabled, use these credentials:

- **Username:** `admin`
- **Email:** `admin@saber.gov.co`
- **Password:** `admin123`

⚠️ Change this password immediately!

## What Happens

### Without Login (Public Access)
- ✅ View National Overview
- ✅ View Department Analysis
- ✅ View Municipality Analysis
- ❌ Cannot view School Analysis
- ❌ Cannot view Socioeconomic Analysis
- ❌ Cannot view Advanced Analytics
- ❌ Cannot view Policy KPIs

### After Login (Corporate Access)
- ✅ All public tabs
- ✅ School Analysis (individual schools)
- ✅ Socioeconomic Analysis (detailed demographics)
- ✅ Advanced Analytics (ML models, predictions)
- ✅ Policy KPIs (government metrics, recommendations)

## Register New Users

1. Go to `http://127.0.0.1:8052/register`
2. Fill in the registration form
3. Login with new credentials

## Disable Authentication

```bash
export ENABLE_AUTH=false
python app_enhanced.py
```

All tabs become public again.

## Need Help?

See `AUTHENTICATION_GUIDE.md` for complete documentation.
