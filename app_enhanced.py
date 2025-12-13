"""
Enhanced Dash App for Colombian SABER School Results Analysis
Designed for governmental agencies to analyze educational performance at multiple levels

Authentication:
- Public pages: National, Department, Municipality overviews (aggregate data)
- Protected pages: School details, Socioeconomic, Advanced Analytics, Policy KPIs (corporate login required)
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
import glob
import os
warnings.filterwarnings('ignore')

# Import enhanced authentication
from auth_integration_enhanced import (
    setup_authentication,
    add_auth_callbacks,
    get_auth_layout,
    create_auth_header,
    is_tab_accessible,
    create_login_required_message,
    AUTH_ENABLED
)

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "SABER Results - Government Dashboard"
server = app.server

# Setup authentication (if enabled via ENABLE_AUTH environment variable)
login_manager = setup_authentication(app)

# Allow callback exceptions for dynamic routing
app.config.suppress_callback_exceptions = True

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

# All SABER 11 subjects
SABER11_SUBJECTS = {
    'lectura_critica': 'Lectura Crítica',
    'matematicas': 'Matemáticas',
    'c_naturales': 'Ciencias Naturales',
    'sociales_ciudadanas': 'Sociales y Ciudadanas',
    'ingles': 'Inglés',
    'global': 'Puntaje Global'
}

def load_saber11_2024_data():
    """
    Load 2024 Saber 11 data from Parquet files
    Combines period 1 and period 2 data
    """
    all_data = []

    # Try to load 2024 Parquet files
    parquet_files = [
        'Examen_Saber_11_SS_20241.parquet',
        'Examen_Saber_11_SS_20242.parquet'
    ]

    for file in parquet_files:
        if os.path.exists(file):
            try:
                print(f"Loading {file}...")
                df = pd.read_parquet(file)
                all_data.append(df)
                print(f"  ✓ Loaded {len(df):,} records from {file}")
            except Exception as e:
                print(f"  ✗ Error loading {file}: {e}")

    # If no 2024 files found, try other Parquet files
    if not all_data:
        print("2024 Parquet files not found, searching for other Parquet files...")
        for file in glob.glob('*.parquet'):
            try:
                print(f"Loading {file}...")
                df = pd.read_parquet(file)
                all_data.append(df)
                print(f"  ✓ Loaded {len(df):,} records")
            except Exception as e:
                print(f"  ✗ Error loading {file}: {e}")

    # If still no data, try CSV/ZIP files
    if not all_data:
        print("No Parquet files found, trying CSV files...")
        csv_files = ['Saber_11__2017-1.csv', 'ICFES_2019.csv']
        for file in csv_files:
            if os.path.exists(file):
                try:
                    print(f"Loading {file}...")
                    df = pd.read_csv(file, low_memory=False)
                    all_data.append(df)
                    print(f"  ✓ Loaded {len(df):,} records")
                    break  # Load only one CSV file to avoid memory issues
                except Exception as e:
                    print(f"  ✗ Error loading {file}: {e}")

        # Try ZIP files
        for file in glob.glob('Saber_11*.zip'):
            try:
                print(f"Loading {file}...")
                df = pd.read_csv(file, compression='zip', low_memory=False)
                all_data.append(df)
                print(f"  ✓ Loaded {len(df):,} records")
                break
            except Exception as e:
                print(f"  ✗ Error loading {file}: {e}")

    if not all_data:
        print("⚠️  No Saber 11 data files found!")
        return pd.DataFrame()

    # Combine all data
    df_combined = pd.concat(all_data, ignore_index=True)

    # Standardize column names to uppercase
    df_combined.columns = df_combined.columns.str.upper()

    # Create period/year info
    if 'PERIODO' in df_combined.columns:
        df_combined['YEAR'] = df_combined['PERIODO'].apply(
            lambda x: int(str(int(x))[:4]) if pd.notna(x) else None
        )

    print(f"\n✅ Total loaded: {len(df_combined):,} student records")
    if 'YEAR' in df_combined.columns:
        years = sorted(df_combined['YEAR'].dropna().unique())
        print(f"📅 Years available: {years}")

    return df_combined


def aggregate_by_school(df_students):
    """
    Aggregate student-level data to school level for all subjects
    """
    # Identify score columns
    score_cols = []
    for subj_key in SABER11_SUBJECTS.keys():
        col_name = f'PUNT_{subj_key.upper()}'
        if col_name in df_students.columns:
            score_cols.append(col_name)

    if not score_cols:
        print("⚠️  No score columns found in data")
        return pd.DataFrame()

    # Group by columns
    groupby_cols = []
    possible_groupby = [
        'COLE_COD_DANE_ESTABLECIMIENTO',
        'COLE_NOMBRE_ESTABLECIMIENTO',
        'COLE_DEPTO_UBICACION',
        'COLE_MCPIO_UBICACION',
        'COLE_NATURALEZA',
        'COLE_AREA_UBICACION',
        'COLE_GENERO',
        'COLE_CARACTER'
    ]

    for col in possible_groupby:
        if col in df_students.columns:
            groupby_cols.append(col)

    if not groupby_cols:
        print("⚠️  No groupby columns found")
        return pd.DataFrame()

    # Aggregate
    agg_dict = {col: ['mean', 'count', 'std'] for col in score_cols}

    df_agg = df_students[groupby_cols + score_cols].groupby(groupby_cols).agg(agg_dict)
    df_agg.columns = ['_'.join(col).strip('_') for col in df_agg.columns.values]
    df_agg = df_agg.reset_index()

    print(f"✅ Aggregated to {len(df_agg):,} schools")

    return df_agg


def aggregate_by_municipality(df_students):
    """
    Aggregate student-level data to municipality level
    """
    # Identify score columns
    score_cols = []
    for subj_key in SABER11_SUBJECTS.keys():
        col_name = f'PUNT_{subj_key.upper()}'
        if col_name in df_students.columns:
            score_cols.append(col_name)

    if not score_cols:
        return pd.DataFrame()

    # Group by columns
    groupby_cols = []
    possible_groupby = [
        'COLE_DEPTO_UBICACION',
        'COLE_MCPIO_UBICACION',
        'COLE_COD_MCPIO_UBICACION'
    ]

    for col in possible_groupby:
        if col in df_students.columns:
            groupby_cols.append(col)

    if not groupby_cols:
        return pd.DataFrame()

    # Aggregate
    agg_dict = {col: ['mean', 'count', 'std'] for col in score_cols}

    df_agg = df_students[groupby_cols + score_cols].groupby(groupby_cols).agg(agg_dict)
    df_agg.columns = ['_'.join(col).strip('_') for col in df_agg.columns.values]
    df_agg = df_agg.reset_index()

    print(f"✅ Aggregated to {len(df_agg):,} municipalities")

    return df_agg


# Load all datasets
print("="*70)
print("LOADING SABER 11 DATA WITH ALL SUBJECTS")
print("="*70)

# Load student-level data from 2024 Parquet files
df_students = load_saber11_2024_data()

# Aggregate to school and municipality levels
df_schools = aggregate_by_school(df_students)
df_municipalities = aggregate_by_municipality(df_students)

print(f"\n📊 Data Summary:")
print(f"  - Students: {len(df_students):,}")
print(f"  - Schools: {len(df_schools):,}")
print(f"  - Municipalities: {len(df_municipalities):,}")

# Create helper data structures for all subjects
grades = ['11']  # Saber 11 only has grade 11
subjects_list = list(SABER11_SUBJECTS.values())

# Build grade_cols structure compatible with existing callbacks
grade_cols = {}
for grade in grades:
    grade_cols[grade] = {}

    # Map all available score columns
    score_cols_found = []
    for col in df_schools.columns:
        if col.endswith('_mean') and col.startswith('PUNT_'):
            # Extract subject name
            base_col = col.replace('_mean', '')
            score_cols_found.append(base_col)

            # Add to grade_cols with friendly name
            if 'LECTURA_CRITICA' in base_col:
                grade_cols[grade]['Lenguaje'] = col  # Keep 'Lenguaje' for backward compatibility
                grade_cols[grade]['Lectura Crítica'] = col
            elif 'MATEMATICAS' in base_col:
                grade_cols[grade]['Matemáticas'] = col
            elif 'C_NATURALES' in base_col:
                grade_cols[grade]['Ciencias Naturales'] = col
            elif 'SOCIALES_CIUDADANAS' in base_col:
                grade_cols[grade]['Sociales y Ciudadanas'] = col
            elif 'INGLES' in base_col:
                grade_cols[grade]['Inglés'] = col
            elif 'GLOBAL' in base_col:
                grade_cols[grade]['Global'] = col

    # Also need count columns
    for col in df_schools.columns:
        if col.endswith('_count') and col.startswith('PUNT_'):
            # Find the first score column to use for 'N'
            if 'LECTURA_CRITICA' in col:
                grade_cols[grade]['N'] = col
                break
            elif 'MATEMATICAS' in col:
                grade_cols[grade]['N'] = col
                break

# Print available subjects for debugging
print(f"\n📚 Available subjects for Grade {grades[0]}:")
for subj, col in grade_cols['11'].items():
    if subj != 'N':
        print(f"  - {subj}: {col}")

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
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
], fluid=True)


def create_main_dashboard():
    """Create the main dashboard layout"""
    auth_header = create_auth_header()

    return dbc.Container([
        # Auth header (login/logout buttons)
        auth_header if auth_header else html.Div(),

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
                                        html.Label("Subject 1:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-subject1',
                                            options=[
                                                {'label': 'Lectura Crítica', 'value': 'Lectura Crítica'},
                                                {'label': 'Matemáticas', 'value': 'Matemáticas'},
                                                {'label': 'Ciencias Naturales', 'value': 'Ciencias Naturales'},
                                                {'label': 'Sociales y Ciudadanas', 'value': 'Sociales y Ciudadanas'},
                                                {'label': 'Inglés', 'value': 'Inglés'},
                                                {'label': 'Global', 'value': 'Global'}
                                            ],
                                            value='Matemáticas',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Subject 2:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-subject2',
                                            options=[
                                                {'label': 'Lectura Crítica', 'value': 'Lectura Crítica'},
                                                {'label': 'Matemáticas', 'value': 'Matemáticas'},
                                                {'label': 'Ciencias Naturales', 'value': 'Ciencias Naturales'},
                                                {'label': 'Sociales y Ciudadanas', 'value': 'Sociales y Ciudadanas'},
                                                {'label': 'Inglés', 'value': 'Inglés'},
                                                {'label': 'Global', 'value': 'Global'}
                                            ],
                                            value='Lectura Crítica',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("School Type:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-naturaleza',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': n, 'value': n} for n in naturaleza_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Area:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-area',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': a, 'value': a} for a in area_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
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
                                html.H3(id='overview-avg-subject1', className="text-center text-info"),
                                html.P(id='overview-avg-subject1-label', className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='overview-avg-subject2', className="text-center text-warning"),
                                html.P(id='overview-avg-subject2-label', className="text-center text-muted")
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
                            dbc.CardHeader(html.H5("Department Selection & Filters")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Department:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-selector',
                                            options=[{'label': d, 'value': d} for d in departments],
                                            value=departments[0] if departments else None,
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Subject 1:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-subject1',
                                            options=[
                                                {'label': 'Lectura Crítica', 'value': 'Lectura Crítica'},
                                                {'label': 'Matemáticas', 'value': 'Matemáticas'},
                                                {'label': 'Ciencias Naturales', 'value': 'Ciencias Naturales'},
                                                {'label': 'Sociales y Ciudadanas', 'value': 'Sociales y Ciudadanas'},
                                                {'label': 'Inglés', 'value': 'Inglés'},
                                                {'label': 'Global', 'value': 'Global'}
                                            ],
                                            value='Matemáticas',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Subject 2:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-subject2',
                                            options=[
                                                {'label': 'Lectura Crítica', 'value': 'Lectura Crítica'},
                                                {'label': 'Matemáticas', 'value': 'Matemáticas'},
                                                {'label': 'Ciencias Naturales', 'value': 'Ciencias Naturales'},
                                                {'label': 'Sociales y Ciudadanas', 'value': 'Sociales y Ciudadanas'},
                                                {'label': 'Inglés', 'value': 'Inglés'},
                                                {'label': 'Global', 'value': 'Global'}
                                            ],
                                            value='Lectura Crítica',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("School Type:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-naturaleza',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': n, 'value': n} for n in naturaleza_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
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
                                html.H3(id='dept-avg-subject1', className="text-center"),
                                html.P(id='dept-avg-subject1-label', className="text-center text-muted")
                            ])
                        ])
                    ], md=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3(id='dept-avg-subject2', className="text-center"),
                                html.P(id='dept-avg-subject2-label', className="text-center text-muted")
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
                                                {'label': 'Lectura Crítica', 'value': 'lectura_critica'},
                                                {'label': 'Matemáticas', 'value': 'matematicas'},
                                                {'label': 'Ciencias Naturales', 'value': 'c_naturales'},
                                                {'label': 'Sociales y Ciudadanas', 'value': 'sociales_ciudadanas'},
                                                {'label': 'Inglés', 'value': 'ingles'},
                                                {'label': 'Puntaje Global', 'value': 'global'}
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

        # TAB 7: Policy KPIs Dashboard
        dbc.Tab(label="📋 Policy KPIs", tab_id="tab-policy-kpis", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Policy Dashboard - Key Performance Indicators"),
                        html.P("Data-driven metrics for resource allocation and policy decisions", className="text-muted"),
                    ])
                ], className="mb-4"),

                # Level Selection
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Analysis Level")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Select Level:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-level',
                                            options=[
                                                {'label': '🇨🇴 National', 'value': 'national'},
                                                {'label': '🗺️ Department', 'value': 'department'},
                                                {'label': '🏘️ Municipality', 'value': 'municipality'}
                                            ],
                                            value='national',
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Department (if applicable):", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-department',
                                            options=[{'label': d, 'value': d} for d in departments],
                                            value=departments[0] if departments else None,
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Municipality (if applicable):", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-municipality',
                                            options=[],
                                            value=None,
                                            clearable=False
                                        )
                                    ], md=4),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                # KPI Summary Cards
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("🎯 Equity Gap Index"),
                            dbc.CardBody([
                                html.H3(id='kpi-equity-gap', className="text-center"),
                                html.P(id='kpi-equity-gap-desc', className="text-center text-muted small"),
                                html.Div(id='kpi-equity-gap-indicator', className="text-center")
                            ])
                        ])
                    ], md=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("📈 Average Global Score"),
                            dbc.CardBody([
                                html.H3(id='kpi-avg-global', className="text-center"),
                                html.P(id='kpi-avg-global-desc', className="text-center text-muted small"),
                                html.Div(id='kpi-avg-global-indicator', className="text-center")
                            ])
                        ])
                    ], md=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("⭐ Value-Added Schools %"),
                            dbc.CardBody([
                                html.H3(id='kpi-value-added-pct', className="text-center"),
                                html.P(id='kpi-value-added-pct-desc', className="text-center text-muted small"),
                                html.Div(id='kpi-value-added-indicator', className="text-center")
                            ])
                        ])
                    ], md=4),
                ], className="mb-4"),

                # Context-Specific KPIs
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Context-Specific KPIs")),
                            dbc.CardBody([
                                html.Div(id='kpi-context-cards')
                            ])
                        ])
                    ])
                ], className="mb-4"),

                # Detailed Analysis
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Equity Analysis")),
                            dbc.CardBody([
                                dcc.Graph(id='kpi-equity-chart', style={'height': '400px'})
                            ])
                        ])
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Performance Gaps")),
                            dbc.CardBody([
                                dcc.Graph(id='kpi-gaps-chart', style={'height': '400px'})
                            ])
                        ])
                    ], md=6),
                ], className="mb-4"),

                # Priority Areas for Intervention
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("🔴 Priority Areas for Intervention")),
                            dbc.CardBody([
                                html.Div(id='kpi-priority-table')
                            ])
                        ])
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("⭐ Best Practices to Replicate")),
                            dbc.CardBody([
                                html.Div(id='kpi-best-practices-table')
                            ])
                        ])
                    ], md=6),
                ], className="mb-4"),

                # Recommendations
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("💡 Policy Recommendations")),
                            dbc.CardBody([
                                html.Div(id='kpi-recommendations')
                            ])
                        ])
                    ])
                ]),
            ], className="p-3")
        ]),
    ]),

    ], fluid=True)


# ============================================================================
# URL ROUTING & AUTHENTICATION
# ============================================================================

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route pages and handle authentication"""
    # Check if it's an auth page (login, register)
    auth_layout = get_auth_layout(pathname)
    if auth_layout:
        return auth_layout

    # Default to main dashboard
    return create_main_dashboard()


