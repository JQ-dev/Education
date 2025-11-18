"""
Quick authentication integration for app.py
This adds login/signup functionality with minimal changes
"""

import os
from flask import Flask, session, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Import auth components
from auth_models import db, User, Institution, init_db
from auth_config import Config
from auth_pages import (
    create_login_layout,
    create_register_individual_layout,
    create_register_institution_layout
)

# Environment variable to enable/disable auth
AUTH_ENABLED = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'


def setup_authentication(dash_app):
    """
    Setup authentication for Dash app
    Call this function after creating your Dash app but before defining layouts

    Usage:
        app = dash.Dash(__name__, ...)
        setup_authentication(app)
    """
    if not AUTH_ENABLED:
        print("⚠️  Authentication DISABLED. Set ENABLE_AUTH=true to enable.")
        return None

    # Configure Flask app
    server = dash_app.server
    server.config.from_object(Config)

    # Initialize database
    db.init_app(server)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(server)
    login_manager.login_view = '/login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create tables
    with server.app_context():
        db.create_all()
        print("✅ Authentication enabled - database tables created")

        # Create default admin if doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@saber.gov.co',
                user_type='individual',
                role='admin',
                full_name='System Administrator'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created: admin/admin123")

    return login_manager


def add_auth_callbacks(dash_app):
    """
    Add authentication callbacks to Dash app
    Call this after setup_authentication() and after defining your main layout

    Returns callback functions for login, logout, and registration
    """
    from dash import Input, Output, State, html
    import dash_bootstrap_components as dbc

    if not AUTH_ENABLED:
        return

    server = dash_app.server

    # Login callback
    @dash_app.callback(
        [Output('login-alert', 'children'),
         Output('url', 'pathname', allow_duplicate=True)],
        [Input('login-button', 'n_clicks')],
        [State('login-username', 'value'),
         State('login-password', 'value'),
         State('login-remember', 'value')],
        prevent_initial_call=True
    )
    def login_user_callback(n_clicks, username, password, remember):
        if not n_clicks:
            return '', dash.no_update

        if not username or not password:
            return dbc.Alert("Please enter username and password", color="danger"), dash.no_update

        with server.app_context():
            # Check by username or email
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()

            if user and user.check_password(password):
                login_user(user, remember=remember)
                return dbc.Alert("Login successful!", color="success"), '/dashboard'
            else:
                return dbc.Alert("Invalid username or password", color="danger"), dash.no_update

    # Individual registration callback
    @dash_app.callback(
        Output('register-alert', 'children'),
        [Input('register-button', 'n_clicks')],
        [State('register-fullname', 'value'),
         State('register-username', 'value'),
         State('register-email', 'value'),
         State('register-password', 'value'),
         State('register-password-confirm', 'value')],
        prevent_initial_call=True
    )
    def register_individual(n_clicks, fullname, username, email, password, password_confirm):
        if not n_clicks:
            return ''

        # Validation
        if not all([fullname, username, email, password, password_confirm]):
            return dbc.Alert("All fields are required", color="danger")

        if password != password_confirm:
            return dbc.Alert("Passwords do not match", color="danger")

        if len(password) < 8:
            return dbc.Alert("Password must be at least 8 characters", color="danger")

        with server.app_context():
            # Check if user exists
            if User.query.filter_by(username=username).first():
                return dbc.Alert("Username already exists", color="danger")

            if User.query.filter_by(email=email).first():
                return dbc.Alert("Email already registered", color="danger")

            # Create user
            new_user = User(
                username=username,
                email=email,
                user_type='individual',
                role='user',
                full_name=fullname
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            return dbc.Alert(
                ["Registration successful! ", html.A("Click here to login", href="/login")],
                color="success"
            )

    # Institution registration callback
    @dash_app.callback(
        Output('register-inst-alert', 'children'),
        [Input('register-inst-button', 'n_clicks')],
        [State('register-inst-name', 'value'),
         State('register-inst-type', 'value'),
         State('register-inst-contact', 'value'),
         State('register-inst-admin-fullname', 'value'),
         State('register-inst-admin-username', 'value'),
         State('register-inst-admin-email', 'value'),
         State('register-inst-admin-password', 'value'),
         State('register-inst-admin-password-confirm', 'value')],
        prevent_initial_call=True
    )
    def register_institution(n_clicks, inst_name, inst_type, inst_contact,
                            admin_fullname, admin_username, admin_email,
                            admin_password, admin_password_confirm):
        if not n_clicks:
            return ''

        # Validation
        required_fields = [inst_name, inst_type, inst_contact, admin_fullname,
                          admin_username, admin_email, admin_password, admin_password_confirm]
        if not all(required_fields):
            return dbc.Alert("All fields are required", color="danger")

        if admin_password != admin_password_confirm:
            return dbc.Alert("Passwords do not match", color="danger")

        if len(admin_password) < 8:
            return dbc.Alert("Password must be at least 8 characters", color="danger")

        with server.app_context():
            # Check if institution exists
            if Institution.query.filter_by(name=inst_name).first():
                return dbc.Alert("Institution name already registered", color="danger")

            # Check if admin user exists
            if User.query.filter_by(username=admin_username).first():
                return dbc.Alert("Username already exists", color="danger")

            if User.query.filter_by(email=admin_email).first():
                return dbc.Alert("Email already registered", color="danger")

            # Create institution
            institution = Institution(
                name=inst_name,
                institution_type=inst_type,
                contact_email=inst_contact
            )
            db.session.add(institution)
            db.session.flush()  # Get institution ID

            # Create admin user
            admin_user = User(
                username=admin_username,
                email=admin_email,
                user_type='institutional',
                role='institution_admin',
                full_name=admin_fullname,
                institution_id=institution.id
            )
            admin_user.set_password(admin_password)

            db.session.add(admin_user)
            db.session.commit()

            return dbc.Alert(
                ["Institution registered successfully! ", html.A("Click here to login", href="/login")],
                color="success"
            )

    # Navigation callbacks
    @dash_app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        [Input('goto-register-individual', 'n_clicks'),
         Input('goto-register-institution', 'n_clicks'),
         Input('goto-login-from-register', 'n_clicks'),
         Input('goto-login-from-inst', 'n_clicks')],
        prevent_initial_call=True
    )
    def navigate_auth_pages(btn1, btn2, btn3, btn4):
        from dash import callback_context
        if not callback_context.triggered:
            return dash.no_update

        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'goto-register-individual':
            return '/register'
        elif button_id == 'goto-register-institution':
            return '/register-institution'
        elif button_id in ['goto-login-from-register', 'goto-login-from-inst']:
            return '/login'

        return dash.no_update


