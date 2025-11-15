"""
Professional Landing Page for SABER Education Dashboard
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_landing_page():
    """Create professional landing page layout"""

    return html.Div([
        # Hero Section
        html.Div([
            dbc.Container([
                html.H1("SABER Educational Analytics Platform", className="hero-title"),
                html.H4("Advanced Analytics for Colombian Education Data", className="hero-subtitle"),
                html.P([
                    "Comprehensive analysis and visualization of SABER exam results ",
                    "across all educational levels in Colombia. Empowering data-driven ",
                    "decisions for educational policy and institutional planning."
                ], className="hero-description"),
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-chart-line me-2"), "Explore Dashboard"],
                        id="btn-explore-dashboard",
                        className="btn-explore",
                        size="lg"
                    )
                ], className="mt-4")
            ])
        ], className="hero-section"),

        # Statistics Section
        dbc.Container([
            html.Div([
                html.H2("Platform Overview", className="section-header text-center mt-5 mb-4"),

                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div("15,000+", className="stat-number"),
                            html.Div("Schools Analyzed", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Div("2.5M+", className="stat-number"),
                            html.Div("Student Records", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Div("1,100+", className="stat-number"),
                            html.Div("Municipalities", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Div("32", className="stat-number"),
                            html.Div("Departments", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                ], className="mb-5"),
            ], className="mt-5")
        ], fluid=True),

        # Features Section
        dbc.Container([
            html.H2("Key Features", className="section-header text-center mb-5"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("📊", className="feature-icon"),
                            html.H5("National Overview", className="feature-title"),
                            html.P([
                                "Comprehensive analysis of educational performance across Colombia. ",
                                "Interactive visualizations showing trends, distributions, and comparative analytics."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("🗺️", className="feature-icon"),
                            html.H5("Geographic Analysis", className="feature-title"),
                            html.P([
                                "Department and municipal-level insights. Identify regional patterns, ",
                                "disparities, and opportunities for targeted interventions."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("🏫", className="feature-icon"),
                            html.H5("School Performance", className="feature-title"),
                            html.P([
                                "Detailed school-level analysis. Search, compare, and benchmark ",
                                "individual institutions against regional and national averages."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("💰", className="feature-icon"),
                            html.H5("Socioeconomic Impact", className="feature-title"),
                            html.P([
                                "Analyze the relationship between socioeconomic factors and educational ",
                                "outcomes. Understand equity gaps and inform policy decisions."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("🤖", className="feature-icon"),
                            html.H5("Predictive Analytics", className="feature-title"),
                            html.P([
                                "Machine learning models to identify schools exceeding expectations. ",
                                "Value-added analysis controlling for socioeconomic factors."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("📈", className="feature-icon"),
                            html.H5("Equity KPIs", className="feature-title"),
                            html.P([
                                "Six independent Key Performance Indicators measuring educational equity, ",
                                "efficiency, and systemic performance across multiple dimensions."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),
            ], className="mb-5")
        ], fluid=True),

        # Data Sources Section
        dbc.Container([
            html.H2("Data Sources & Methodology", className="section-header text-center mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("SABER 11 Exams", className="mb-3"),
                            html.P([
                                "Comprehensive standardized test results for 11th grade students across Colombia. ",
                                "Includes scores in Mathematics, Critical Reading, Natural Sciences, ",
                                "Social Sciences & Civics, and English."
                            ]),
                            html.Ul([
                                html.Li("Student-level performance data"),
                                html.Li("School aggregated results"),
                                html.Li("Municipal and departmental statistics"),
                                html.Li("Socioeconomic contextual information")
                            ])
                        ])
                    ])
                ], md=6, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("SABER 3-5-9 Exams", className="mb-3"),
                            html.P([
                                "Elementary and middle school assessment results providing a comprehensive ",
                                "view of the educational pipeline from early grades through high school."
                            ]),
                            html.Ul([
                                html.Li("Grades 3, 5, and 9 results"),
                                html.Li("Language and Mathematics proficiency"),
                                html.Li("Longitudinal performance tracking"),
                                html.Li("Early intervention indicators")
                            ])
                        ])
                    ])
                ], md=6, className="mb-4"),
            ]),

            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                html.Strong("Data Privacy: "),
                "All data is anonymized and aggregated to protect student privacy. ",
                "Individual student information is never displayed or accessible through this platform."
            ], color="info", className="mt-4")
        ], fluid=True, className="mb-5"),

        # Call to Action
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Ready to Explore Educational Data?", className="text-center mb-4"),
                    html.P([
                        "Access comprehensive analytics, generate custom reports, and discover ",
                        "insights that drive educational improvement across Colombia."
                    ], className="text-center text-muted mb-4"),
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-rocket me-2"), "Start Analyzing"],
                            id="btn-start-analyzing",
                            color="primary",
                            size="lg",
                            className="me-3"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-book me-2"), "View Documentation"],
                            color="secondary",
                            size="lg",
                            outline=True
                        ),
                    ], className="text-center")
                ])
            ], className="mb-5", style={"background": "linear-gradient(135deg, #E3F2FD 0%, #F3E5F5 100%)"})
        ], fluid=True),

        # Footer
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H5("SABER Analytics Platform", className="mb-3"),
                        html.P([
                            "Advanced educational data analytics for Colombia. ",
                            "Powered by ICFES SABER examination data."
                        ])
                    ], md=4),

                    dbc.Col([
                        html.H6("Quick Links", className="mb-3"),
                        html.Ul([
                            html.Li(html.A("National Dashboard", href="#", className="footer-link")),
                            html.Li(html.A("Department Analysis", href="#", className="footer-link")),
                            html.Li(html.A("School Finder", href="#", className="footer-link")),
                            html.Li(html.A("KPI Metrics", href="#", className="footer-link")),
                        ], style={"listStyle": "none", "padding": 0})
                    ], md=4),

                    dbc.Col([
                        html.H6("About", className="mb-3"),
                        html.P([
                            "This platform provides analytical tools for educational stakeholders ",
                            "including government agencies, researchers, schools, and policy makers."
                        ])
                    ], md=4),
                ]),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.2)", "marginTop": "30px"}),

                html.P([
                    "© 2024 SABER Educational Analytics Platform. ",
                    "Data source: ICFES Colombia. All rights reserved."
                ], className="text-center mb-0", style={"opacity": "0.8"})
            ])
        ], className="footer")

    ])