# Add authentication callbacks (login, logout, registration)
add_auth_callbacks(app)


# Tab access control
@app.callback(
    Output('main-tabs', 'active_tab'),
    [Input('main-tabs', 'active_tab')],
    prevent_initial_call=True
)
def check_tab_access(active_tab):
    """Check if user has access to the selected tab"""
    if not active_tab:
        return 'tab-overview'

    accessible, message = is_tab_accessible(active_tab)

    if not accessible and message == 'login_required':
        # Redirect to overview and let the user know (through tab content)
        return active_tab  # Keep the tab selection to show login message

    return active_tab


# ============================================================================
# CALLBACKS
# ============================================================================

# TAB 1: Overview callbacks
@app.callback(
    [Output('overview-total-schools', 'children'),
     Output('overview-total-students', 'children'),
     Output('overview-avg-subject1', 'children'),
     Output('overview-avg-subject1-label', 'children'),
     Output('overview-avg-subject2', 'children'),
     Output('overview-avg-subject2-label', 'children'),
     Output('overview-scatter', 'figure'),
     Output('overview-distribution', 'figure'),
     Output('overview-grade-comparison', 'figure')],
    [Input('overview-subject1', 'value'),
     Input('overview-subject2', 'value'),
     Input('overview-naturaleza', 'value'),
     Input('overview-area', 'value')]
)
def update_overview(subject1, subject2, naturaleza, area):
    """Update overview tab visualizations"""

    grade = '11'  # All data is grade 11

    # Filter data
    df = df_schools.copy()

    if naturaleza != 'ALL':
        df = df[df['COLE_NATURALEZA'] == naturaleza]
    if area != 'ALL':
        df = df[df['COLE_AREA_UBICACION'] == area]

    # Get columns for selected subjects
    if subject1 not in grade_cols[grade]:
        subject1 = 'Matemáticas'  # Fallback
    if subject2 not in grade_cols[grade]:
        subject2 = 'Lectura Crítica'  # Fallback

    subject1_col = grade_cols[grade][subject1]
    subject2_col = grade_cols[grade][subject2]
    n_col = grade_cols[grade]['N']

    # Filter out missing values
    required_cols = [subject1_col, subject2_col, n_col]
    meta_cols = ['COLE_NATURALEZA', 'COLE_AREA_UBICACION']
    available_cols = [c for c in required_cols + meta_cols if c in df.columns]

    df_plot = df[available_cols].dropna(subset=[col for col in [subject1_col, subject2_col] if col in df.columns])

    # Calculate stats
    total_schools = len(df_plot)
    total_students = int(df_plot[n_col].sum()) if len(df_plot) > 0 and n_col in df_plot.columns else 0
    avg_subject1 = f"{df_plot[subject1_col].mean():.3f}" if len(df_plot) > 0 and subject1_col in df_plot.columns else "N/A"
    avg_subject2 = f"{df_plot[subject2_col].mean():.3f}" if len(df_plot) > 0 and subject2_col in df_plot.columns else "N/A"

    # Scatter plot - Subject1 vs Subject2
    if subject1_col in df_plot.columns and subject2_col in df_plot.columns and subject1_col != subject2_col:
        scatter_fig = px.scatter(
            df_plot,
            x=subject1_col,
            y=subject2_col,
            size=n_col if n_col in df_plot.columns else None,
            color='COLE_NATURALEZA' if 'COLE_NATURALEZA' in df_plot.columns else None,
            hover_data=['COLE_AREA_UBICACION'] if 'COLE_AREA_UBICACION' in df_plot.columns else None,
            title=f'{subject1} vs {subject2}',
            labels={subject1_col: subject1, subject2_col: subject2},
            opacity=0.6
        )
        scatter_fig.add_shape(
            type="line", line=dict(dash='dash', color='gray'),
            x0=df_plot[subject1_col].min(), y0=df_plot[subject1_col].min(),
            x1=df_plot[subject1_col].max(), y1=df_plot[subject1_col].max()
        )
    else:
        # If same subject or missing columns, show distribution
        scatter_fig = px.histogram(
            df_plot,
            x=subject1_col if subject1_col in df_plot.columns else subject2_col,
            nbins=50,
            title=f'{subject1} Distribution'
        )

    # Distribution - Overlapping histograms
    dist_fig = go.Figure()
    if subject1_col in df_plot.columns:
        dist_fig.add_trace(
            go.Histogram(
                x=df_plot[subject1_col],
                name=subject1,
                nbinsx=50,
                marker_color='rgba(0, 123, 255, 0.6)',  # Blue with transparency
                opacity=0.7
            )
        )
    if subject2_col in df_plot.columns:
        dist_fig.add_trace(
            go.Histogram(
                x=df_plot[subject2_col],
                name=subject2,
                nbinsx=50,
                marker_color='rgba(255, 99, 71, 0.6)',  # Red with transparency
                opacity=0.7
            )
        )
    dist_fig.update_layout(
        barmode='overlay',  # Overlay the histograms
        title_text=f'Score Distribution: {subject1} vs {subject2}',
        xaxis_title='Score',
        yaxis_title='Frequency',
        showlegend=True,
        legend=dict(x=0.7, y=0.95)
    )

    # Comparison chart - Both subjects
    comparison_fig = go.Figure()
    if subject1_col in df_plot.columns:
        comparison_fig.add_trace(go.Box(y=df_plot[subject1_col], name=subject1, marker_color='lightblue'))
    if subject2_col in df_plot.columns:
        comparison_fig.add_trace(go.Box(y=df_plot[subject2_col], name=subject2, marker_color='lightcoral'))
    comparison_fig.update_layout(title=f'Score Comparison: {subject1} vs {subject2}', yaxis_title='Score')

    return (f"{total_schools:,}", f"{total_students:,}",
            avg_subject1, f"Avg {subject1}",
            avg_subject2, f"Avg {subject2}",
            scatter_fig, dist_fig, comparison_fig)