def get_auth_layout(pathname):
    """
    Get authentication layout based on pathname
    Use this in your page routing callback

    Example:
        @app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
        def display_page(pathname):
            # Check if it's an auth page
            auth_layout = get_auth_layout(pathname)
            if auth_layout:
                return auth_layout

            # Your existing routing logic
            if pathname == '/dashboard':
                return create_dashboard_content()
            ...
    """
    if not AUTH_ENABLED:
        return None

    if pathname == '/login':
        return create_login_layout()
    elif pathname == '/register':
        return create_register_individual_layout()
    elif pathname == '/register-institution':
        return create_register_institution_layout()

    return None


def require_login(func):
    """
    Decorator to require login for specific pages

    Usage:
        @require_login
        def create_admin_page():
            return html.Div("Admin content")
    """
    def wrapper(*args, **kwargs):
        if not AUTH_ENABLED:
            return func(*args, **kwargs)

        if not current_user.is_authenticated:
            from dash import html
            import dash_bootstrap_components as dbc
            return dbc.Container([
                dbc.Alert([
                    html.H4("Authentication Required"),
                    html.P("Please login to access this page."),
                    dbc.Button("Go to Login", href="/login", color="primary")
                ], color="warning")
            ])

        return func(*args, **kwargs)

    return wrapper
