"""
Authentication pages and components for Dash application
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_login_layout():
    """Create login page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H2("SABER Educational Dashboard", className="text-center mb-4"),
                    html.H5("Sign In", className="text-center text-muted mb-4"),

                    dbc.Card([
                        dbc.CardBody([
                            # Login form
                            dbc.Form([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Username or Email", className="fw-bold"),
                                        dbc.Input(
                                            type="text",
                                            id="login-username",
                                            placeholder="Enter username or email",
                                            className="mb-3"
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Password", className="fw-bold"),
                                        dbc.Input(
                                            type="password",
                                            id="login-password",
                                            placeholder="Enter password",
                                            className="mb-3"
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Checkbox(
                                            id="login-remember",
                                            label="Remember me",
                                            value=False,
                                            className="mb-3"
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            "Sign In",
                                            id="login-button",
                                            color="primary",
                                            className="w-100 mb-3",
                                            size="lg"
                                        ),
                                    ])
                                ]),
                                html.Div(id="login-alert", className="mb-3"),
                            ]),

                            html.Hr(),

                            # Registration links
                            html.Div([
                                html.P("Don't have an account?", className="text-center mb-2"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            "Register as Individual",
                                            id="goto-register-individual",
                                            color="secondary",
                                            outline=True,
                                            className="w-100 mb-2"
                                        ),
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Button(
                                            "Register as Institution",
                                            id="goto-register-institution",
                                            color="secondary",
                                            outline=True,
                                            className="w-100 mb-2"
                                        ),
                                    ], md=6),
                                ])
                            ]),
                        ])
                    ], className="shadow"),

                ], style={'maxWidth': '500px', 'margin': '0 auto', 'marginTop': '100px'})
            ], md=12)
        ])
    ], fluid=True)


def create_register_individual_layout():
    """Create individual user registration layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H2("SABER Educational Dashboard", className="text-center mb-4"),
                    html.H5("Register - Individual User", className="text-center text-muted mb-4"),

                    dbc.Card([
                        dbc.CardBody([
                            dbc.Form([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Full Name", className="fw-bold"),
                                        dbc.Input(
                                            type="text",
                                            id="register-fullname",
                                            placeholder="Enter your full name",
                                            className="mb-3"
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Username", className="fw-bold"),
                                        dbc.Input(
                                            type="text",
                                            id="register-username",
                                            placeholder="Choose a username",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Label("Email", className="fw-bold"),
                                        dbc.Input(
                                            type="email",
                                            id="register-email",
                                            placeholder="Enter your email",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Password", className="fw-bold"),
                                        dbc.Input(
                                            type="password",
                                            id="register-password",
                                            placeholder="Choose a password (min 8 characters)",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Label("Confirm Password", className="fw-bold"),
                                        dbc.Input(
                                            type="password",
                                            id="register-password-confirm",
                                            placeholder="Confirm your password",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                ]),
                                html.Div(id="register-alert", className="mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            "Register",
                                            id="register-button",
                                            color="success",
                                            className="w-100 mb-3",
                                            size="lg"
                                        ),
                                    ])
                                ]),
                            ]),

                            html.Hr(),

                            html.Div([
                                html.P("Already have an account?", className="text-center mb-2"),
                                dbc.Button(
                                    "Back to Login",
                                    id="goto-login-from-register",
                                    color="secondary",
                                    outline=True,
                                    className="w-100"
                                ),
                            ]),
                        ])
                    ], className="shadow"),

                ], style={'maxWidth': '600px', 'margin': '0 auto', 'marginTop': '50px'})
            ], md=12)
        ])
    ], fluid=True)


def create_register_institution_layout():
    """Create institutional registration layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H2("SABER Educational Dashboard", className="text-center mb-4"),
                    html.H5("Register - Institution", className="text-center text-muted mb-4"),

                    dbc.Card([
                        dbc.CardBody([
                            html.P("Register your institution to enable multiple users from your organization to access the dashboard.",
                                  className="text-muted mb-4"),

                            dbc.Form([
                                # Institution information
                                html.H6("Institution Information", className="fw-bold mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Institution Name", className="fw-bold"),
                                        dbc.Input(
                                            type="text",
                                            id="register-inst-name",
                                            placeholder="Enter institution name",
                                            className="mb-3"
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Institution Type", className="fw-bold"),
                                        dcc.Dropdown(
                                            id="register-inst-type",
                                            options=[
                                                {'label': 'Government Agency', 'value': 'government'},
                                                {'label': 'University', 'value': 'university'},
                                                {'label': 'Research Institute', 'value': 'research'},
                                                {'label': 'NGO', 'value': 'ngo'},
                                                {'label': 'Private Company', 'value': 'private'},
                                                {'label': 'Other', 'value': 'other'},
                                            ],
                                            placeholder="Select institution type",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Label("Contact Email", className="fw-bold"),
                                        dbc.Input(
                                            type="email",
                                            id="register-inst-contact",
                                            placeholder="Institution contact email",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                ]),

                                html.Hr(),

                                # Admin user information
                                html.H6("Administrator Account", className="fw-bold mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Full Name", className="fw-bold"),
                                        dbc.Input(
                                            type="text",
                                            id="register-inst-admin-fullname",
                                            placeholder="Administrator's full name",
                                            className="mb-3"
                                        ),
                                    ])
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Username", className="fw-bold"),
                                        dbc.Input(
                                            type="text",
                                            id="register-inst-admin-username",
                                            placeholder="Administrator username",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Label("Email", className="fw-bold"),
                                        dbc.Input(
                                            type="email",
                                            id="register-inst-admin-email",
                                            placeholder="Administrator email",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                ]),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Password", className="fw-bold"),
                                        dbc.Input(
                                            type="password",
                                            id="register-inst-admin-password",
                                            placeholder="Choose a password (min 8 characters)",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Label("Confirm Password", className="fw-bold"),
                                        dbc.Input(
                                            type="password",
                                            id="register-inst-admin-password-confirm",
                                            placeholder="Confirm password",
                                            className="mb-3"
                                        ),
                                    ], md=6),
                                ]),

                                html.Div(id="register-inst-alert", className="mb-3"),

                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            "Register Institution",
                                            id="register-inst-button",
                                            color="success",
                                            className="w-100 mb-3",
                                            size="lg"
                                        ),
                                    ])
                                ]),
                            ]),

                            html.Hr(),

                            html.Div([
                                html.P("Already have an account?", className="text-center mb-2"),
                                dbc.Button(
                                    "Back to Login",
                                    id="goto-login-from-inst",
                                    color="secondary",
                                    outline=True,
                                    className="w-100"
                                ),
                            ]),
                        ])
                    ], className="shadow"),

                ], style={'maxWidth': '700px', 'margin': '0 auto', 'marginTop': '50px'})
            ], md=12)
        ])
    ], fluid=True)
