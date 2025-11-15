# Authentication Integration Guide

## Overview

This guide explains how to integrate the authentication system with your existing Dash applications (`app.py` and `app_enhanced.py`).

## Integration Approach

Since Dash applications are different from traditional Flask apps, we have two approaches:

### Approach 1: Separate Flask + Dash (Recommended for Production)

Use Flask for authentication and serve Dash as a sub-application:

```python
from flask import Flask, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import dash

# Flask app for authentication
server = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(server)

# Dash app
dash_app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')

# Protect dashboard routes
@server.before_request
def require_login():
    # Implement authentication check
    pass
```

### Approach 2: Dash Enterprise Auth (For Dash Enterprise deployments)

Use Dash Enterprise's built-in authentication features.

### Approach 3: Custom Dash Auth (Simplified - Good for Development)

Implement custom authentication within Dash using callbacks and dcc.Location.

## Quick Start Integration

### Step 1: Install Dependencies

```bash
pip install -r requirements_auth.txt
```

### Step 2: Initialize Database

```bash
python init_database.py
```

### Step 3: Choose Integration Method

#### Option A: Run Authenticated Version (Recommended)

Create `app_with_auth.py` based on the template provided.

#### Option B: Add Authentication Layer to Existing App

Modify `app_enhanced.py` to check authentication before rendering.

## Detailed Integration Steps

### 1. Import Authentication Modules

```python
from flask import Flask, session, redirect
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from auth_models import db, User, Institution
from auth_config import get_config
from auth_pages import create_login_layout, create_register_individual_layout
```

### 2. Configure Flask Server

```python
import dash

# Create Flask server with config
server = Flask(__name__)
config = get_config()
server.config.from_object(config)

# Initialize database
db.init_app(server)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

# Create Dash app with Flask server
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
```

### 3. Add User Loader

```python
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

### 4. Create Multi-Page Layout

```python
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    # Check if user is authenticated
    if pathname == '/login':
        return create_login_layout()
    elif pathname == '/register-individual':
        return create_register_individual_layout()
    elif pathname == '/dashboard' or pathname == '/':
        if current_user.is_authenticated:
            return create_dashboard_layout()  # Your existing dashboard
        else:
            return dcc.Location(pathname='/login', id='redirect')
    else:
        return html.H1('404 - Page Not Found')
```

### 5. Add Login Callback

```python
@app.callback(
    [Output('login-alert', 'children'),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('login-remember', 'value')],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password, remember):
    if not n_clicks:
        return dash.no_update, dash.no_update

    # Validate inputs
    if not username or not password:
        return dbc.Alert("Please enter username and password", color="danger"), dash.no_update

    # Find user
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if user and user.check_password(password) and user.is_active:
        login_user(user, remember=remember)
        return dbc.Alert("Login successful!", color="success"), '/dashboard'
    else:
        return dbc.Alert("Invalid credentials", color="danger"), dash.no_update
```

### 6. Add Registration Callbacks

```python
@app.callback(
    [Output('register-alert', 'children'),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('register-button', 'n_clicks')],
    [State('register-fullname', 'value'),
     State('register-username', 'value'),
     State('register-email', 'value'),
     State('register-password', 'value'),
     State('register-password-confirm', 'value')],
    prevent_initial_call=True
)
def handle_registration(n_clicks, fullname, username, email, password, password_confirm):
    if not n_clicks:
        return dash.no_update, dash.no_update

    # Validate inputs
    if not all([fullname, username, email, password, password_confirm]):
        return dbc.Alert("All fields are required", color="danger"), dash.no_update

    if password != password_confirm:
        return dbc.Alert("Passwords do not match", color="danger"), dash.no_update

    if len(password) < 8:
        return dbc.Alert("Password must be at least 8 characters", color="danger"), dash.no_update

    # Check if username/email already exists
    if User.query.filter_by(username=username).first():
        return dbc.Alert("Username already exists", color="danger"), dash.no_update

    if User.query.filter_by(email=email).first():
        return dbc.Alert("Email already exists", color="danger"), dash.no_update

    # Create new user
    new_user = User(
        username=username,
        email=email,
        full_name=fullname,
        user_type='individual',
        role='user',
        is_active=True
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return dbc.Alert("Registration successful! Please login.", color="success"), '/login'
```

### 7. Add Logout Functionality

```python
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if n_clicks:
        logout_user()
        return '/login'
    return dash.no_update
```

### 8. Add User Info to Dashboard

```python
def create_dashboard_layout():
    """Create dashboard layout with user info"""
    return dbc.Container([
        # Header with user info
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(f"Welcome, {current_user.full_name or current_user.username}"),
                    dbc.Button("Logout", id="logout-button", color="danger", size="sm", className="ms-3")
                ], className="d-flex justify-content-between align-items-center mb-3")
            ])
        ]),

        # Your existing dashboard content
        # ... (copy from app_enhanced.py)

    ], fluid=True)
```

## Testing

### 1. Test Database Creation

```bash
python init_database.py
```

### 2. Test Login

```bash
python app_with_auth.py
# Open http://localhost:8052/login
# Login with: admin / admin123
```

### 3. Test Registration

- Navigate to registration page
- Create a new account
- Login with new credentials

## Production Deployment

### Environment Variables

Set these before deploying:

```bash
export FLASK_ENV=production
export SECRET_KEY=your-production-secret-key
export DATABASE_URL=postgresql://user:pass@host:port/db
```

### Database Migration

If deploying to cloud with PostgreSQL:

```bash
# On your cloud platform
python init_database.py
```

### HTTPS Configuration

Always use HTTPS in production. Most cloud platforms handle this automatically.

## Troubleshooting

### Issue: Login callback not working

- Check `suppress_callback_exceptions=True` in Dash app config
- Verify Flask-Login is properly initialized
- Check browser console for errors

### Issue: Database errors

- Verify DATABASE_URL is correct
- Check database permissions
- Run `init_database.py` to create tables

### Issue: Session not persisting

- Verify SECRET_KEY is set
- Check cookie settings in browser
- Ensure HTTPS in production

## Next Steps

1. Customize login/registration pages with your branding
2. Add password reset functionality
3. Implement two-factor authentication
4. Add email verification
5. Create admin panel for user management
6. Implement audit logging for compliance

## Support

For questions or issues, refer to AUTH_README.md or open an issue on GitHub.