# TAB 2: Department callbacks
@app.callback(
    [Output('dept-total-munic', 'children'),
     Output('dept-total-schools', 'children'),
     Output('dept-avg-subject1', 'children'),
     Output('dept-avg-subject1-label', 'children'),
     Output('dept-avg-subject2', 'children'),
     Output('dept-avg-subject2-label', 'children'),
     Output('dept-municipality-ranking', 'figure'),
     Output('dept-performance-map', 'figure'),
     Output('dept-type-comparison', 'figure')],
    [Input('dept-selector', 'value'),
     Input('dept-subject1', 'value'),
     Input('dept-subject2', 'value'),
     Input('dept-naturaleza', 'value')]
)
def update_department(department, subject1, subject2, naturaleza):
    """Update department analysis"""

    grade = '11'  # All data is grade 11

    if not department:
        empty_fig = go.Figure()
        return "0", "0", "N/A", "Subject 1", "N/A", "Subject 2", empty_fig, empty_fig, empty_fig

    # Filter municipalities in department
    df_munic_dept = df_municipalities[df_municipalities['COLE_DEPTO_UBICACION'] == department].copy()

    # Get subject columns
    if subject1 not in grade_cols[grade]:
        subject1 = 'Matemáticas'  # Fallback
    if subject2 not in grade_cols[grade]:
        subject2 = 'Lectura Crítica'  # Fallback

    subject1_col = grade_cols[grade][subject1]
    subject2_col = grade_cols[grade][subject2]
    n_col = grade_cols[grade]['N']

    # Filter to available columns
    required_cols = [c for c in [subject1_col, subject2_col, n_col, 'COLE_MCPIO_UBICACION'] if c in df_munic_dept.columns]
    df_munic_dept = df_munic_dept[required_cols].dropna()

    # Get schools in department
    df_schools_dept = df_schools[df_schools['COLE_DEPTO_UBICACION'] == department].copy() if 'COLE_DEPTO_UBICACION' in df_schools.columns else df_schools.copy()

    # Apply school type filter
    if naturaleza != 'ALL' and 'COLE_NATURALEZA' in df_schools_dept.columns:
        df_schools_dept = df_schools_dept[df_schools_dept['COLE_NATURALEZA'] == naturaleza]

    total_munic = len(df_munic_dept)
    total_schools = len(df_schools_dept)
    avg_subject1 = f"{df_munic_dept[subject1_col].mean():.3f}" if len(df_munic_dept) > 0 and subject1_col in df_munic_dept.columns else "N/A"
    avg_subject2 = f"{df_munic_dept[subject2_col].mean():.3f}" if len(df_munic_dept) > 0 and subject2_col in df_munic_dept.columns else "N/A"

    # Municipality ranking - sort by subject1 column
    if subject1_col in df_munic_dept.columns:
        df_munic_sorted = df_munic_dept.sort_values(subject1_col, ascending=True).tail(20)
    else:
        df_munic_sorted = df_munic_dept.tail(20)

    rank_fig = go.Figure()
    if 'COLE_MCPIO_UBICACION' in df_munic_sorted.columns:
        if subject1_col in df_munic_sorted.columns:
            rank_fig.add_trace(go.Bar(
                y=df_munic_sorted['COLE_MCPIO_UBICACION'],
                x=df_munic_sorted[subject1_col],
                name=subject1,
                orientation='h',
                marker_color='lightblue'
            ))
        if subject2_col in df_munic_sorted.columns:
            rank_fig.add_trace(go.Bar(
                y=df_munic_sorted['COLE_MCPIO_UBICACION'],
                x=df_munic_sorted[subject2_col],
                name=subject2,
                orientation='h',
                marker_color='lightcoral'
            ))
    rank_fig.update_layout(
        title=f'Top 20 Municipalities in {department} - {subject1} vs {subject2}',
        barmode='group',
        xaxis_title='Score',
        height=500
    )

    # Performance scatter
    if 'COLE_MCPIO_UBICACION' in df_munic_sorted.columns and subject1_col in df_munic_sorted.columns and subject2_col in df_munic_sorted.columns:
        perf_fig = px.scatter(
            df_munic_sorted,
            x=subject1_col,
            y=subject2_col,
            text='COLE_MCPIO_UBICACION',
            title=f'Municipality Performance Map - {department}',
            labels={subject1_col: subject1, subject2_col: subject2}
        )
        perf_fig.update_traces(textposition='top center')
    else:
        perf_fig = go.Figure()

    # Type comparison (using school data)
    if len(df_schools_dept) > 0 and 'COLE_NATURALEZA' in df_schools_dept.columns:
        available_score_cols = [c for c in [subject1_col, subject2_col] if c in df_schools_dept.columns]
        if available_score_cols:
            type_data = df_schools_dept.groupby('COLE_NATURALEZA')[available_score_cols].mean().reset_index()
            type_fig = go.Figure()
            if subject1_col in type_data.columns:
                type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[subject1_col], name=subject1))
            if subject2_col in type_data.columns:
                type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[subject2_col], name=subject2))
            type_fig.update_layout(title=f'Performance by School Type: {subject1} vs {subject2}', barmode='group')
        else:
            type_fig = go.Figure()
    else:
        type_fig = go.Figure()

    return (str(total_munic), str(total_schools),
            avg_subject1, f"Avg {subject1}",
            avg_subject2, f"Avg {subject2}",
            rank_fig, perf_fig, type_fig)


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
    # Check access for protected tab
    accessible, message = is_tab_accessible('tab-school')
    if not accessible:
        return create_login_required_message("School Analysis")

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
    # Check access for protected tab
    accessible, message = is_tab_accessible('tab-socioeconomic')
    if not accessible:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="🔒 Login required for Socioeconomic Analysis",
                                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return empty_fig, empty_fig, empty_fig

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
    # Check access for protected tab
    accessible, message = is_tab_accessible('tab-prediction')
    if not accessible:
        login_msg = create_login_required_message("Advanced Analytics")
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="🔒 Login required for Advanced Analytics",
                                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return login_msg, empty_fig, empty_fig, html.P("N/A"), html.P("N/A")

    if level == 'student':
        # Student-level prediction
        if len(df_students) == 0:
            return html.P("No student data"), go.Figure(), go.Figure(), html.P("N/A"), html.P("N/A")

        df_model = df_students.copy()

        # Select target column based on subject
        target_mapping = {
            'lectura_critica': 'PUNT_LECTURA_CRITICA',
            'matematicas': 'PUNT_MATEMATICAS',
            'c_naturales': 'PUNT_C_NATURALES',
            'sociales_ciudadanas': 'PUNT_SOCIALES_CIUDADANAS',
            'ingles': 'PUNT_INGLES',
            'global': 'PUNT_GLOBAL'
        }
        target_col = target_mapping.get(target, 'PUNT_MATEMATICAS')

        # Check if column exists (case insensitive)
        if target_col not in df_model.columns:
            # Try lowercase version
            target_col = target_col.lower()
            if target_col not in df_model.columns:
                # Try to find any matching column
                matching_cols = [c for c in df_model.columns if target.upper() in c.upper()]
                if matching_cols:
                    target_col = matching_cols[0]
                else:
                    return html.P(f"Target column not found: {target}"), go.Figure(), go.Figure(), html.P("N/A"), html.P("N/A")

        # Select features (handle case sensitivity)
        possible_features = {
            'fami_estratovivienda': ['FAMI_ESTRATOVIVIENDA', 'fami_estratovivienda'],
            'fami_educacionmadre': ['FAMI_EDUCACIONMADRE', 'fami_educacionmadre'],
            'fami_educacionpadre': ['FAMI_EDUCACIONPADRE', 'fami_educacionpadre'],
            'fami_tieneinternet': ['FAMI_TIENEINTERNET', 'fami_tieneinternet'],
            'fami_tienecomputador': ['FAMI_TIENECOMPUTADOR', 'fami_tienecomputador'],
            'estu_genero': ['ESTU_GENERO', 'estu_genero'],
            'cole_naturaleza': ['COLE_NATURALEZA', 'cole_naturaleza'],
            'cole_area_ubicacion': ['COLE_AREA_UBICACION', 'cole_area_ubicacion']
        }

        feature_cols = []
        for key, variants in possible_features.items():
            for variant in variants:
                if variant in df_model.columns:
                    feature_cols.append(variant)
                    break

        # School name column
        school_col = 'COLE_NOMBRE_ESTABLECIMIENTO' if 'COLE_NOMBRE_ESTABLECIMIENTO' in df_model.columns else 'cole_nombre_establecimiento'

        # Prepare data
        required_cols = feature_cols + [target_col]
        if school_col in df_model.columns:
            required_cols.append(school_col)

        df_model = df_model[required_cols].dropna()

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

        if school_col in df_model.columns:
            school_residuals = df_model.groupby(school_col).agg({
                'residual': 'mean',
                target_col: 'mean',
                'predicted': 'mean'
            }).reset_index()

            school_residuals = school_residuals[school_residuals[school_col].notna()]
            school_residuals = school_residuals.sort_values('residual', ascending=False)
        else:
            school_residuals = pd.DataFrame()

    else:
        # School-level prediction
        df_model = df_schools.copy()

        # Select target column - use grade_cols mapping
        target_mapping = {
            'lectura_critica': 'Lenguaje',  # Maps to grade_cols
            'matematicas': 'Matemáticas',
            'c_naturales': 'Ciencias Naturales',
            'sociales_ciudadanas': 'Sociales y Ciudadanas',
            'ingles': 'Inglés',
            'global': 'Global'
        }

        subj_key = target_mapping.get(target, 'Matemáticas')
        if subj_key in grade_cols['11']:
            target_col = grade_cols['11'][subj_key]
        else:
            return html.P(f"Subject not available: {subj_key}"), go.Figure(), go.Figure(), html.P("N/A"), html.P("N/A")

        # Features
        feature_cols = []
        possible_features = ['COLE_GENERO', 'COLE_NATURALEZA', 'COLE_CARACTER', 'COLE_AREA_UBICACION']
        for col in possible_features:
            if col in df_model.columns:
                feature_cols.append(col)

        # Count column
        n_col = grade_cols['11'].get('N', None)
        school_col = 'COLE_NOMBRE_ESTABLECIMIENTO' if 'COLE_NOMBRE_ESTABLECIMIENTO' in df_model.columns else None

        # Prepare columns list
        required_cols = feature_cols + [target_col]
        if n_col:
            required_cols.append(n_col)
        if school_col:
            required_cols.append(school_col)

        df_model = df_model[required_cols].dropna()

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

        result_cols = [target_col, 'predicted', 'residual']
        if school_col:
            result_cols.insert(0, school_col)
        if n_col:
            result_cols.append(n_col)

        school_residuals = df_model[result_cols].copy()
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

    # Determine school column name
    if level == 'school':
        hover_col = school_col if school_col else None
        size_col = n_col if n_col else None
    else:
        # Student level - use the school_col variable we set earlier
        hover_col = school_col if school_col in school_residuals.columns else None
        size_col = None

    # Value-added scatter
    scatter_kwargs = {
        'data_frame': school_residuals.head(100),
        'x': 'predicted',
        'y': target_col,
        'title': 'Actual vs Predicted Performance (Value-Added Analysis)',
        'labels': {'predicted': 'Predicted Score', target_col: 'Actual Score'}
    }
    if size_col and size_col in school_residuals.columns:
        scatter_kwargs['size'] = size_col
    if hover_col and hover_col in school_residuals.columns:
        scatter_kwargs['hover_name'] = hover_col

    va_fig = px.scatter(**scatter_kwargs)
    va_fig.add_shape(
        type="line", line=dict(color='red', dash='dash'),
        x0=school_residuals['predicted'].min(), y0=school_residuals['predicted'].min(),
        x1=school_residuals['predicted'].max(), y1=school_residuals['predicted'].max()
    )

    # Top schools (positive residuals)
    top_cols = ['residual']
    if hover_col and hover_col in school_residuals.columns:
        top_cols.insert(0, hover_col)

    top_schools = school_residuals.head(10)[top_cols].copy()
    if len(top_cols) == 2:
        top_schools.columns = ['School', 'Value Added (Residual)']
    else:
        top_schools.columns = ['Value Added (Residual)']
    top_schools['Value Added (Residual)'] = top_schools['Value Added (Residual)'].round(3)

    top_table = dash_table.DataTable(
        data=top_schools.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in top_schools.columns],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgreen', 'fontWeight': 'bold'},
    )

    # Bottom schools (negative residuals)
    bottom_schools = school_residuals.tail(10)[top_cols].copy()
    if len(top_cols) == 2:
        bottom_schools.columns = ['School', 'Value Added (Residual)']
    else:
        bottom_schools.columns = ['Value Added (Residual)']
    bottom_schools['Value Added (Residual)'] = bottom_schools['Value Added (Residual)'].round(3)

    bottom_table = dash_table.DataTable(
        data=bottom_schools.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in bottom_schools.columns],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightcoral', 'fontWeight': 'bold'},
    )

    return stats_content, imp_fig, va_fig, top_table, bottom_table


