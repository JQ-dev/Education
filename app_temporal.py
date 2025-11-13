"""
Enhanced Dash App with Multi-Year Temporal Analysis for SABER Results
Supports CSV and Parquet files with year-over-year trend analysis
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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error
import warnings
import os
import glob
warnings.filterwarnings('ignore')

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "SABER Results - Temporal Analysis Platform"

# ============================================================================
# MULTI-YEAR DATA LOADING FUNCTIONS
# ============================================================================

def parse_period_to_year(periodo):
    """Convert period like 20221 or 20222 to year 2022"""
    if pd.isna(periodo):
        return None
    periodo_str = str(int(periodo))
    if len(periodo_str) >= 4:
        return int(periodo_str[:4])
    return None

def load_saber11_multi_year():
    """
    Load Saber 11 data from multiple years
    Supports both CSV and Parquet formats
    Combines multiple periods within same year
    """
    all_data = []

    # Pattern 1: Look for Parquet files (preferred format)
    parquet_files = glob.glob('*.parquet') + glob.glob('Examen_Saber_11*.parquet')

    for file in parquet_files:
        try:
            print(f"Loading {file}...")
            df = pd.read_parquet(file)

            # Standardize column names to uppercase
            df.columns = df.columns.str.upper()

            # Extract year from PERIODO column
            if 'PERIODO' in df.columns:
                df['YEAR'] = df['PERIODO'].apply(parse_period_to_year)

            all_data.append(df)
            print(f"  ✓ Loaded {len(df):,} records")
        except Exception as e:
            print(f"  ✗ Error loading {file}: {e}")

    # Pattern 2: Look for CSV files (fallback)
    csv_files = ['Saber_11__2017-1.csv', 'ICFES_2019.csv']

    for file in csv_files:
        if os.path.exists(file):
            try:
                print(f"Loading {file}...")
                # Load sample to check columns
                df_sample = pd.read_csv(file, nrows=1)
                df_sample.columns = df_sample.columns.str.upper()

                # Load full data
                df = pd.read_csv(file)
                df.columns = df.columns.str.upper()

                # Extract year
                if 'PERIODO' in df.columns:
                    df['YEAR'] = df['PERIODO'].apply(parse_period_to_year)
                else:
                    # Try to extract from filename
                    year_match = file.split('_')
                    for part in year_match:
                        if part.isdigit() and len(part) == 4:
                            df['YEAR'] = int(part)
                            break

                all_data.append(df)
                print(f"  ✓ Loaded {len(df):,} records")
            except Exception as e:
                print(f"  ✗ Error loading {file}: {e}")

    # Pattern 3: Load from zip files if needed
    if os.path.exists('Saber_11__2017-2.zip'):
        try:
            print("Loading Saber_11__2017-2.zip...")
            df = pd.read_csv('Saber_11__2017-2.zip', compression='zip')
            df.columns = df.columns.str.upper()
            if 'PERIODO' in df.columns:
                df['YEAR'] = df['PERIODO'].apply(parse_period_to_year)
            else:
                df['YEAR'] = 2017
            all_data.append(df)
            print(f"  ✓ Loaded {len(df):,} records")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    if not all_data:
        print("⚠️  No Saber 11 data files found. Using sample data.")
        return pd.DataFrame()

    # Combine all years
    df_combined = pd.concat(all_data, ignore_index=True)

    # Ensure YEAR column exists
    if 'YEAR' not in df_combined.columns:
        df_combined['YEAR'] = 2017  # Default

    # Standardize key column names
    column_mapping = {
        'PUNT_MATEMATICAS': 'punt_matematicas',
        'PUNT_LECTURA_CRITICA': 'punt_lectura_critica',
        'PUNT_GLOBAL': 'punt_global',
        'COLE_COD_DANE_ESTABLECIMIENTO': 'cole_cod_dane_establecimiento',
        'COLE_NOMBRE_ESTABLECIMIENTO': 'cole_nombre_establecimiento',
        'COLE_DEPTO_UBICACION': 'cole_depto_ubicacion',
        'COLE_MCPIO_UBICACION': 'cole_mcpio_ubicacion',
        'FAMI_ESTRATOVIVIENDA': 'fami_estratovivienda',
        'FAMI_EDUCACIONMADRE': 'fami_educacionmadre',
        'FAMI_EDUCACIONPADRE': 'fami_educacionpadre',
        'FAMI_TIENEINTERNET': 'fami_tieneinternet',
        'FAMI_TIENECOMPUTADOR': 'fami_tienecomputador',
        'ESTU_GENERO': 'estu_genero',
        'COLE_NATURALEZA': 'cole_naturaleza',
        'COLE_AREA_UBICACION': 'cole_area_ubicacion',
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df_combined.columns:
            df_combined[new_col] = df_combined[old_col]

    print(f"\n✅ Total loaded: {len(df_combined):,} student records")
    print(f"📅 Years available: {sorted(df_combined['YEAR'].dropna().unique())}")

    return df_combined

def aggregate_by_year_school(df_students):
    """Aggregate student data by year and school"""

    score_cols = ['punt_matematicas', 'punt_lectura_critica', 'punt_global']
    groupby_cols = ['YEAR', 'cole_cod_dane_establecimiento', 'cole_nombre_establecimiento',
                   'cole_depto_ubicacion', 'cole_mcpio_ubicacion', 'cole_naturaleza', 'cole_area_ubicacion']

    # Filter to existing columns
    groupby_cols = [c for c in groupby_cols if c in df_students.columns]
    score_cols = [c for c in score_cols if c in df_students.columns]

    if not score_cols or not groupby_cols:
        return pd.DataFrame()

    # Aggregate
    agg_dict = {col: ['mean', 'count'] for col in score_cols}

    df_agg = df_students[groupby_cols + score_cols].groupby(groupby_cols).agg(agg_dict).reset_index()

    # Flatten column names
    df_agg.columns = ['_'.join(col).strip('_') if col[1] else col[0] for col in df_agg.columns.values]

    return df_agg

def aggregate_by_year_municipality(df_students):
    """Aggregate student data by year and municipality"""

    score_cols = ['punt_matematicas', 'punt_lectura_critica', 'punt_global']
    groupby_cols = ['YEAR', 'cole_depto_ubicacion', 'cole_mcpio_ubicacion']

    groupby_cols = [c for c in groupby_cols if c in df_students.columns]
    score_cols = [c for c in score_cols if c in df_students.columns]

    if not score_cols or not groupby_cols:
        return pd.DataFrame()

    agg_dict = {col: ['mean', 'count'] for col in score_cols}

    df_agg = df_students[groupby_cols + score_cols].groupby(groupby_cols).agg(agg_dict).reset_index()
    df_agg.columns = ['_'.join(col).strip('_') if col[1] else col[0] for col in df_agg.columns.values]

    return df_agg

def aggregate_by_year_department(df_students):
    """Aggregate student data by year and department"""

    score_cols = ['punt_matematicas', 'punt_lectura_critica', 'punt_global']
    groupby_cols = ['YEAR', 'cole_depto_ubicacion']

    groupby_cols = [c for c in groupby_cols if c in df_students.columns]
    score_cols = [c for c in score_cols if c in df_students.columns]

    if not score_cols or not groupby_cols:
        return pd.DataFrame()

    agg_dict = {col: ['mean', 'count'] for col in score_cols}

    df_agg = df_students[groupby_cols + score_cols].groupby(groupby_cols).agg(agg_dict).reset_index()
    df_agg.columns = ['_'.join(col).strip('_') if col[1] else col[0] for col in df_agg.columns.values]

    return df_agg

# ============================================================================
# LOAD DATA
# ============================================================================

print("="*70)
print("SABER TEMPORAL ANALYSIS - Loading Multi-Year Data")
print("="*70)

# Load multi-year student data
df_students_multi = load_saber11_multi_year()

# Aggregate by different levels
df_schools_by_year = aggregate_by_year_school(df_students_multi) if len(df_students_multi) > 0 else pd.DataFrame()
df_munic_by_year = aggregate_by_year_municipality(df_students_multi) if len(df_students_multi) > 0 else pd.DataFrame()
df_dept_by_year = aggregate_by_year_department(df_students_multi) if len(df_students_multi) > 0 else pd.DataFrame()

# Get available years
available_years = sorted(df_students_multi['YEAR'].dropna().unique()) if len(df_students_multi) > 0 else [2017, 2019]
departments = sorted(df_students_multi['cole_depto_ubicacion'].dropna().unique()) if len(df_students_multi) > 0 else []

print(f"\n✅ Aggregated data ready:")
print(f"   Schools by year: {len(df_schools_by_year):,} records")
print(f"   Municipalities by year: {len(df_munic_by_year):,} records")
print(f"   Departments by year: {len(df_dept_by_year):,} records")
print("="*70 + "\n")

# ============================================================================
# APP LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("📈 SABER Temporal Analysis Dashboard", className="text-center mb-3 mt-4"),
            html.H5("Multi-Year Educational Performance Trends & Insights",
                   className="text-center text-muted mb-4"),
        ])
    ]),

    # Main tabs
    dbc.Tabs(id="main-tabs", active_tab="tab-trends", children=[

        # TAB 1: Temporal Trends (NEW)
        dbc.Tab(label="📈 Year-over-Year Trends", tab_id="tab-trends", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("National Performance Trends Over Time"),
                        html.P(f"Analyzing data from {len(available_years)} years: {', '.join(map(str, available_years))}",
                              className="text-muted"),
                    ])
                ], className="mb-4"),

                # Year range selector
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Analysis Parameters")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Select Years to Compare:", className="fw-bold"),
                                        dcc.RangeSlider(
                                            id='year-range-slider',
                                            min=min(available_years) if available_years else 2017,
                                            max=max(available_years) if available_years else 2024,
                                            step=1,
                                            value=[min(available_years) if available_years else 2017,
                                                  max(available_years) if available_years else 2024],
                                            marks={year: str(year) for year in available_years},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        )
                                    ], md=8),
                                    dbc.Col([
                                        html.Label("Score Type:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='trend-score-type',
                                            options=[
                                                {'label': 'Mathematics', 'value': 'matematicas'},
                                                {'label': 'Reading/Language', 'value': 'lectura'},
                                                {'label': 'Global Score', 'value': 'global'}
                                            ],
                                            value='matematicas',
                                            clearable=False
                                        )
                                    ], md=4),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                # National trend
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='national-trend-line', style={'height': '400px'})
                    ], md=12),
                ], className="mb-4"),

                # Department and school type trends
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='department-trend-top', style={'height': '400px'})
                    ], md=6),
                    dbc.Col([
                        dcc.Graph(id='schooltype-trend', style={'height': '400px'})
                    ], md=6),
                ]),
            ], className="p-3")
        ]),

        # TAB 2: Department Comparison Over Time
        dbc.Tab(label="🗺️ Department Trends", tab_id="tab-dept-trends", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Department Selection")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Select Departments (up to 5):", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-multi-selector',
                                            options=[{'label': d, 'value': d} for d in departments],
                                            value=departments[:3] if len(departments) >= 3 else departments,
                                            multi=True
                                        )
                                    ], md=8),
                                    dbc.Col([
                                        html.Label("Score Type:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-trend-score',
                                            options=[
                                                {'label': 'Mathematics', 'value': 'matematicas'},
                                                {'label': 'Reading', 'value': 'lectura'},
                                                {'label': 'Global', 'value': 'global'}
                                            ],
                                            value='matematicas',
                                            clearable=False
                                        )
                                    ], md=4),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='dept-comparison-trend', style={'height': '500px'})
                    ], md=12),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='dept-growth-rate', style={'height': '400px'})
                    ], md=6),
                    dbc.Col([
                        dcc.Graph(id='dept-variance-trend', style={'height': '400px'})
                    ], md=6),
                ]),
            ], className="p-3")
        ]),

        # TAB 3: School Performance Evolution
        dbc.Tab(label="🏫 School Evolution", tab_id="tab-school-evolution", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Individual School Performance Over Time"),
                        html.P("Track specific schools' progress year-over-year", className="text-muted"),
                    ])
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Search Schools")),
                            dbc.CardBody([
                                html.Label("Search by School Name:", className="fw-bold"),
                                dcc.Input(
                                    id='school-evolution-search',
                                    type='text',
                                    placeholder='Type school name (min 3 characters)...',
                                    style={'width': '100%'},
                                    className="mb-3"
                                ),
                                html.Div(id='school-evolution-results')
                            ])
                        ], className="mb-4")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        html.Div(id='school-evolution-chart-container')
                    ])
                ]),
            ], className="p-3")
        ]),

        # TAB 4: Improvement & Decline Analysis
        dbc.Tab(label="📊 Improvement Analysis", tab_id="tab-improvement", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Schools & Municipalities: Most Improved vs Most Declined"),
                        html.P("Identify areas showing significant improvement or requiring intervention", className="text-muted"),
                    ])
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Analysis Settings")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Analysis Level:", className="fw-bold"),
                                        dcc.RadioItems(
                                            id='improvement-level',
                                            options=[
                                                {'label': ' Schools', 'value': 'schools'},
                                                {'label': ' Municipalities', 'value': 'municipalities'},
                                                {'label': ' Departments', 'value': 'departments'}
                                            ],
                                            value='schools',
                                            inline=True
                                        )
                                    ], md=6),
                                    dbc.Col([
                                        html.Label("Compare:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='improvement-years',
                                            options=[
                                                {'label': f'{available_years[0]} vs {available_years[-1]}',
                                                 'value': f'{available_years[0]}_{available_years[-1]}'}
                                            ] if len(available_years) >= 2 else [],
                                            value=f'{available_years[0]}_{available_years[-1]}' if len(available_years) >= 2 else None,
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
                        html.H5("🚀 Most Improved (Top 20)"),
                        html.Div(id='most-improved-table')
                    ], md=6),
                    dbc.Col([
                        html.H5("⚠️ Most Declined (Bottom 20)"),
                        html.Div(id='most-declined-table')
                    ], md=6),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='improvement-distribution', style={'height': '400px'})
                    ], md=12),
                ]),
            ], className="p-3")
        ]),

        # TAB 5: Predictive Trends
        dbc.Tab(label="🔮 Future Projections", tab_id="tab-projections", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Performance Projections & Trend Forecasting"),
                        html.P("Statistical projections based on historical trends", className="text-muted"),
                    ])
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.P("⚠️ This feature requires at least 3 years of data for reliable projections.",
                                      className="text-warning"),
                                html.P(f"Currently available: {len(available_years)} years", className="fw-bold"),
                            ])
                        ])
                    ])
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='projection-national', style={'height': '400px'})
                    ], md=12),
                ]),
            ], className="p-3")
        ]),
    ]),

], fluid=True)

# ============================================================================
# CALLBACKS
# ============================================================================

# TAB 1: Temporal trends
@app.callback(
    [Output('national-trend-line', 'figure'),
     Output('department-trend-top', 'figure'),
     Output('schooltype-trend', 'figure')],
    [Input('year-range-slider', 'value'),
     Input('trend-score-type', 'value')]
)
def update_temporal_trends(year_range, score_type):
    """Update temporal trend visualizations"""

    if len(df_students_multi) == 0:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No data available", showarrow=False)
        return empty_fig, empty_fig, empty_fig

    # Map score type to column name
    score_col_map = {
        'matematicas': 'punt_matematicas',
        'lectura': 'punt_lectura_critica',
        'global': 'punt_global'
    }
    score_col = score_col_map.get(score_type, 'punt_matematicas')

    # Filter by year range
    df_filtered = df_students_multi[
        (df_students_multi['YEAR'] >= year_range[0]) &
        (df_students_multi['YEAR'] <= year_range[1])
    ].copy()

    # National trend
    if score_col in df_filtered.columns:
        national_trend = df_filtered.groupby('YEAR')[score_col].mean().reset_index()

        nat_fig = go.Figure()
        nat_fig.add_trace(go.Scatter(
            x=national_trend['YEAR'],
            y=national_trend[score_col],
            mode='lines+markers',
            name='National Average',
            line=dict(width=3, color='blue'),
            marker=dict(size=10)
        ))
        nat_fig.update_layout(
            title=f'National Average {score_type.title()} Score Trend',
            xaxis_title='Year',
            yaxis_title='Average Score',
            hovermode='x unified'
        )
    else:
        nat_fig = go.Figure()

    # Department trends (top 5)
    if 'cole_depto_ubicacion' in df_filtered.columns and score_col in df_filtered.columns:
        dept_trend = df_filtered.groupby(['YEAR', 'cole_depto_ubicacion'])[score_col].mean().reset_index()

        # Get top 5 departments by latest year
        latest_year = dept_trend['YEAR'].max()
        top_depts = dept_trend[dept_trend['YEAR'] == latest_year].nlargest(5, score_col)['cole_depto_ubicacion'].values

        dept_fig = go.Figure()
        for dept in top_depts:
            dept_data = dept_trend[dept_trend['cole_depto_ubicacion'] == dept]
            dept_fig.add_trace(go.Scatter(
                x=dept_data['YEAR'],
                y=dept_data[score_col],
                mode='lines+markers',
                name=dept
            ))

        dept_fig.update_layout(
            title=f'Top 5 Departments - {score_type.title()} Score Trend',
            xaxis_title='Year',
            yaxis_title='Average Score',
            hovermode='x unified'
        )
    else:
        dept_fig = go.Figure()

    # School type trends
    if 'cole_naturaleza' in df_filtered.columns and score_col in df_filtered.columns:
        type_trend = df_filtered.groupby(['YEAR', 'cole_naturaleza'])[score_col].mean().reset_index()

        type_fig = go.Figure()
        for school_type in type_trend['cole_naturaleza'].unique():
            type_data = type_trend[type_trend['cole_naturaleza'] == school_type]
            type_fig.add_trace(go.Scatter(
                x=type_data['YEAR'],
                y=type_data[score_col],
                mode='lines+markers',
                name=school_type
            ))

        type_fig.update_layout(
            title=f'School Type Comparison - {score_type.title()}',
            xaxis_title='Year',
            yaxis_title='Average Score',
            hovermode='x unified'
        )
    else:
        type_fig = go.Figure()

    return nat_fig, dept_fig, type_fig


# TAB 2: Department trends
@app.callback(
    [Output('dept-comparison-trend', 'figure'),
     Output('dept-growth-rate', 'figure'),
     Output('dept-variance-trend', 'figure')],
    [Input('dept-multi-selector', 'value'),
     Input('dept-trend-score', 'value')]
)
def update_department_trends(selected_depts, score_type):
    """Update department comparison trends"""

    if not selected_depts or len(df_students_multi) == 0:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Select departments to compare", showarrow=False)
        return empty_fig, empty_fig, empty_fig

    score_col_map = {
        'matematicas': 'punt_matematicas',
        'lectura': 'punt_lectura_critica',
        'global': 'punt_global'
    }
    score_col = score_col_map.get(score_type, 'punt_matematicas')

    # Filter data
    df_depts = df_students_multi[df_students_multi['cole_depto_ubicacion'].isin(selected_depts)].copy()

    if score_col not in df_depts.columns:
        empty_fig = go.Figure()
        return empty_fig, empty_fig, empty_fig

    # Comparison trend
    dept_trends = df_depts.groupby(['YEAR', 'cole_depto_ubicacion'])[score_col].mean().reset_index()

    comp_fig = go.Figure()
    for dept in selected_depts:
        dept_data = dept_trends[dept_trends['cole_depto_ubicacion'] == dept]
        comp_fig.add_trace(go.Scatter(
            x=dept_data['YEAR'],
            y=dept_data[score_col],
            mode='lines+markers',
            name=dept,
            line=dict(width=2),
            marker=dict(size=8)
        ))

    comp_fig.update_layout(
        title='Department Performance Comparison',
        xaxis_title='Year',
        yaxis_title=f'Average {score_type.title()} Score',
        hovermode='x unified',
        height=500
    )

    # Growth rate (year-over-year change)
    growth_data = []
    for dept in selected_depts:
        dept_data = dept_trends[dept_trends['cole_depto_ubicacion'] == dept].sort_values('YEAR')
        if len(dept_data) >= 2:
            first_year = dept_data.iloc[0][score_col]
            last_year = dept_data.iloc[-1][score_col]
            years_diff = dept_data.iloc[-1]['YEAR'] - dept_data.iloc[0]['YEAR']
            if years_diff > 0:
                growth_rate = ((last_year - first_year) / first_year) * 100
                growth_data.append({'Department': dept, 'Growth %': growth_rate})

    growth_df = pd.DataFrame(growth_data).sort_values('Growth %', ascending=True)

    growth_fig = go.Figure(go.Bar(
        x=growth_df['Growth %'],
        y=growth_df['Department'],
        orientation='h',
        marker_color=['red' if x < 0 else 'green' for x in growth_df['Growth %']]
    ))
    growth_fig.update_layout(
        title='Overall Growth Rate (%)',
        xaxis_title='Percentage Change',
        yaxis_title='Department'
    )

    # Variance trend (consistency)
    variance_data = df_depts.groupby(['YEAR', 'cole_depto_ubicacion'])[score_col].std().reset_index()

    var_fig = go.Figure()
    for dept in selected_depts:
        dept_var = variance_data[variance_data['cole_depto_ubicacion'] == dept]
        var_fig.add_trace(go.Scatter(
            x=dept_var['YEAR'],
            y=dept_var[score_col],
            mode='lines+markers',
            name=dept
        ))

    var_fig.update_layout(
        title='Score Variance Over Time (Lower = More Consistent)',
        xaxis_title='Year',
        yaxis_title='Standard Deviation',
        hovermode='x unified'
    )

    return comp_fig, growth_fig, var_fig


# TAB 3: School evolution
@app.callback(
    Output('school-evolution-results', 'children'),
    [Input('school-evolution-search', 'value')]
)
def search_schools_evolution(search_term):
    """Search schools for evolution tracking"""

    if not search_term or len(search_term) < 3:
        return html.P("Type at least 3 characters to search...", className="text-muted")

    if len(df_schools_by_year) == 0:
        return html.P("No school data available", className="text-warning")

    # Search
    df_search = df_schools_by_year[
        df_schools_by_year['cole_nombre_establecimiento'].str.contains(search_term, case=False, na=False)
    ].copy()

    if len(df_search) == 0:
        return html.P("No schools found", className="text-warning")

    # Show schools with multiple years of data
    school_years = df_search.groupby('cole_cod_dane_establecimiento')['YEAR'].count().reset_index()
    multi_year_schools = school_years[school_years['YEAR'] >= 2]['cole_cod_dane_establecimiento'].values

    df_display = df_search[df_search['cole_cod_dane_establecimiento'].isin(multi_year_schools)].copy()

    if len(df_display) == 0:
        return html.P("No schools with multi-year data found for this search", className="text-warning")

    # Create clickable list
    unique_schools = df_display[['cole_cod_dane_establecimiento', 'cole_nombre_establecimiento']].drop_duplicates().head(20)

    return html.Div([
        html.P(f"Found {len(unique_schools)} schools with multi-year data (showing first 20):"),
        dbc.ListGroup([
            dbc.ListGroupItem(
                row['cole_nombre_establecimiento'],
                id={'type': 'school-evolution-item', 'index': row['cole_cod_dane_establecimiento']},
                action=True
            )
            for _, row in unique_schools.iterrows()
        ])
    ])


# TAB 4: Improvement analysis
@app.callback(
    [Output('most-improved-table', 'children'),
     Output('most-declined-table', 'children'),
     Output('improvement-distribution', 'figure')],
    [Input('improvement-level', 'value'),
     Input('improvement-years', 'value')]
)
def update_improvement_analysis(level, year_comparison):
    """Analyze most improved and declined entities"""

    if not year_comparison or len(df_students_multi) == 0:
        empty = html.P("No data available")
        empty_fig = go.Figure()
        return empty, empty, empty_fig

    year_start, year_end = map(int, year_comparison.split('_'))

    # Select appropriate dataset
    if level == 'schools':
        df_data = df_schools_by_year
        id_col = 'cole_cod_dane_establecimiento'
        name_col = 'cole_nombre_establecimiento'
        score_col = 'punt_matematicas_mean'
    elif level == 'municipalities':
        df_data = df_munic_by_year
        id_col = 'cole_mcpio_ubicacion'
        name_col = 'cole_mcpio_ubicacion'
        score_col = 'punt_matematicas_mean'
    else:  # departments
        df_data = df_dept_by_year
        id_col = 'cole_depto_ubicacion'
        name_col = 'cole_depto_ubicacion'
        score_col = 'punt_matematicas_mean'

    if len(df_data) == 0 or score_col not in df_data.columns:
        empty = html.P("Insufficient data")
        empty_fig = go.Figure()
        return empty, empty, empty_fig

    # Get data for both years
    df_start = df_data[df_data['YEAR'] == year_start][[id_col, name_col, score_col]].copy()
    df_end = df_data[df_data['YEAR'] == year_end][[id_col, name_col, score_col]].copy()

    # Merge and calculate change
    df_change = pd.merge(df_start, df_end, on=id_col, suffixes=('_start', '_end'))
    df_change['change'] = df_change[f'{score_col}_end'] - df_change[f'{score_col}_start']
    df_change['change_pct'] = (df_change['change'] / df_change[f'{score_col}_start']) * 100

    # Most improved
    df_improved = df_change.nlargest(20, 'change')[[f'{name_col}_start', 'change', 'change_pct']].copy()
    df_improved.columns = ['Name', 'Score Change', 'Change %']
    df_improved['Score Change'] = df_improved['Score Change'].round(2)
    df_improved['Change %'] = df_improved['Change %'].round(2)

    improved_table = dash_table.DataTable(
        data=df_improved.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in df_improved.columns],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgreen', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
        ]
    )

    # Most declined
    df_declined = df_change.nsmallest(20, 'change')[[f'{name_col}_start', 'change', 'change_pct']].copy()
    df_declined.columns = ['Name', 'Score Change', 'Change %']
    df_declined['Score Change'] = df_declined['Score Change'].round(2)
    df_declined['Change %'] = df_declined['Change %'].round(2)

    declined_table = dash_table.DataTable(
        data=df_declined.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in df_declined.columns],
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightcoral', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
        ]
    )

    # Distribution of changes
    dist_fig = px.histogram(
        df_change,
        x='change',
        nbins=50,
        title=f'Distribution of Score Changes ({year_start} to {year_end})',
        labels={'change': 'Score Change', 'count': 'Frequency'}
    )
    dist_fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="No Change")

    return improved_table, declined_table, dist_fig


# TAB 5: Projections
@app.callback(
    Output('projection-national', 'figure'),
    [Input('year-range-slider', 'value')]
)
def update_projections(year_range):
    """Create simple linear projections"""

    if len(df_students_multi) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Need at least 3 years of data for projections",
            showarrow=False,
            font=dict(size=16, color="orange")
        )
        return fig

    # National average by year
    df_nat = df_students_multi.groupby('YEAR')['punt_matematicas'].mean().reset_index()
    df_nat = df_nat.sort_values('YEAR')

    if len(df_nat) < 3:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data", showarrow=False)
        return fig

    # Simple linear regression for projection
    from sklearn.linear_model import LinearRegression

    X = df_nat['YEAR'].values.reshape(-1, 1)
    y = df_nat['punt_matematicas'].values

    model = LinearRegression()
    model.fit(X, y)

    # Project 3 years into future
    future_years = np.arange(df_nat['YEAR'].max() + 1, df_nat['YEAR'].max() + 4).reshape(-1, 1)
    future_predictions = model.predict(future_years)

    # Create figure
    fig = go.Figure()

    # Historical data
    fig.add_trace(go.Scatter(
        x=df_nat['YEAR'],
        y=df_nat['punt_matematicas'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='blue', width=2),
        marker=dict(size=10)
    ))

    # Projected data
    fig.add_trace(go.Scatter(
        x=future_years.flatten(),
        y=future_predictions,
        mode='lines+markers',
        name='Projected',
        line=dict(color='orange', width=2, dash='dash'),
        marker=dict(size=10, symbol='x')
    ))

    fig.update_layout(
        title='National Mathematics Score: Historical + 3-Year Projection',
        xaxis_title='Year',
        yaxis_title='Average Mathematics Score',
        hovermode='x unified'
    )

    return fig


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("SABER TEMPORAL ANALYSIS DASHBOARD")
    print("="*70)
    print(f"\nYears available: {', '.join(map(str, available_years))}")
    print(f"Total student records: {len(df_students_multi):,}")
    print(f"\nStarting server...")
    print("Open http://127.0.0.1:8053/ in your browser")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=8053)
    app.run_server(debug=True, host='0.0.0.0', port=8053)
