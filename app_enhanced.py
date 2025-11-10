"""
Enhanced Dash App for Colombian SABER School Results Analysis
Designed for governmental agencies to analyze educational performance at multiple levels
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "SABER Results - Government Dashboard"

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_school_aggregated_data():
    """Load aggregated school-level test scores"""
    try:
        scores_df = pd.read_csv('Colegios4.csv')
        schools_df = pd.read_csv('Cole_list3.csv')

        df = pd.merge(
            scores_df,
            schools_df,
            left_on='CODIGO',
            right_on='COLE_COD_DANE_ESTABLECIMIENTO',
            how='left'
        )

        categorical_cols = ['COLE_GENERO', 'COLE_NATURALEZA', 'COLE_CARACTER', 'COLE_AREA_UBICACION']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].fillna('No especificado')

        return df
    except Exception as e:
        print(f"Error loading school data: {e}")
        return pd.DataFrame()


def load_municipality_data():
    """Load municipality-level aggregated scores"""
    try:
        munic_scores = pd.read_csv('Municipios3.csv')
        munic_list = pd.read_csv('Muni_list_proper2.csv')

        df = pd.merge(
            munic_scores,
            munic_list,
            left_on='MUNI_ID',
            right_on='COLE_COD_MCPIO_UBICACION',
            how='left'
        )

        return df
    except Exception as e:
        print(f"Error loading municipality data: {e}")
        return pd.DataFrame()


def load_student_level_data(sample_size=50000):
    """Load student-level data from Saber 11 (sampled for performance)"""
    try:
        # Load both files
        df1 = pd.read_csv('Saber_11__2017-1.csv')

        # Try to load second file if it exists
        try:
            df2 = pd.read_csv('Saber_11__2017-2.csv')
            df = pd.concat([df1, df2], ignore_index=True)
        except:
            df = df1

        # Sample for performance if too large
        if len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)

        return df
    except Exception as e:
        print(f"Error loading student data: {e}")
        return pd.DataFrame()


# Load all datasets
print("Loading data...")
df_schools = load_school_aggregated_data()
df_municipalities = load_municipality_data()
df_students = load_student_level_data()
print(f"Loaded {len(df_schools)} schools, {len(df_municipalities)} municipalities, {len(df_students)} students")

# Create helper data structures
grades = ['3', '5', '9', '11']
subjects = ['Lenguaje', 'Matemáticas']

grade_cols = {}
for grade in grades:
    grade_cols[grade] = {
        'Lenguaje': f'Lenguaje Grado {grade}',
        'Matemáticas': f'Matemáticas Grado {grade}',
        'N': f'N {grade}'
    }

# Get unique values for filters
genero_options = sorted(df_schools['COLE_GENERO'].unique()) if 'COLE_GENERO' in df_schools.columns else []
naturaleza_options = sorted(df_schools['COLE_NATURALEZA'].unique()) if 'COLE_NATURALEZA' in df_schools.columns else []
caracter_options = sorted(df_schools['COLE_CARACTER'].unique()) if 'COLE_CARACTER' in df_schools.columns else []
area_options = sorted(df_schools['COLE_AREA_UBICACION'].unique()) if 'COLE_AREA_UBICACION' in df_schools.columns else []

# Get departments and municipalities
if 'COLE_DEPTO_UBICACION' in df_municipalities.columns:
    departments = sorted(df_municipalities['COLE_DEPTO_UBICACION'].dropna().unique())
else:
    departments = []

# ============================================================================
# APP LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("SABER Educational Results Dashboard", className="text-center mb-3 mt-4"),
            html.H5("Government Analytics Platform - Comprehensive Educational Performance Analysis",
                   className="text-center text-muted mb-4"),
        ])
    ]),

    # Main tabs
    dbc.Tabs(id="main-tabs", active_tab="tab-overview", children=[

        # TAB 1: Overview / Nacional
        dbc.Tab(label="📊 National Overview", tab_id="tab-overview", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Filters")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Grade:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-grade',
                                            options=[{'label': f'Grado {g}', 'value': g} for g in grades],
                                            value='11',
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("School Type:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-naturaleza',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': n, 'value': n} for n in naturaleza_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Area:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-area',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': a, 'value': a} for a in area_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=4),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                # Summary cards
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='overview-total-schools', className="text-center text-primary"),
                                html.P("Schools Analyzed", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='overview-total-students', className="text-center text-success"),
                                html.P("Total Students", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='overview-avg-lang', className="text-center text-info"),
                                html.P("Avg Language Score", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='overview-avg-math', className="text-center text-warning"),
                                html.P("Avg Math Score", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                ], className="mb-4"),

                # Visualizations
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='overview-scatter', style={'height': '500px'})
                    ], md=6),
                    dbc.Col([
                        dcc.Graph(id='overview-distribution', style={'height': '500px'})
                    ], md=6),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='overview-grade-comparison', style={'height': '400px'})
                    ], md=12),
                ]),
            ], className="p-3")
        ]),

        # TAB 2: Department Analysis
        dbc.Tab(label="🗺️ Department Analysis", tab_id="tab-department", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Department Selection")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Select Department:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-selector',
                                            options=[{'label': d, 'value': d} for d in departments],
                                            value=departments[0] if departments else None,
                                            clearable=False
                                        )
                                    ], md=6),
                                    dbc.Col([
                                        html.Label("Grade:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-grade',
                                            options=[{'label': f'Grado {g}', 'value': g} for g in grades],
                                            value='11',
                                            clearable=False
                                        )
                                    ], md=6),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                # Department summary
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='dept-total-munic', className="text-center"),
                                html.P("Municipalities", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='dept-total-schools', className="text-center"),
                                html.P("Schools", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='dept-avg-lang', className="text-center"),
                                html.P("Dept Avg Language", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='dept-avg-math', className="text-center"),
                                html.P("Dept Avg Math", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                ], className="mb-4"),

                # Department visualizations
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='dept-municipality-ranking', style={'height': '500px'})
                    ], md=12),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='dept-performance-map', style={'height': '400px'})
                    ], md=6),
                    dbc.Col([
                        dcc.Graph(id='dept-type-comparison', style={'height': '400px'})
                    ], md=6),
                ]),
            ], className="p-3")
        ]),

        # TAB 3: Municipality Analysis
        dbc.Tab(label="🏘️ Municipality Analysis", tab_id="tab-municipality", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Municipality Selection")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Department:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='munic-dept-selector',
                                            options=[{'label': d, 'value': d} for d in departments],
                                            value=departments[0] if departments else None,
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Municipality:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='munic-selector',
                                            options=[],
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Grade:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='munic-grade',
                                            options=[{'label': f'Grado {g}', 'value': g} for g in grades],
                                            value='11',
                                            clearable=False
                                        )
                                    ], md=4),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                # Municipality stats
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4(id='munic-name', className="text-center"),
                                html.P("Selected Municipality", className="text-center text-muted")
                            ])
                        ])
                    ], md=12),
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='munic-total-schools', className="text-center"),
                                html.P("Schools", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='munic-total-students', className="text-center"),
                                html.P("Students", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='munic-avg-lang', className="text-center"),
                                html.P("Avg Language", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='munic-avg-math', className="text-center"),
                                html.P("Avg Math", className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                ], className="mb-4"),

                # Municipality visualizations
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='munic-school-ranking', style={'height': '500px'})
                    ], md=12),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='munic-performance-dist', style={'height': '400px'})
                    ], md=6),
                    dbc.Col([
                        dcc.Graph(id='munic-school-types', style={'height': '400px'})
                    ], md=6),
                ]),
            ], className="p-3")
        ]),

        # TAB 4: School-Focused Analysis
        dbc.Tab(label="🏫 School Analysis", tab_id="tab-school", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("School Search and Analysis")),
                            dbc.CardBody([
                                html.Label("Search School by Name:", className="fw-bold"),
                                dcc.Input(
                                    id='school-search-input',
                                    type='text',
                                    placeholder='Type school name (min 3 characters)...',
                                    style={'width': '100%'},
                                    className="mb-3"
                                ),
                                html.Div(id='school-search-results')
                            ])
                        ], className="mb-4")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("School Performance Profile")),
                            dbc.CardBody([
                                html.Div(id='school-detail-view')
                            ])
                        ])
                    ])
                ]),
            ], className="p-3")
        ]),

        # TAB 5: Socioeconomic Impact Analysis
        dbc.Tab(label="💰 Socioeconomic Analysis", tab_id="tab-socioeconomic", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Impact of Socioeconomic Factors on Educational Outcomes"),
                        html.P("Analysis based on student-level data from Saber 11 exams", className="text-muted"),
                    ])
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Select Analysis Type")),
                            dbc.CardBody([
                                dcc.Dropdown(
                                    id='socio-analysis-type',
                                    options=[
                                        {'label': 'Parent Education Impact', 'value': 'education'},
                                        {'label': 'Socioeconomic Stratum (Estrato)', 'value': 'estrato'},
                                        {'label': 'Home Assets & Resources', 'value': 'assets'},
                                        {'label': 'Family Economic Situation', 'value': 'economic'},
                                        {'label': 'Comprehensive Socioeconomic Index', 'value': 'index'}
                                    ],
                                    value='estrato',
                                    clearable=False
                                )
                            ])
                        ], className="mb-4")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='socio-main-chart', style={'height': '500px'})
                    ], md=12),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='socio-correlation', style={'height': '400px'})
                    ], md=6),
                    dbc.Col([
                        dcc.Graph(id='socio-distribution', style={'height': '400px'})
                    ], md=6),
                ]),
            ], className="p-3")
        ]),

        # TAB 6: Enhanced Prediction Model
        dbc.Tab(label="🤖 Advanced Analytics", tab_id="tab-prediction", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Value-Added Analysis: Identifying True School Excellence"),
                        html.P("This model controls for socioeconomic factors to identify schools that outperform expectations",
                              className="text-muted"),
                    ])
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Model Configuration")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Analysis Level:", className="fw-bold"),
                                        dcc.RadioItems(
                                            id='pred-level',
                                            options=[
                                                {'label': ' Student-Level Prediction', 'value': 'student'},
                                                {'label': ' School-Level Prediction', 'value': 'school'}
                                            ],
                                            value='school',
                                            inline=True
                                        )
                                    ], md=6),
                                    dbc.Col([
                                        html.Label("Target Score:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='pred-target',
                                            options=[
                                                {'label': 'Mathematics', 'value': 'matematicas'},
                                                {'label': 'Reading/Language', 'value': 'lectura'},
                                                {'label': 'Global Score', 'value': 'global'}
                                            ],
                                            value='matematicas',
                                            clearable=False
                                        )
                                    ], md=6),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Model Performance"),
                                html.Div(id='pred-model-stats')
                            ])
                        ])
                    ], md=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Feature Importance"),
                                dcc.Graph(id='pred-feature-importance', style={'height': '300px'})
                            ])
                        ])
                    ], md=8),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        html.H5("Top Schools: Actual Performance vs Expected (Value-Added)"),
                        dcc.Graph(id='pred-value-added', style={'height': '600px'})
                    ], md=12),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        html.H5("Schools Exceeding Expectations (Positive Residuals)"),
                        html.Div(id='pred-top-schools-table')
                    ], md=6),
                    dbc.Col([
                        html.H5("Schools Below Expectations (Negative Residuals)"),
                        html.Div(id='pred-bottom-schools-table')
                    ], md=6),
                ]),
            ], className="p-3")
        ]),
    ]),

], fluid=True)


# ============================================================================
# CALLBACKS
# ============================================================================

# TAB 1: Overview callbacks
@app.callback(
    [Output('overview-total-schools', 'children'),
     Output('overview-total-students', 'children'),
     Output('overview-avg-lang', 'children'),
     Output('overview-avg-math', 'children'),
     Output('overview-scatter', 'figure'),
     Output('overview-distribution', 'figure'),
     Output('overview-grade-comparison', 'figure')],
    [Input('overview-grade', 'value'),
     Input('overview-naturaleza', 'value'),
     Input('overview-area', 'value')]
)
def update_overview(grade, naturaleza, area):
    """Update overview tab visualizations"""

    # Filter data
    df = df_schools.copy()

    if naturaleza != 'ALL':
        df = df[df['COLE_NATURALEZA'] == naturaleza]
    if area != 'ALL':
        df = df[df['COLE_AREA_UBICACION'] == area]

    lang_col = grade_cols[grade]['Lenguaje']
    math_col = grade_cols[grade]['Matemáticas']
    n_col = grade_cols[grade]['N']

    # Filter out missing values
    df_plot = df[[lang_col, math_col, n_col, 'COLE_NATURALEZA', 'COLE_AREA_UBICACION']].dropna()

    # Calculate stats
    total_schools = len(df_plot)
    total_students = int(df_plot[n_col].sum()) if len(df_plot) > 0 else 0
    avg_lang = f"{df_plot[lang_col].mean():.3f}" if len(df_plot) > 0 else "N/A"
    avg_math = f"{df_plot[math_col].mean():.3f}" if len(df_plot) > 0 else "N/A"

    # Scatter plot
    scatter_fig = px.scatter(
        df_plot,
        x=lang_col,
        y=math_col,
        size=n_col,
        color='COLE_NATURALEZA',
        hover_data=['COLE_AREA_UBICACION'],
        title=f'Language vs Mathematics Performance - Grade {grade}',
        labels={lang_col: 'Language (z-score)', math_col: 'Math (z-score)'},
        opacity=0.6
    )
    scatter_fig.add_shape(
        type="line", line=dict(dash='dash', color='gray'),
        x0=df_plot[lang_col].min(), y0=df_plot[lang_col].min(),
        x1=df_plot[lang_col].max(), y1=df_plot[lang_col].max()
    )

    # Distribution
    dist_fig = make_subplots(rows=1, cols=2, subplot_titles=('Language Distribution', 'Math Distribution'))
    dist_fig.add_trace(
        go.Histogram(x=df_plot[lang_col], name='Language', nbinsx=50, marker_color='lightblue'),
        row=1, col=1
    )
    dist_fig.add_trace(
        go.Histogram(x=df_plot[math_col], name='Math', nbinsx=50, marker_color='lightcoral'),
        row=1, col=2
    )
    dist_fig.update_layout(showlegend=False, title_text=f'Score Distributions - Grade {grade}')

    # Grade comparison
    grade_data = []
    for g in grades:
        lang_g = grade_cols[g]['Lenguaje']
        math_g = grade_cols[g]['Matemáticas']
        temp = df[[lang_g, math_g]].dropna()
        if len(temp) > 0:
            grade_data.append({
                'Grade': g,
                'Language': temp[lang_g].mean(),
                'Mathematics': temp[math_g].mean()
            })

    grade_df = pd.DataFrame(grade_data)
    grade_fig = go.Figure()
    grade_fig.add_trace(go.Bar(x=grade_df['Grade'], y=grade_df['Language'], name='Language', marker_color='lightblue'))
    grade_fig.add_trace(go.Bar(x=grade_df['Grade'], y=grade_df['Mathematics'], name='Mathematics', marker_color='lightcoral'))
    grade_fig.update_layout(title='Average Performance by Grade', barmode='group', xaxis_title='Grade', yaxis_title='Average Score (z-score)')

    return f"{total_schools:,}", f"{total_students:,}", avg_lang, avg_math, scatter_fig, dist_fig, grade_fig


# TAB 2: Department callbacks
@app.callback(
    [Output('dept-total-munic', 'children'),
     Output('dept-total-schools', 'children'),
     Output('dept-avg-lang', 'children'),
     Output('dept-avg-math', 'children'),
     Output('dept-municipality-ranking', 'figure'),
     Output('dept-performance-map', 'figure'),
     Output('dept-type-comparison', 'figure')],
    [Input('dept-selector', 'value'),
     Input('dept-grade', 'value')]
)
def update_department(department, grade):
    """Update department analysis"""

    if not department:
        empty_fig = go.Figure()
        return "0", "0", "N/A", "N/A", empty_fig, empty_fig, empty_fig

    # Filter municipalities in department
    df_munic_dept = df_municipalities[df_municipalities['COLE_DEPTO_UBICACION'] == department].copy()

    lang_col = grade_cols[grade]['Lenguaje']
    math_col = grade_cols[grade]['Matemáticas']
    n_col = grade_cols[grade]['N']

    df_munic_dept = df_munic_dept[[lang_col, math_col, n_col, 'COLE_MCPIO_UBICACION']].dropna()

    # Get schools in department
    df_schools_dept = df_schools[df_schools['COLE_COD_MCPIO_UBICACION'].astype(str).str[:2] ==
                                   df_munic_dept['MUNI_ID'].astype(str).str[:2].iloc[0] if len(df_munic_dept) > 0 else '']

    total_munic = len(df_munic_dept)
    total_schools = len(df_schools_dept)
    avg_lang = f"{df_munic_dept[lang_col].mean():.3f}" if len(df_munic_dept) > 0 else "N/A"
    avg_math = f"{df_munic_dept[math_col].mean():.3f}" if len(df_munic_dept) > 0 else "N/A"

    # Municipality ranking
    df_munic_dept = df_munic_dept.sort_values(math_col, ascending=True).tail(20)
    rank_fig = go.Figure()
    rank_fig.add_trace(go.Bar(
        y=df_munic_dept['COLE_MCPIO_UBICACION'],
        x=df_munic_dept[lang_col],
        name='Language',
        orientation='h',
        marker_color='lightblue'
    ))
    rank_fig.add_trace(go.Bar(
        y=df_munic_dept['COLE_MCPIO_UBICACION'],
        x=df_munic_dept[math_col],
        name='Math',
        orientation='h',
        marker_color='lightcoral'
    ))
    rank_fig.update_layout(
        title=f'Top 20 Municipalities in {department} - Grade {grade}',
        barmode='group',
        xaxis_title='Score (z-score)',
        height=500
    )

    # Performance scatter
    perf_fig = px.scatter(
        df_munic_dept,
        x=lang_col,
        y=math_col,
        text='COLE_MCPIO_UBICACION',
        title=f'Municipality Performance Map - {department}',
        labels={lang_col: 'Language', math_col: 'Math'}
    )
    perf_fig.update_traces(textposition='top center')

    # Type comparison (using school data)
    if len(df_schools_dept) > 0:
        type_data = df_schools_dept.groupby('COLE_NATURALEZA')[[lang_col, math_col]].mean().reset_index()
        type_fig = go.Figure()
        type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[lang_col], name='Language'))
        type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[math_col], name='Math'))
        type_fig.update_layout(title='Performance by School Type', barmode='group')
    else:
        type_fig = go.Figure()

    return str(total_munic), str(total_schools), avg_lang, avg_math, rank_fig, perf_fig, type_fig


# TAB 3: Municipality callbacks
@app.callback(
    Output('munic-selector', 'options'),
    [Input('munic-dept-selector', 'value')]
)
def update_municipality_dropdown(department):
    """Update municipality dropdown based on selected department"""
    if not department:
        return []

    munics = df_municipalities[df_municipalities['COLE_DEPTO_UBICACION'] == department]['COLE_MCPIO_UBICACION'].dropna().unique()
    return [{'label': m, 'value': m} for m in sorted(munics)]


@app.callback(
    [Output('munic-name', 'children'),
     Output('munic-total-schools', 'children'),
     Output('munic-total-students', 'children'),
     Output('munic-avg-lang', 'children'),
     Output('munic-avg-math', 'children'),
     Output('munic-school-ranking', 'figure'),
     Output('munic-performance-dist', 'figure'),
     Output('munic-school-types', 'figure')],
    [Input('munic-selector', 'value'),
     Input('munic-grade', 'value')]
)
def update_municipality_analysis(municipality, grade):
    """Update municipality analysis"""

    if not municipality:
        empty_fig = go.Figure()
        return "Select a municipality", "0", "0", "N/A", "N/A", empty_fig, empty_fig, empty_fig

    # Get municipality code
    munic_code = df_municipalities[df_municipalities['COLE_MCPIO_UBICACION'] == municipality]['MUNI_ID'].iloc[0] if len(
        df_municipalities[df_municipalities['COLE_MCPIO_UBICACION'] == municipality]) > 0 else None

    if not munic_code:
        empty_fig = go.Figure()
        return municipality, "0", "0", "N/A", "N/A", empty_fig, empty_fig, empty_fig

    # Filter schools in municipality
    df_schools_munic = df_schools[df_schools['COLE_COD_MCPIO_UBICACION'] == munic_code].copy()

    lang_col = grade_cols[grade]['Lenguaje']
    math_col = grade_cols[grade]['Matemáticas']
    n_col = grade_cols[grade]['N']

    df_schools_munic = df_schools_munic[[lang_col, math_col, n_col, 'COLE_NOMBRE_ESTABLECIMIENTO',
                                          'COLE_NATURALEZA', 'COLE_AREA_UBICACION']].dropna()

    total_schools = len(df_schools_munic)
    total_students = int(df_schools_munic[n_col].sum()) if len(df_schools_munic) > 0 else 0
    avg_lang = f"{df_schools_munic[lang_col].mean():.3f}" if len(df_schools_munic) > 0 else "N/A"
    avg_math = f"{df_schools_munic[math_col].mean():.3f}" if len(df_schools_munic) > 0 else "N/A"

    # School ranking
    df_top = df_schools_munic.sort_values(math_col, ascending=True).tail(15)
    rank_fig = go.Figure()
    rank_fig.add_trace(go.Bar(
        y=df_top['COLE_NOMBRE_ESTABLECIMIENTO'].str[:40],
        x=df_top[math_col],
        orientation='h',
        marker_color='lightcoral',
        name='Math Score'
    ))
    rank_fig.update_layout(
        title=f'Top 15 Schools in {municipality} - Grade {grade}',
        xaxis_title='Math Score (z-score)',
        height=500
    )

    # Performance distribution
    dist_fig = px.histogram(
        df_schools_munic,
        x=math_col,
        title=f'Math Score Distribution - {municipality}',
        nbins=30
    )

    # School types
    type_data = df_schools_munic.groupby('COLE_NATURALEZA')[[lang_col, math_col]].mean().reset_index()
    type_fig = go.Figure()
    type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[lang_col], name='Language'))
    type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[math_col], name='Math'))
    type_fig.update_layout(title='Average Performance by School Type', barmode='group')

    return municipality, str(total_schools), f"{total_students:,}", avg_lang, avg_math, rank_fig, dist_fig, type_fig


# TAB 4: School search callbacks
@app.callback(
    Output('school-search-results', 'children'),
    [Input('school-search-input', 'value')]
)
def search_schools(search_term):
    """Search for schools"""

    if not search_term or len(search_term) < 3:
        return html.P("Type at least 3 characters to search...", className="text-muted")

    # Search schools
    df_search = df_schools[df_schools['COLE_NOMBRE_ESTABLECIMIENTO'].str.contains(search_term, case=False, na=False)].copy()

    if len(df_search) == 0:
        return html.P("No schools found", className="text-warning")

    # Select columns to display
    display_cols = ['CODIGO', 'COLE_NOMBRE_ESTABLECIMIENTO', 'COLE_GENERO', 'COLE_NATURALEZA',
                   'COLE_AREA_UBICACION', 'Lenguaje Grado 11', 'Matemáticas Grado 11']

    df_display = df_search[display_cols].head(20)

    # Round numeric columns
    for col in ['Lenguaje Grado 11', 'Matemáticas Grado 11']:
        if col in df_display.columns:
            df_display[col] = df_display[col].round(3)

    return html.Div([
        html.P(f"Found {len(df_search)} schools (showing first 20)"),
        dash_table.DataTable(
            data=df_display.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df_display.columns],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
            ],
            page_size=10
        )
    ])


# TAB 5: Socioeconomic analysis callbacks
@app.callback(
    [Output('socio-main-chart', 'figure'),
     Output('socio-correlation', 'figure'),
     Output('socio-distribution', 'figure')],
    [Input('socio-analysis-type', 'value')]
)
def update_socioeconomic_analysis(analysis_type):
    """Update socioeconomic impact analysis"""

    if len(df_students) == 0:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Student data not available", showarrow=False)
        return empty_fig, empty_fig, empty_fig

    df_socio = df_students.copy()

    if analysis_type == 'estrato':
        # Estrato analysis
        df_plot = df_socio[['fami_estratovivienda', 'punt_matematicas', 'punt_lectura_critica']].dropna()
        df_plot = df_plot[df_plot['fami_estratovivienda'] != 'Sin Estrato']

        avg_by_estrato = df_plot.groupby('fami_estratovivienda')[['punt_matematicas', 'punt_lectura_critica']].mean().reset_index()

        main_fig = go.Figure()
        main_fig.add_trace(go.Bar(x=avg_by_estrato['fami_estratovivienda'],
                                   y=avg_by_estrato['punt_matematicas'],
                                   name='Math', marker_color='lightcoral'))
        main_fig.add_trace(go.Bar(x=avg_by_estrato['fami_estratovivienda'],
                                   y=avg_by_estrato['punt_lectura_critica'],
                                   name='Reading', marker_color='lightblue'))
        main_fig.update_layout(title='Average Scores by Socioeconomic Stratum (Estrato)',
                              barmode='group', xaxis_title='Estrato', yaxis_title='Score')

        # Distribution
        dist_fig = px.box(df_plot, x='fami_estratovivienda', y='punt_matematicas',
                         title='Math Score Distribution by Estrato')

    elif analysis_type == 'education':
        # Parent education
        df_plot = df_socio[['fami_educacionmadre', 'fami_educacionpadre', 'punt_matematicas']].dropna()

        avg_by_edu = df_plot.groupby('fami_educacionmadre')['punt_matematicas'].mean().reset_index()
        avg_by_edu = avg_by_edu.sort_values('punt_matematicas')

        main_fig = go.Figure()
        main_fig.add_trace(go.Bar(x=avg_by_edu['fami_educacionmadre'],
                                   y=avg_by_edu['punt_matematicas'],
                                   marker_color='mediumpurple'))
        main_fig.update_layout(title='Average Math Score by Mother\'s Education Level',
                              xaxis_title='Mother Education', yaxis_title='Math Score')

        dist_fig = px.violin(df_plot, x='fami_educacionmadre', y='punt_matematicas',
                            title='Score Distribution by Mother\'s Education')

    elif analysis_type == 'assets':
        # Home assets
        asset_cols = ['fami_tieneinternet', 'fami_tienecomputador', 'fami_tieneautomovil']
        df_plot = df_socio[asset_cols + ['punt_matematicas']].dropna()

        # Convert to numeric
        for col in asset_cols:
            df_plot[col] = df_plot[col].map({'Si': 1, 'No': 0})

        correlations = df_plot[asset_cols].corrwith(df_plot['punt_matematicas'])

        main_fig = go.Figure()
        main_fig.add_trace(go.Bar(
            x=['Internet', 'Computer', 'Car'],
            y=correlations.values,
            marker_color='teal'
        ))
        main_fig.update_layout(title='Correlation: Home Assets vs Math Score',
                              yaxis_title='Correlation Coefficient')

        # Compare with/without internet
        df_plot_labeled = df_socio[['fami_tieneinternet', 'punt_matematicas']].dropna()
        dist_fig = px.box(df_plot_labeled, x='fami_tieneinternet', y='punt_matematicas',
                         title='Math Scores: With vs Without Internet')

    elif analysis_type == 'index':
        # INSE index
        df_plot = df_socio[['estu_inse_individual', 'punt_matematicas', 'punt_lectura_critica']].dropna()

        main_fig = px.scatter(df_plot.sample(min(5000, len(df_plot))),
                             x='estu_inse_individual', y='punt_matematicas',
                             opacity=0.3,
                             title='Math Score vs Socioeconomic Index (INSE)',
                             trendline='ols')

        dist_fig = px.scatter(df_plot.sample(min(5000, len(df_plot))),
                             x='estu_inse_individual', y='punt_lectura_critica',
                             opacity=0.3,
                             title='Reading Score vs Socioeconomic Index (INSE)',
                             trendline='ols')

    else:  # economic
        df_plot = df_socio[['fami_situacioneconomica', 'punt_matematicas']].dropna()
        avg_by_econ = df_plot.groupby('fami_situacioneconomica')['punt_matematicas'].mean().reset_index()

        main_fig = go.Figure()
        main_fig.add_trace(go.Bar(x=avg_by_econ['fami_situacioneconomica'],
                                   y=avg_by_econ['punt_matematicas'],
                                   marker_color='orange'))
        main_fig.update_layout(title='Average Math Score by Family Economic Situation',
                              xaxis_title='Economic Situation', yaxis_title='Math Score')

        dist_fig = px.box(df_plot, x='fami_situacioneconomica', y='punt_matematicas',
                         title='Math Score Distribution by Economic Situation')

    # Correlation heatmap
    corr_cols = ['punt_matematicas', 'punt_lectura_critica']
    if 'estu_inse_individual' in df_socio.columns:
        corr_data = df_socio[corr_cols + ['estu_inse_individual']].dropna().corr()
        corr_fig = px.imshow(corr_data, text_auto=True, title='Correlation Matrix',
                            color_continuous_scale='RdBu_r')
    else:
        corr_fig = go.Figure()

    return main_fig, corr_fig, dist_fig


# TAB 6: Advanced prediction model callbacks
@app.callback(
    [Output('pred-model-stats', 'children'),
     Output('pred-feature-importance', 'figure'),
     Output('pred-value-added', 'figure'),
     Output('pred-top-schools-table', 'children'),
     Output('pred-bottom-schools-table', 'children')],
    [Input('pred-level', 'value'),
     Input('pred-target', 'value')]
)
def update_prediction_model(level, target):
    """Build and evaluate value-added prediction model"""

    if level == 'student':
        # Student-level prediction
        if len(df_students) == 0:
            return html.P("No student data"), go.Figure(), go.Figure(), html.P("N/A"), html.P("N/A")

        df_model = df_students.copy()

        # Select target
        if target == 'matematicas':
            target_col = 'punt_matematicas'
        elif target == 'lectura':
            target_col = 'punt_lectura_critica'
        else:
            target_col = 'punt_global'

        # Select features
        feature_cols = ['fami_estratovivienda', 'fami_educacionmadre', 'fami_educacionpadre',
                       'fami_tieneinternet', 'fami_tienecomputador', 'estu_genero',
                       'cole_naturaleza', 'cole_area_ubicacion']

        # Prepare data
        df_model = df_model[feature_cols + [target_col, 'cole_nombre_establecimiento']].dropna()

        if len(df_model) < 100:
            return html.P("Insufficient data"), go.Figure(), go.Figure(), html.P("N/A"), html.P("N/A")

        # Encode categorical variables
        X = df_model[feature_cols].copy()
        le_dict = {}
        for col in feature_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            le_dict[col] = le

        y = df_model[target_col]

        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        # Feature importance
        importance_df = pd.DataFrame({
            'Feature': feature_cols,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=True)

        imp_fig = go.Figure(go.Bar(
            x=importance_df['Importance'],
            y=importance_df['Feature'],
            orientation='h',
            marker_color='lightgreen'
        ))
        imp_fig.update_layout(title='Feature Importance', xaxis_title='Importance', height=300)

        # Calculate residuals by school
        df_model['predicted'] = model.predict(X)
        df_model['residual'] = df_model[target_col] - df_model['predicted']

        school_residuals = df_model.groupby('cole_nombre_establecimiento').agg({
            'residual': 'mean',
            target_col: 'mean',
            'predicted': 'mean'
        }).reset_index()

        school_residuals = school_residuals[school_residuals['cole_nombre_establecimiento'].notna()]
        school_residuals = school_residuals.sort_values('residual', ascending=False)

    else:
        # School-level prediction
        df_model = df_schools.copy()

        # Select target
        target_col = 'Matemáticas Grado 11' if target == 'matematicas' else 'Lenguaje Grado 11'

        # Features
        feature_cols = ['COLE_GENERO', 'COLE_NATURALEZA', 'COLE_CARACTER', 'COLE_AREA_UBICACION']

        df_model = df_model[feature_cols + [target_col, 'COLE_NOMBRE_ESTABLECIMIENTO', 'N 11']].dropna()

        if len(df_model) < 100:
            return html.P("Insufficient data"), go.Figure(), go.Figure(), html.P("N/A"), html.P("N/A")

        # Encode
        X = df_model[feature_cols].copy()
        for col in feature_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))

        y = df_model[target_col]

        # Train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        # Feature importance
        importance_df = pd.DataFrame({
            'Feature': feature_cols,
            'Importance': model.feature_importances_
        }).sort_values('Importance', ascending=True)

        imp_fig = go.Figure(go.Bar(
            x=importance_df['Importance'],
            y=importance_df['Feature'],
            orientation='h',
            marker_color='lightgreen'
        ))
        imp_fig.update_layout(title='Feature Importance', xaxis_title='Importance', height=300)

        # Residuals
        df_model['predicted'] = model.predict(X)
        df_model['residual'] = df_model[target_col] - df_model['predicted']

        school_residuals = df_model[['COLE_NOMBRE_ESTABLECIMIENTO', target_col, 'predicted', 'residual', 'N 11']].copy()
        school_residuals = school_residuals.sort_values('residual', ascending=False)

    # Model stats
    stats_content = html.Div([
        html.P([html.Strong("R² Score: "), f"{r2:.4f}"]),
        html.P([html.Strong("MAE: "), f"{mae:.2f}"]),
        html.P([html.Strong("RMSE: "), f"{rmse:.2f}"]),
        html.P([html.Strong("Samples: "), f"{len(df_model):,}"]),
        html.Hr(),
        html.P("A positive residual means the school/student performed BETTER than expected based on socioeconomic factors.",
              className="small text-muted")
    ])

    # Value-added scatter
    va_fig = px.scatter(
        school_residuals.head(100),
        x='predicted',
        y=target_col if level == 'student' else target_col,
        size='N 11' if level == 'school' else None,
        hover_name='COLE_NOMBRE_ESTABLECIMIENTO' if level == 'school' else 'cole_nombre_establecimiento',
        title='Actual vs Predicted Performance (Value-Added Analysis)',
        labels={'predicted': 'Predicted Score', target_col: 'Actual Score'}
    )
    va_fig.add_shape(
        type="line", line=dict(color='red', dash='dash'),
        x0=school_residuals['predicted'].min(), y0=school_residuals['predicted'].min(),
        x1=school_residuals['predicted'].max(), y1=school_residuals['predicted'].max()
    )

    # Top schools (positive residuals)
    top_schools = school_residuals.head(10)[['COLE_NOMBRE_ESTABLECIMIENTO' if level == 'school' else 'cole_nombre_establecimiento',
                                              'residual']].copy()
    top_schools.columns = ['School', 'Value Added (Residual)']
    top_schools['Value Added (Residual)'] = top_schools['Value Added (Residual)'].round(3)

    top_table = dash_table.DataTable(
        data=top_schools.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in top_schools.columns],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgreen', 'fontWeight': 'bold'},
    )

    # Bottom schools (negative residuals)
    bottom_schools = school_residuals.tail(10)[['COLE_NOMBRE_ESTABLECIMIENTO' if level == 'school' else 'cole_nombre_establecimiento',
                                                 'residual']].copy()
    bottom_schools.columns = ['School', 'Value Added (Residual)']
    bottom_schools['Value Added (Residual)'] = bottom_schools['Value Added (Residual)'].round(3)

    bottom_table = dash_table.DataTable(
        data=bottom_schools.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in bottom_schools.columns],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightcoral', 'fontWeight': 'bold'},
    )

    return stats_content, imp_fig, va_fig, top_table, bottom_table


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("SABER Educational Results Dashboard - Government Analytics Platform")
    print("="*70)
    print(f"\nData loaded successfully:")
    print(f"  - Schools: {len(df_schools):,}")
    print(f"  - Municipalities: {len(df_municipalities):,}")
    print(f"  - Student records: {len(df_students):,}")
    print(f"\nStarting server...")
    print("Open http://127.0.0.1:8050/ in your browser")
    print("="*70 + "\n")

    app.run_server(debug=True, host='0.0.0.0', port=8050)