# ============================================================================
# TAB 7: POLICY KPIs CALLBACKS
# ============================================================================

# Update municipality dropdown based on department selection
@app.callback(
    Output('kpi-municipality', 'options'),
    [Input('kpi-department', 'value')]
)
def update_kpi_municipality_dropdown(department):
    """Update municipality dropdown for KPI tab"""
    if not department:
        return []

    munics = df_municipalities[df_municipalities['COLE_DEPTO_UBICACION'] == department]['COLE_MCPIO_UBICACION'].dropna().unique()
    return [{'label': m, 'value': m} for m in sorted(munics)]


# Main KPI calculation callback
@app.callback(
    [Output('kpi-equity-gap', 'children'),
     Output('kpi-equity-gap-desc', 'children'),
     Output('kpi-equity-gap-indicator', 'children'),
     Output('kpi-avg-global', 'children'),
     Output('kpi-avg-global-desc', 'children'),
     Output('kpi-avg-global-indicator', 'children'),
     Output('kpi-value-added-pct', 'children'),
     Output('kpi-value-added-pct-desc', 'children'),
     Output('kpi-value-added-indicator', 'children'),
     Output('kpi-context-cards', 'children'),
     Output('kpi-equity-chart', 'figure'),
     Output('kpi-gaps-chart', 'figure'),
     Output('kpi-priority-table', 'children'),
     Output('kpi-best-practices-table', 'children'),
     Output('kpi-recommendations', 'children')],
    [Input('kpi-level', 'value'),
     Input('kpi-department', 'value'),
     Input('kpi-municipality', 'value')]
)
def update_policy_kpis(level, department, municipality):
    """Calculate and display policy KPIs based on selected level"""
    # Check access for protected tab
    accessible, message = is_tab_accessible('tab-policy-kpis')
    if not accessible:
        login_msg = create_login_required_message("Policy KPIs Dashboard")
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="🔒 Login required for Policy KPIs",
                                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return ("N/A", "Login required", "", "N/A", "Login required", "", "N/A", "Login required", "",
                login_msg, empty_fig, empty_fig, html.P("Login required"), html.P("Login required"),
                html.P("Login required to view recommendations"))

    # Filter data based on level
    if level == 'national':
        df_filtered_students = df_students.copy()
        df_filtered_schools = df_schools.copy()
        level_name = "Colombia (National)"
    elif level == 'department':
        if not department:
            return generate_empty_kpis()
        df_filtered_students = df_students[df_students['COLE_DEPTO_UBICACION'] == department] if 'COLE_DEPTO_UBICACION' in df_students.columns else df_students
        df_filtered_schools = df_schools[df_schools['COLE_DEPTO_UBICACION'] == department] if 'COLE_DEPTO_UBICACION' in df_schools.columns else df_schools
        level_name = department
    elif level == 'municipality':
        if not municipality:
            return generate_empty_kpis()
        df_filtered_students = df_students[df_students['COLE_MCPIO_UBICACION'] == municipality] if 'COLE_MCPIO_UBICACION' in df_students.columns else df_students
        df_filtered_schools = df_schools[df_schools['COLE_MCPIO_UBICACION'] == municipality] if 'COLE_MCPIO_UBICACION' in df_schools.columns else df_schools
        level_name = municipality
    else:
        return generate_empty_kpis()

    if len(df_filtered_students) == 0 or len(df_filtered_schools) == 0:
        return generate_empty_kpis()

    # ===== KPI 1: EQUITY GAP INDEX =====
    equity_gap, equity_desc, equity_indicator = calculate_equity_gap(df_filtered_students)

    # ===== KPI 2: AVERAGE GLOBAL SCORE =====
    avg_global, global_desc, global_indicator = calculate_avg_global_score(df_filtered_students, df_filtered_schools)

    # ===== KPI 3: VALUE-ADDED SCHOOLS % =====
    value_added_pct, va_desc, va_indicator = calculate_value_added_percentage(df_filtered_students, df_filtered_schools)

    # ===== CONTEXT-SPECIFIC KPIs =====
    context_cards = generate_context_kpis(level, df_filtered_students, df_filtered_schools)

    # ===== EQUITY CHART =====
    equity_chart = create_equity_chart(df_filtered_students, level_name)

    # ===== GAPS CHART =====
    gaps_chart = create_gaps_chart(df_filtered_students, df_filtered_schools, level)

    # ===== PRIORITY AREAS =====
    priority_table = create_priority_table(df_filtered_schools, level)

    # ===== BEST PRACTICES =====
    best_practices_table = create_best_practices_table(df_filtered_schools, level)

    # ===== RECOMMENDATIONS =====
    recommendations = generate_recommendations(equity_gap, avg_global, value_added_pct, level, level_name)

    return (equity_gap, equity_desc, equity_indicator,
            avg_global, global_desc, global_indicator,
            value_added_pct, va_desc, va_indicator,
            context_cards,
            equity_chart, gaps_chart,
            priority_table, best_practices_table,
            recommendations)


