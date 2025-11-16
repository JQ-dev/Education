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
                html.H1("Plataforma de Analítica Educativa SABER", className="hero-title"),
                html.H4("Analítica Avanzada para Datos Educativos de Colombia", className="hero-subtitle"),
                html.P([
                    "Análisis y visualización integral de los resultados de exámenes SABER ",
                    "en todos los niveles educativos de Colombia. Potenciando decisiones basadas en datos ",
                    "para políticas educativas y planificación institucional."
                ], className="hero-description"),
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-chart-line me-2"), "Explorar Panel"],
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
                html.H2("Resumen de la Plataforma", className="section-header text-center mt-5 mb-4"),

                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div("15,000+", className="stat-number"),
                            html.Div("Colegios Analizados", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Div("2.5M+", className="stat-number"),
                            html.Div("Registros de Estudiantes", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Div("1,100+", className="stat-number"),
                            html.Div("Municipios", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.Div("32", className="stat-number"),
                            html.Div("Departamentos", className="stat-label")
                        ], className="stat-card text-center")
                    ], md=3),
                ], className="mb-5"),
            ], className="mt-5")
        ], fluid=True),

        # Features Section
        dbc.Container([
            html.H2("Características Principales", className="section-header text-center mb-5"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("📊", className="feature-icon"),
                            html.H5("Panorama Nacional", className="feature-title"),
                            html.P([
                                "Análisis integral del desempeño educativo en toda Colombia. ",
                                "Visualizaciones interactivas mostrando tendencias, distribuciones y análisis comparativos."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("🗺️", className="feature-icon"),
                            html.H5("Análisis Geográfico", className="feature-title"),
                            html.P([
                                "Perspectivas a nivel departamental y municipal. Identifique patrones regionales, ",
                                "disparidades y oportunidades para intervenciones focalizadas."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("🏫", className="feature-icon"),
                            html.H5("Desempeño Escolar", className="feature-title"),
                            html.P([
                                "Análisis detallado a nivel de colegio. Busque, compare y referencie ",
                                "instituciones individuales contra promedios regionales y nacionales."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("💰", className="feature-icon"),
                            html.H5("Impacto Socioeconómico", className="feature-title"),
                            html.P([
                                "Analice la relación entre factores socioeconómicos y resultados educativos. ",
                                "Comprenda brechas de equidad e informe decisiones de política."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("🤖", className="feature-icon"),
                            html.H5("Analítica Predictiva", className="feature-title"),
                            html.P([
                                "Modelos de aprendizaje automático para identificar colegios que superan expectativas. ",
                                "Análisis de valor agregado controlando por factores socioeconómicos."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("📈", className="feature-icon"),
                            html.H5("Indicadores de Equidad", className="feature-title"),
                            html.P([
                                "Seis Indicadores Clave de Desempeño independientes que miden equidad educativa, ",
                                "eficiencia y desempeño sistémico en múltiples dimensiones."
                            ], className="feature-description")
                        ])
                    ], className="feature-card")
                ], md=4, className="mb-4"),
            ], className="mb-5")
        ], fluid=True),

        # Data Sources Section
        dbc.Container([
            html.H2("Fuentes de Datos y Metodología", className="section-header text-center mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Exámenes SABER 11", className="mb-3"),
                            html.P([
                                "Resultados completos de pruebas estandarizadas para estudiantes de grado 11 en toda Colombia. ",
                                "Incluye puntajes en Matemáticas, Lectura Crítica, Ciencias Naturales, ",
                                "Sociales y Ciudadanas, e Inglés."
                            ]),
                            html.Ul([
                                html.Li("Datos de desempeño a nivel de estudiante"),
                                html.Li("Resultados agregados por colegio"),
                                html.Li("Estadísticas municipales y departamentales"),
                                html.Li("Información contextual socioeconómica")
                            ])
                        ])
                    ])
                ], md=6, className="mb-4"),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Exámenes SABER 3-5-9", className="mb-3"),
                            html.P([
                                "Resultados de evaluación de primaria y secundaria proporcionando una vista integral ",
                                "del sistema educativo desde los primeros grados hasta la educación media."
                            ]),
                            html.Ul([
                                html.Li("Resultados de grados 3, 5 y 9"),
                                html.Li("Competencia en Lenguaje y Matemáticas"),
                                html.Li("Seguimiento longitudinal del desempeño"),
                                html.Li("Indicadores de intervención temprana")
                            ])
                        ])
                    ])
                ], md=6, className="mb-4"),
            ]),

            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                html.Strong("Privacidad de Datos: "),
                "Todos los datos están anonimizados y agregados para proteger la privacidad de los estudiantes. ",
                "La información individual de estudiantes nunca se muestra ni es accesible a través de esta plataforma."
            ], color="info", className="mt-4")
        ], fluid=True, className="mb-5"),

        # Call to Action
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    html.H3("¿Listo para Explorar los Datos Educativos?", className="text-center mb-4"),
                    html.P([
                        "Acceda a analítica integral, genere reportes personalizados y descubra ",
                        "perspectivas que impulsan el mejoramiento educativo en toda Colombia."
                    ], className="text-center text-muted mb-4"),
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-rocket me-2"), "Comenzar Análisis"],
                            id="btn-start-analyzing",
                            color="primary",
                            size="lg",
                            className="me-3"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-book me-2"), "Ver Documentación"],
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
                        html.H5("Plataforma de Analítica SABER", className="mb-3"),
                        html.P([
                            "Analítica avanzada de datos educativos para Colombia. ",
                            "Impulsado por los datos de exámenes SABER del ICFES."
                        ])
                    ], md=4),

                    dbc.Col([
                        html.H6("Enlaces Rápidos", className="mb-3"),
                        html.Ul([
                            html.Li(html.A("Panel Nacional", href="#", className="footer-link")),
                            html.Li(html.A("Análisis Departamental", href="#", className="footer-link")),
                            html.Li(html.A("Buscador de Colegios", href="#", className="footer-link")),
                            html.Li(html.A("Indicadores Clave", href="#", className="footer-link")),
                        ], style={"listStyle": "none", "padding": 0})
                    ], md=4),

                    dbc.Col([
                        html.H6("Acerca de", className="mb-3"),
                        html.P([
                            "Esta plataforma proporciona herramientas analíticas para actores educativos ",
                            "incluyendo agencias gubernamentales, investigadores, colegios y formuladores de política."
                        ])
                    ], md=4),
                ]),

                html.Hr(style={"borderColor": "rgba(255,255,255,0.2)", "marginTop": "30px"}),

                html.P([
                    "© 2024 Plataforma de Analítica Educativa SABER. ",
                    "Fuente de datos: ICFES Colombia. Todos los derechos reservados."
                ], className="text-center mb-0", style={"opacity": "0.8"})
            ])
        ], className="footer")

    ])
