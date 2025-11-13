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
import glob
import os
warnings.filterwarnings('ignore')

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "SABER Results - Government Dashboard"

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
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Subject:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-subject',
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
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Grade:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-grade',
                                            options=[{'label': f'Grado {g}', 'value': g} for g in grades],
                                            value='11',
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Subject:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-subject',
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
                                    ], md=4),
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
     Input('overview-subject', 'value'),
     Input('overview-naturaleza', 'value'),
     Input('overview-area', 'value')]
)
def update_overview(grade, subject, naturaleza, area):
    """Update overview tab visualizations"""

    # Filter data
    df = df_schools.copy()

    if naturaleza != 'ALL':
        df = df[df['COLE_NATURALEZA'] == naturaleza]
    if area != 'ALL':
        df = df[df['COLE_AREA_UBICACION'] == area]

    # Get column for selected subject
    if subject not in grade_cols[grade]:
        subject = 'Matemáticas'  # Fallback

    subject_col = grade_cols[grade][subject]
    lang_col = grade_cols[grade].get('Lenguaje', subject_col)  # Keep for backward compatibility
    n_col = grade_cols[grade]['N']

    # Filter out missing values
    required_cols = [subject_col, lang_col, n_col]
    meta_cols = ['COLE_NATURALEZA', 'COLE_AREA_UBICACION']
    available_cols = [c for c in required_cols + meta_cols if c in df.columns]

    df_plot = df[available_cols].dropna(subset=[col for col in [subject_col, lang_col] if col in df.columns])

    # Calculate stats
    total_schools = len(df_plot)
    total_students = int(df_plot[n_col].sum()) if len(df_plot) > 0 else 0
    avg_lang = f"{df_plot[lang_col].mean():.3f}" if len(df_plot) > 0 and lang_col in df_plot.columns else "N/A"
    avg_subject = f"{df_plot[subject_col].mean():.3f}" if len(df_plot) > 0 and subject_col in df_plot.columns else "N/A"

    # Scatter plot - Language vs Selected Subject
    if lang_col in df_plot.columns and subject_col in df_plot.columns and lang_col != subject_col:
        scatter_fig = px.scatter(
            df_plot,
            x=lang_col,
            y=subject_col,
            size=n_col if n_col in df_plot.columns else None,
            color='COLE_NATURALEZA' if 'COLE_NATURALEZA' in df_plot.columns else None,
            hover_data=['COLE_AREA_UBICACION'] if 'COLE_AREA_UBICACION' in df_plot.columns else None,
            title=f'Lectura Crítica vs {subject} - Grade {grade}',
            labels={lang_col: 'Lectura Crítica', subject_col: subject},
            opacity=0.6
        )
        scatter_fig.add_shape(
            type="line", line=dict(dash='dash', color='gray'),
            x0=df_plot[lang_col].min(), y0=df_plot[lang_col].min(),
            x1=df_plot[lang_col].max(), y1=df_plot[lang_col].max()
        )
    else:
        # If same subject or missing columns, show distribution
        scatter_fig = px.histogram(
            df_plot,
            x=subject_col if subject_col in df_plot.columns else lang_col,
            nbins=50,
            title=f'{subject} Distribution - Grade {grade}'
        )

    # Distribution
    dist_fig = make_subplots(rows=1, cols=2, subplot_titles=('Lectura Crítica Distribution', f'{subject} Distribution'))
    if lang_col in df_plot.columns:
        dist_fig.add_trace(
            go.Histogram(x=df_plot[lang_col], name='Lectura Crítica', nbinsx=50, marker_color='lightblue'),
            row=1, col=1
        )
    if subject_col in df_plot.columns:
        dist_fig.add_trace(
            go.Histogram(x=df_plot[subject_col], name=subject, nbinsx=50, marker_color='lightcoral'),
            row=1, col=2
        )
    dist_fig.update_layout(showlegend=False, title_text=f'Score Distributions - Grade {grade}')

    # Grade comparison - show selected subject across grades
    grade_data = []
    for g in grades:
        if subject in grade_cols[g]:
            subj_col_g = grade_cols[g][subject]
            temp = df[[subj_col_g]].dropna()
            if len(temp) > 0:
                grade_data.append({
                    'Grade': g,
                    subject: temp[subj_col_g].mean()
                })

    if grade_data:
        grade_df = pd.DataFrame(grade_data)
        grade_fig = go.Figure()
        grade_fig.add_trace(go.Bar(x=grade_df['Grade'], y=grade_df[subject], name=subject, marker_color='lightcoral'))
        grade_fig.update_layout(title=f'Average {subject} Performance by Grade', barmode='group', xaxis_title='Grade', yaxis_title='Average Score')
    else:
        grade_fig = go.Figure()
        grade_fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)

    return f"{total_schools:,}", f"{total_students:,}", avg_lang, avg_subject, scatter_fig, dist_fig, grade_fig


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
     Input('dept-grade', 'value'),
     Input('dept-subject', 'value')]
)
def update_department(department, grade, subject):
    """Update department analysis"""

    if not department:
        empty_fig = go.Figure()
        return "0", "0", "N/A", "N/A", empty_fig, empty_fig, empty_fig

    # Filter municipalities in department
    df_munic_dept = df_municipalities[df_municipalities['COLE_DEPTO_UBICACION'] == department].copy()

    # Get subject columns
    if subject not in grade_cols[grade]:
        subject = 'Matemáticas'  # Fallback

    subject_col = grade_cols[grade][subject]
    lang_col = grade_cols[grade].get('Lenguaje', subject_col)
    n_col = grade_cols[grade]['N']

    # Filter to available columns
    required_cols = [c for c in [subject_col, lang_col, n_col, 'COLE_MCPIO_UBICACION'] if c in df_munic_dept.columns]
    df_munic_dept = df_munic_dept[required_cols].dropna()

    # Get schools in department - use COLE_DEPTO_UBICACION instead of COLE_COD_MCPIO_UBICACION
    df_schools_dept = df_schools[df_schools['COLE_DEPTO_UBICACION'] == department].copy() if 'COLE_DEPTO_UBICACION' in df_schools.columns else df_schools.copy()

    total_munic = len(df_munic_dept)
    total_schools = len(df_schools_dept)
    avg_lang = f"{df_munic_dept[lang_col].mean():.3f}" if len(df_munic_dept) > 0 and lang_col in df_munic_dept.columns else "N/A"
    avg_subject = f"{df_munic_dept[subject_col].mean():.3f}" if len(df_munic_dept) > 0 and subject_col in df_munic_dept.columns else "N/A"

    # Municipality ranking - sort by subject column
    if subject_col in df_munic_dept.columns:
        df_munic_sorted = df_munic_dept.sort_values(subject_col, ascending=True).tail(20)
    else:
        df_munic_sorted = df_munic_dept.tail(20)

    rank_fig = go.Figure()
    if 'COLE_MCPIO_UBICACION' in df_munic_sorted.columns:
        if lang_col in df_munic_sorted.columns:
            rank_fig.add_trace(go.Bar(
                y=df_munic_sorted['COLE_MCPIO_UBICACION'],
                x=df_munic_sorted[lang_col],
                name='Lectura Crítica',
                orientation='h',
                marker_color='lightblue'
            ))
        if subject_col in df_munic_sorted.columns:
            rank_fig.add_trace(go.Bar(
                y=df_munic_sorted['COLE_MCPIO_UBICACION'],
                x=df_munic_sorted[subject_col],
                name=subject,
                orientation='h',
                marker_color='lightcoral'
            ))
    rank_fig.update_layout(
        title=f'Top 20 Municipalities in {department} - {subject} - Grade {grade}',
        barmode='group',
        xaxis_title='Score',
        height=500
    )

    # Performance scatter
    if 'COLE_MCPIO_UBICACION' in df_munic_sorted.columns and lang_col in df_munic_sorted.columns and subject_col in df_munic_sorted.columns:
        perf_fig = px.scatter(
            df_munic_sorted,
            x=lang_col,
            y=subject_col,
            text='COLE_MCPIO_UBICACION',
            title=f'Municipality Performance Map - {department}',
            labels={lang_col: 'Lectura Crítica', subject_col: subject}
        )
        perf_fig.update_traces(textposition='top center')
    else:
        perf_fig = go.Figure()

    # Type comparison (using school data)
    if len(df_schools_dept) > 0 and 'COLE_NATURALEZA' in df_schools_dept.columns:
        available_score_cols = [c for c in [lang_col, subject_col] if c in df_schools_dept.columns]
        if available_score_cols:
            type_data = df_schools_dept.groupby('COLE_NATURALEZA')[available_score_cols].mean().reset_index()
            type_fig = go.Figure()
            if lang_col in type_data.columns:
                type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[lang_col], name='Lectura Crítica'))
            if subject_col in type_data.columns:
                type_fig.add_trace(go.Bar(x=type_data['COLE_NATURALEZA'], y=type_data[subject_col], name=subject))
            type_fig.update_layout(title='Performance by School Type', barmode='group')
        else:
            type_fig = go.Figure()
    else:
        type_fig = go.Figure()

    return str(total_munic), str(total_schools), avg_lang, avg_subject, rank_fig, perf_fig, type_fig


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