def generate_empty_kpis():
    """Return empty values for all KPI outputs"""
    empty_fig = go.Figure()
    empty_fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    return ("N/A", "Select a valid location", html.Span(),
            "N/A", "Select a valid location", html.Span(),
            "N/A", "Select a valid location", html.Span(),
            html.P("No data available"),
            empty_fig, empty_fig,
            html.P("No data available"),
            html.P("No data available"),
            html.P("Select a valid location to see recommendations"))


def calculate_equity_gap(df_students):
    """Calculate equity gap index based on socioeconomic strata"""
    estrato_col = 'FAMI_ESTRATOVIVIENDA' if 'FAMI_ESTRATOVIVIENDA' in df_students.columns else None
    global_col = 'PUNT_GLOBAL' if 'PUNT_GLOBAL' in df_students.columns else None

    if not estrato_col or not global_col:
        return "N/A", "Data not available", html.Span()

    df_valid = df_students[[estrato_col, global_col]].dropna()

    if len(df_valid) < 100:
        return "N/A", "Insufficient data", html.Span()

    # Group by estrato and get mean scores
    estrato_scores = df_valid.groupby(estrato_col)[global_col].mean()

    if len(estrato_scores) < 2:
        return "N/A", "Insufficient strata", html.Span()

    # Calculate gap between highest and lowest quintile
    top_quintile = estrato_scores.nlargest(int(len(estrato_scores) * 0.2) + 1).mean()
    bottom_quintile = estrato_scores.nsmallest(int(len(estrato_scores) * 0.2) + 1).mean()

    gap = top_quintile - bottom_quintile

    # Determine indicator
    if gap < 30:
        indicator = html.Span("🟢 Low Gap", className="badge bg-success")
        desc = "Good equity - small gap between strata"
    elif gap < 50:
        indicator = html.Span("🟡 Moderate Gap", className="badge bg-warning")
        desc = "Moderate equity concerns"
    else:
        indicator = html.Span("🔴 High Gap", className="badge bg-danger")
        desc = "Urgent: Large inequality between strata"

    return f"{gap:.1f} pts", desc, indicator


def calculate_avg_global_score(df_students, df_schools):
    """Calculate average global score"""
    global_col = 'PUNT_GLOBAL' if 'PUNT_GLOBAL' in df_students.columns else None
    global_mean_col = 'PUNT_GLOBAL_mean' if 'PUNT_GLOBAL_mean' in df_schools.columns else None

    if global_mean_col and len(df_schools) > 0:
        avg = df_schools[global_mean_col].mean()
    elif global_col and len(df_students) > 0:
        avg = df_students[global_col].mean()
    else:
        return "N/A", "Data not available", html.Span()

    # National average is around 250-270 for SABER 11
    if avg >= 270:
        indicator = html.Span("🟢 Above National", className="badge bg-success")
        desc = "Above national average"
    elif avg >= 250:
        indicator = html.Span("🟡 National Average", className="badge bg-warning")
        desc = "At national average level"
    else:
        indicator = html.Span("🔴 Below National", className="badge bg-danger")
        desc = "Below national average - needs improvement"

    return f"{avg:.1f}", desc, indicator


def calculate_value_added_percentage(df_students, df_schools):
    """Calculate percentage of schools with positive value-added"""
    # This requires running the value-added model
    # For now, use a simplified version based on school performance vs estrato

    if len(df_schools) < 10:
        return "N/A", "Insufficient schools", html.Span()

    # Use global score mean as proxy
    global_mean_col = 'PUNT_GLOBAL_mean' if 'PUNT_GLOBAL_mean' in df_schools.columns else None

    if not global_mean_col:
        return "N/A", "Data not available", html.Span()

    # Simple heuristic: schools above median are "value-added"
    median_score = df_schools[global_mean_col].median()
    above_median = (df_schools[global_mean_col] > median_score).sum()
    pct = (above_median / len(df_schools)) * 100

    if pct >= 55:
        indicator = html.Span("🟢 High", className="badge bg-success")
        desc = "Many schools exceeding expectations"
    elif pct >= 45:
        indicator = html.Span("🟡 Balanced", className="badge bg-warning")
        desc = "Balanced performance distribution"
    else:
        indicator = html.Span("🔴 Low", className="badge bg-danger")
        desc = "Few schools exceeding expectations"

    return f"{pct:.1f}%", desc, indicator


def generate_context_kpis(level, df_students, df_schools):
    """Generate context-specific KPIs based on level"""
    cards = []

    if level == 'national' or level == 'department':
        # Urban-Rural Gap
        area_col = 'COLE_AREA_UBICACION' if 'COLE_AREA_UBICACION' in df_students.columns else None
        global_col = 'PUNT_GLOBAL' if 'PUNT_GLOBAL' in df_students.columns else None

        if area_col and global_col:
            df_valid = df_students[[area_col, global_col]].dropna()
            if len(df_valid) > 100:
                area_scores = df_valid.groupby(area_col)[global_col].mean()
                if 'URBANO' in area_scores.index and 'RURAL' in area_scores.index:
                    gap = area_scores['URBANO'] - area_scores['RURAL']
                    color = "success" if gap < 20 else ("warning" if gap < 35 else "danger")
                    cards.append(
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H5("🌆 Urban-Rural Gap", className="card-title"),
                                    html.H3(f"{gap:.1f} pts", className=f"text-{color}"),
                                    html.P("Difference between urban and rural schools", className="small text-muted")
                                ])
                            ], color=color, outline=True)
                        ], md=4)
                    )

    if level == 'department' or level == 'municipality':
        # School Type Gap
        naturaleza_col = 'COLE_NATURALEZA' if 'COLE_NATURALEZA' in df_schools.columns else None
        global_mean_col = 'PUNT_GLOBAL_mean' if 'PUNT_GLOBAL_mean' in df_schools.columns else None

        if naturaleza_col and global_mean_col:
            df_valid = df_schools[[naturaleza_col, global_mean_col]].dropna()
            if len(df_valid) > 10:
                type_scores = df_valid.groupby(naturaleza_col)[global_mean_col].mean()
                if 'OFICIAL' in type_scores.index and 'NO OFICIAL' in type_scores.index:
                    gap = abs(type_scores['NO OFICIAL'] - type_scores['OFICIAL'])
                    color = "success" if gap < 15 else ("warning" if gap < 30 else "danger")
                    cards.append(
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.H5("🏫 Public-Private Gap", className="card-title"),
                                    html.H3(f"{gap:.1f} pts", className=f"text-{color}"),
                                    html.P("Difference between public and private schools", className="small text-muted")
                                ])
                            ], color=color, outline=True)
                        ], md=4)
                    )

    # Subject-Specific Weaknesses
    subjects = ['PUNT_MATEMATICAS', 'PUNT_LECTURA_CRITICA', 'PUNT_C_NATURALES',
                'PUNT_SOCIALES_CIUDADANAS', 'PUNT_INGLES']
    subject_scores = {}

    for subj in subjects:
        if subj in df_students.columns:
            subject_scores[subj] = df_students[subj].mean()

    if len(subject_scores) >= 3:
        weakest = min(subject_scores, key=subject_scores.get)
        weakest_name = weakest.replace('PUNT_', '').replace('_', ' ').title()
        weakest_score = subject_scores[weakest]

        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Weakest Subject", className="card-title"),
                        html.H3(weakest_name, className="text-danger"),
                        html.P(f"Avg: {weakest_score:.1f}", className="small text-muted")
                    ])
                ], color="danger", outline=True)
            ], md=4)
        )

    return dbc.Row(cards) if cards else html.P("No context-specific KPIs available")


def create_equity_chart(df_students, level_name):
    """Create equity analysis chart by socioeconomic strata"""
    estrato_col = 'FAMI_ESTRATOVIVIENDA' if 'FAMI_ESTRATOVIVIENDA' in df_students.columns else None
    global_col = 'PUNT_GLOBAL' if 'PUNT_GLOBAL' in df_students.columns else None

    if not estrato_col or not global_col:
        fig = go.Figure()
        fig.add_annotation(text="Socioeconomic data not available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

    df_valid = df_students[[estrato_col, global_col]].dropna()

    if len(df_valid) < 50:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

    # Group by estrato
    estrato_stats = df_valid.groupby(estrato_col)[global_col].agg(['mean', 'count']).reset_index()
    estrato_stats = estrato_stats.sort_values(estrato_col)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=estrato_stats[estrato_col],
        y=estrato_stats['mean'],
        text=estrato_stats['mean'].round(1),
        textposition='auto',
        marker_color=['#d32f2f' if x <= 2 else ('#ff9800' if x <= 4 else '#4caf50') for x in estrato_stats[estrato_col]],
        name='Average Score'
    ))

    fig.update_layout(
        title=f'Performance by Socioeconomic Stratum - {level_name}',
        xaxis_title='Estrato (1=Low, 6=High)',
        yaxis_title='Average Global Score',
        showlegend=False
    )

    return fig


def create_gaps_chart(df_students, df_schools, level):
    """Create performance gaps chart"""
    # Show gaps across different dimensions
    subjects = {
        'PUNT_MATEMATICAS': 'Math',
        'PUNT_LECTURA_CRITICA': 'Reading',
        'PUNT_C_NATURALES': 'Science',
        'PUNT_SOCIALES_CIUDADANAS': 'Social Studies',
        'PUNT_INGLES': 'English'
    }

    subject_avgs = {}
    national_benchmark = 250  # Approximate national average

    for col, name in subjects.items():
        if col in df_students.columns:
            avg = df_students[col].mean()
            gap = avg - national_benchmark
            subject_avgs[name] = gap

    if not subject_avgs:
        fig = go.Figure()
        fig.add_annotation(text="Subject data not available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

    names = list(subject_avgs.keys())
    gaps = list(subject_avgs.values())
    colors = ['#4caf50' if g >= 0 else '#d32f2f' for g in gaps]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names,
        y=gaps,
        marker_color=colors,
        text=[f"{g:+.1f}" for g in gaps],
        textposition='auto'
    ))

    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="National Average")

    fig.update_layout(
        title='Subject Gaps vs National Average',
        xaxis_title='Subject',
        yaxis_title='Gap (points)',
        showlegend=False
    )

    return fig


def create_priority_table(df_schools, level):
    """Create table of priority areas for intervention"""
    global_mean_col = 'PUNT_GLOBAL_mean' if 'PUNT_GLOBAL_mean' in df_schools.columns else None
    name_col = 'COLE_NOMBRE_ESTABLECIMIENTO' if 'COLE_NOMBRE_ESTABLECIMIENTO' in df_schools.columns else None

    if not global_mean_col or not name_col:
        return html.P("School data not available")

    # Get bottom 10 schools
    df_sorted = df_schools.sort_values(global_mean_col).head(10)

    if len(df_sorted) == 0:
        return html.P("No schools found")

    table_data = []
    for idx, row in df_sorted.iterrows():
        table_data.append({
            'School': row[name_col][:50] if len(str(row[name_col])) > 50 else row[name_col],
            'Global Score': f"{row[global_mean_col]:.1f}",
            'Priority': '🔴 High' if row[global_mean_col] < 200 else '🟡 Medium'
        })

    return dash_table.DataTable(
        data=table_data,
        columns=[{'name': i, 'id': i} for i in ['School', 'Global Score', 'Priority']],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#f44336', 'color': 'white', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'column_id': 'Priority', 'filter_query': '{Priority} contains High'},
             'backgroundColor': '#ffebee', 'color': '#c62828'}
        ]
    )


def create_best_practices_table(df_schools, level):
    """Create table of best practice schools to replicate"""
    global_mean_col = 'PUNT_GLOBAL_mean' if 'PUNT_GLOBAL_mean' in df_schools.columns else None
    name_col = 'COLE_NOMBRE_ESTABLECIMIENTO' if 'COLE_NOMBRE_ESTABLECIMIENTO' in df_schools.columns else None

    if not global_mean_col or not name_col:
        return html.P("School data not available")

    # Get top 10 schools
    df_sorted = df_schools.sort_values(global_mean_col, ascending=False).head(10)

    if len(df_sorted) == 0:
        return html.P("No schools found")

    table_data = []
    for idx, row in df_sorted.iterrows():
        table_data.append({
            'School': row[name_col][:50] if len(str(row[name_col])) > 50 else row[name_col],
            'Global Score': f"{row[global_mean_col]:.1f}",
            'Status': '⭐ Excellent'
        })

    return dash_table.DataTable(
        data=table_data,
        columns=[{'name': i, 'id': i} for i in ['School', 'Global Score', 'Status']],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#4caf50', 'color': 'white', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'column_id': 'Status'},
             'backgroundColor': '#e8f5e9', 'color': '#2e7d32'}
        ]
    )


def generate_recommendations(equity_gap, avg_global, value_added_pct, level, level_name):
    """Generate policy recommendations based on KPIs"""
    recommendations = []

    # Parse numeric values
    try:
        gap_value = float(equity_gap.replace(' pts', '').replace('N/A', '0'))
    except:
        gap_value = 0

    try:
        global_value = float(avg_global.replace('N/A', '0'))
    except:
        global_value = 0

    try:
        va_value = float(value_added_pct.replace('%', '').replace('N/A', '0'))
    except:
        va_value = 0

    # Equity-based recommendations
    if gap_value > 50:
        recommendations.append(html.Li([
            html.Strong("🔴 URGENT - Equity Crisis: "),
            f"Large gap ({gap_value:.1f} pts) between socioeconomic strata. ",
            html.Strong("Actions: "),
            "1) Targeted support for Estrato 1-2 schools, 2) Additional teacher training in low-performing areas, 3) Infrastructure investment in disadvantaged neighborhoods"
        ]))
    elif gap_value > 30:
        recommendations.append(html.Li([
            html.Strong("🟡 Equity Concern: "),
            f"Moderate gap ({gap_value:.1f} pts) exists. ",
            html.Strong("Actions: "),
            "1) Scholarship programs for low-estrato students, 2) Peer mentoring between high and low performing schools"
        ]))
    else:
        recommendations.append(html.Li([
            html.Strong("🟢 Good Equity: "),
            f"Low gap ({gap_value:.1f} pts) maintained. ",
            html.Strong("Actions: "),
            "Continue current equity programs and monitor quarterly"
        ]))

    # Performance-based recommendations
    if global_value < 250:
        recommendations.append(html.Li([
            html.Strong("🔴 Below National Average: "),
            f"Score ({global_value:.1f}) below national benchmark. ",
            html.Strong("Actions: "),
            "1) Comprehensive curriculum review, 2) Teacher professional development programs, 3) Student tutoring initiatives"
        ]))
    elif global_value < 270:
        recommendations.append(html.Li([
            html.Strong("🟡 At National Average: "),
            f"Score ({global_value:.1f}) at national level. ",
            html.Strong("Actions: "),
            "1) Identify and replicate best practices from high-performing schools, 2) Focus on weakest subjects"
        ]))
    else:
        recommendations.append(html.Li([
            html.Strong("🟢 Above National Average: "),
            f"Score ({global_value:.1f}) exceeds national benchmark. ",
            html.Strong("Actions: "),
            "Share successful strategies with other regions, continue innovation"
        ]))

    # Value-added recommendations
    if va_value < 45:
        recommendations.append(html.Li([
            html.Strong("⭐ Value-Added Focus Needed: "),
            f"Only {va_value:.1f}% of schools exceeding expectations. ",
            html.Strong("Actions: "),
            "1) Principal leadership training, 2) School transformation programs for underperformers, 3) Study high value-added schools"
        ]))

    # Level-specific recommendations
    if level == 'national':
        recommendations.append(html.Li([
            html.Strong("🇨🇴 National Policy: "),
            "1) Create national teacher training program focused on weakest subjects, ",
            "2) Establish rural school support network, ",
            "3) Implement value-added metrics in school evaluation"
        ]))
    elif level == 'department':
        recommendations.append(html.Li([
            html.Strong("🗺️ Department Actions: "),
            f"For {level_name}: ",
            "1) Deploy mobile teacher teams to struggling municipalities, ",
            "2) Create department-wide best practice sharing network, ",
            "3) Target infrastructure investments to lowest-performing municipalities"
        ]))
    elif level == 'municipality':
        recommendations.append(html.Li([
            html.Strong("🏘️ Municipality Actions: "),
            f"For {level_name}: ",
            "1) School-by-school improvement plans for bottom 10 performers, ",
            "2) Parent engagement programs, ",
            "3) After-school tutoring in weakest subjects"
        ]))

    return html.Ul(recommendations, className="list-group list-group-flush")


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
    print("Open http://127.0.0.1:8052/ in your browser")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=8052)
