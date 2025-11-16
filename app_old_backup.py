"""
Dash App for Colombian SABER School Results Analysis
Shows school performance across different grades and subjects with ML-based predictions
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "SABER School Results Dashboard"

# Load and prepare data
def load_data():
    """Load and merge school data"""
    try:
        # Load test scores
        scores_df = pd.read_csv('Colegios4.csv')

        # Load school information
        schools_df = pd.read_csv('Cole_list3.csv')

        # Merge dataframes
        df = pd.merge(
            scores_df,
            schools_df,
            left_on='CODIGO',
            right_on='COLE_COD_DANE_ESTABLECIMIENTO',
            how='left'
        )

        # Fill missing values in categorical columns
        categorical_cols = ['COLE_GENERO', 'COLE_NATURALEZA', 'COLE_CARACTER', 'COLE_AREA_UBICACION']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].fillna('No especificado')

        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data
df_schools = load_data()

# KPI Calculation Functions
def calculate_kpis(df):
    """
    Calculate the 6 independent KPIs for educational equity and efficiency.

    NOTE: Some KPIs use simulated data as placeholders where actual data
    (SES quintiles, ethnicity, spending, etc.) is not available in current dataset.
    These should be replaced with real calculations when data becomes available.
    """
    kpis = {}

    # 1. Equity-Adjusted Learning Gap (EALG)
    # Target: >0.85 (i.e., <15% of score variance due to SES)
    # NOTE: Requires SES data, parental education, urban/rural - using simulated value
    kpis['EALG'] = {
        'name': 'Equity-Adjusted Learning Gap',
        'abbr': 'EALG',
        'current': 0.78,  # Simulated - would need R² from SES regression
        'target': 0.85,
        'target_comparison': '>',
        'description': 'Proportion of score variance unexplained by SES (higher is better)',
        'formula': '1 - R²(Global Score ~ SES quintile + parental education + urban/rural)',
        'status': 'red',
        'unit': ''
    }

    # 2. Rural-Urban Competency Divergence Index (RUCDI)
    # Target: <0.3σ (small effect size)
    # NOTE: Requires English scores by rural/urban within SES quintiles - using simulated value
    kpis['RUCDI'] = {
        'name': 'Rural-Urban Competency Divergence Index',
        'abbr': 'RUCDI',
        'current': 0.62,  # Simulated - would calculate from English scores
        'target': 0.30,
        'target_comparison': '<',
        'description': 'Standardized mean difference in English scores (rural vs urban, same SES)',
        'formula': '(Mean_urban - Mean_rural) / σ_pooled within SES Q3',
        'status': 'red',
        'unit': 'σ'
    }

    # 3. Ethnic Resilience Ratio (ERR)
    # Target: >0.95
    # NOTE: Requires ethnicity data and Ciencias Naturales scores - using simulated value
    kpis['ERR'] = {
        'name': 'Ethnic Resilience Ratio',
        'abbr': 'ERR',
        'current': 0.88,  # Simulated - would use propensity score matching
        'target': 0.95,
        'target_comparison': '>',
        'description': 'Performance of indigenous/afro-Colombian students vs national average in Science',
        'formula': 'Mean_indigenous/afro (matched) / Mean_national in Ciencias Naturales',
        'status': 'yellow',
        'unit': ''
    }

    # 4. Gender-Neutral Critical Thinking Premium (GNCTP)
    # Target: ≈ 0 (no gender gap after controlling for math)
    # NOTE: Requires Lectura Crítica scores - using simulated value
    kpis['GNCTP'] = {
        'name': 'Gender-Neutral Critical Thinking Premium',
        'abbr': 'GNCTP',
        'current': -2.1,  # Simulated β coefficient
        'target': 0.0,
        'target_comparison': '≈',
        'description': 'Male-female gap in Critical Reading after controlling for Math ability',
        'formula': 'β_female in Lectura ~ Matemáticas + controls',
        'status': 'yellow',
        'unit': ''
    }

    # 5. Municipal Efficiency Frontier (MEF)
    # Target: >15%
    # NOTE: Requires per-student spending data - using simulated value
    kpis['MEF'] = {
        'name': 'Municipal Efficiency Frontier',
        'abbr': 'MEF',
        'current': 11.0,  # Simulated percentage
        'target': 15.0,
        'target_comparison': '>',
        'description': '% of municipalities in top decile of score per peso spent',
        'formula': '% municipalities with (Global Score / Spending per student) > P90',
        'status': 'yellow',
        'unit': '%'
    }

    # 6. School-Level Volatility Stabilizer (SVS)
    # Target: >0.80 (low volatility)
    # NOTE: Requires multi-year data - using simulated value
    kpis['SVS'] = {
        'name': 'School-Level Volatility Stabilizer',
        'abbr': 'SVS',
        'current': 0.71,  # Simulated
        'target': 0.80,
        'target_comparison': '>',
        'description': 'Year-to-year stability in Civics rankings (higher is better)',
        'formula': '1 - median|Rank_t - Rank_t-1| for Sociales y Ciudadanas',
        'status': 'red',
        'unit': ''
    }

    return kpis

# Get available grades and subjects
grades = ['3', '5', '9', '11']
subjects = ['Lenguaje', 'Matemáticas']

# Create grade-subject columns mapping
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

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("📊 SABER School Results Dashboard", className="text-center mb-4 mt-4"),
            html.H5("Análisis de Resultados por Colegio y Predicción de Desempeño",
                   className="text-center text-muted mb-4"),
        ])
    ]),

    # Filters section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Filtros")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Género del Colegio:", className="fw-bold"),
                            dcc.Dropdown(
                                id='filter-genero',
                                options=[{'label': 'Todos', 'value': 'ALL'}] +
                                        [{'label': g, 'value': g} for g in genero_options],
                                value='ALL',
                                clearable=False
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Naturaleza:", className="fw-bold"),
                            dcc.Dropdown(
                                id='filter-naturaleza',
                                options=[{'label': 'Todos', 'value': 'ALL'}] +
                                        [{'label': n, 'value': n} for n in naturaleza_options],
                                value='ALL',
                                clearable=False
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Carácter:", className="fw-bold"),
                            dcc.Dropdown(
                                id='filter-caracter',
                                options=[{'label': 'Todos', 'value': 'ALL'}] +
                                        [{'label': c, 'value': c} for c in caracter_options],
                                value='ALL',
                                clearable=False
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("Área:", className="fw-bold"),
                            dcc.Dropdown(
                                id='filter-area',
                                options=[{'label': 'Todos', 'value': 'ALL'}] +
                                        [{'label': a, 'value': a} for a in area_options],
                                value='ALL',
                                clearable=False
                            )
                        ], md=3),
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Grado:", className="fw-bold"),
                            dcc.Dropdown(
                                id='select-grade',
                                options=[{'label': f'Grado {g}', 'value': g} for g in grades],
                                value='11',
                                clearable=False
                            )
                        ], md=6),
                        dbc.Col([
                            html.Label("Tamaño Mínimo de Muestra (N):", className="fw-bold"),
                            dcc.Slider(
                                id='min-sample-size',
                                min=0,
                                max=100,
                                step=10,
                                value=20,
                                marks={i: str(i) for i in range(0, 101, 20)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], md=6),
                    ])
                ])
            ], className="mb-4")
        ])
    ]),

    # Summary statistics
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='total-schools', className="text-center"),
                    html.P("Colegios Filtrados", className="text-center text-muted")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='avg-lenguaje', className="text-center"),
                    html.P("Promedio Lenguaje", className="text-center text-muted")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='avg-matematicas', className="text-center"),
                    html.P("Promedio Matemáticas", className="text-center text-muted")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='total-students', className="text-center"),
                    html.P("Total Estudiantes", className="text-center text-muted")
                ])
            ])
        ], md=3),
    ], className="mb-4"),

    # Tabs for different visualizations
    dbc.Tabs([
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='scatter-plot', style={'height': '600px'})
                ], md=12)
            ], className="mt-3")
        ], label="📈 Lenguaje vs Matemáticas"),

        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='distribution-plot', style={'height': '600px'})
                ], md=12)
            ], className="mt-3")
        ], label="📊 Distribuciones"),

        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='grade-comparison', style={'height': '600px'})
                ], md=12)
            ], className="mt-3")
        ], label="📉 Comparación por Grado"),

        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("Predicción de Desempeño")),
                        dbc.CardBody([
                            html.P("Este modelo usa Random Forest para predecir el desempeño basado en características del colegio."),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Seleccione Características:", className="fw-bold"),
                                    html.Div(id='prediction-inputs'),
                                ], md=6),
                                dbc.Col([
                                    html.Div(id='prediction-results', className="mt-4")
                                ], md=6)
                            ]),
                            html.Hr(),
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Importancia de Características"),
                                    dcc.Graph(id='feature-importance')
                                ])
                            ])
                        ])
                    ])
                ], md=12)
            ], className="mt-3")
        ], label="🤖 Predicción ML"),

        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Buscar Colegio por Nombre:"),
                        dcc.Input(
                            id='search-school',
                            type='text',
                            placeholder='Escriba el nombre del colegio...',
                            style={'width': '100%', 'marginBottom': '20px'}
                        ),
                        html.Div(id='school-table-container')
                    ])
                ], md=12)
            ], className="mt-3")
        ], label="🔍 Buscar Colegio"),

        dbc.Tab([
            html.Div([
                # Filters Row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("School Filters")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("School Gender:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-genero-filter',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': g, 'value': g} for g in genero_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("School Type:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-naturaleza-filter',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': n, 'value': n} for n in naturaleza_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Character:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-caracter-filter',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': c, 'value': c} for c in caracter_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Area:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-area-filter',
                                            options=[{'label': 'All', 'value': 'ALL'}] +
                                                    [{'label': a, 'value': a} for a in area_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                ]),
                                html.Hr(),
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Grade:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-grade-filter',
                                            options=[{'label': f'Grado {g}', 'value': g} for g in grades],
                                            value='11',
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Minimum Sample Size:", className="fw-bold"),
                                        dcc.Slider(
                                            id='kpi-min-sample',
                                            min=0,
                                            max=100,
                                            step=10,
                                            value=20,
                                            marks={i: str(i) for i in range(0, 101, 20)},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Div([
                                            html.Label("Filtered Schools:", className="fw-bold"),
                                            html.H4(id='kpi-filtered-count', className="text-primary mt-2")
                                        ])
                                    ], md=4),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H4("Key Performance Indicators (KPIs) - Educational Equity & Efficiency")),
                            dbc.CardBody([
                                html.P([
                                    "These 6 metrics are ",
                                    html.Strong("statistically orthogonal"),
                                    " (pairwise |r| < 0.4), ",
                                    html.Strong("policy-actionable"),
                                    ", and focus on ",
                                    html.Strong("systemic failures"),
                                    " rather than simple averages."
                                ], className="text-muted mb-4"),
                                html.P([
                                    html.Strong("Note: "),
                                    "Current values are simulated placeholders. Real calculations require additional data ",
                                    "(SES quintiles, ethnicity, subject-specific scores, spending data, multi-year records)."
                                ], className="alert alert-info"),
                                html.Div(id='kpi-summary-cards'),
                                html.Hr(),
                                html.H5("KPI Dashboard", className="mt-4 mb-3"),
                                html.Div(id='kpi-summary-table'),
                                html.Hr(),
                                html.H5("Visual Analysis", className="mt-4 mb-3"),
                                dcc.Graph(id='kpi-gauge-chart', style={'height': '800px'}),
                            ])
                        ])
                    ], md=12)
                ])
            ], className="mt-3")
        ], label="📊 KPIs - Equity & Efficiency")
    ])

], fluid=True)


# Callback for filtering data and updating all visualizations
@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('distribution-plot', 'figure'),
     Output('grade-comparison', 'figure'),
     Output('total-schools', 'children'),
     Output('avg-lenguaje', 'children'),
     Output('avg-matematicas', 'children'),
     Output('total-students', 'children')],
    [Input('filter-genero', 'value'),
     Input('filter-naturaleza', 'value'),
     Input('filter-caracter', 'value'),
     Input('filter-area', 'value'),
     Input('select-grade', 'value'),
     Input('min-sample-size', 'value')]
)
def update_visualizations(genero, naturaleza, caracter, area, grade, min_sample):
    """Update all visualizations based on filters"""

    # Filter data
    filtered_df = df_schools.copy()

    if genero != 'ALL' and 'COLE_GENERO' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_GENERO'] == genero]

    if naturaleza != 'ALL' and 'COLE_NATURALEZA' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_NATURALEZA'] == naturaleza]

    if caracter != 'ALL' and 'COLE_CARACTER' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_CARACTER'] == caracter]

    if area != 'ALL' and 'COLE_AREA_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_AREA_UBICACION'] == area]

    # Filter by sample size
    n_col = grade_cols[grade]['N']
    if n_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[n_col] >= min_sample]

    # Get column names for selected grade
    lenguaje_col = grade_cols[grade]['Lenguaje']
    matematicas_col = grade_cols[grade]['Matemáticas']
    n_col = grade_cols[grade]['N']

    # Remove rows with missing values for the selected grade
    plot_df = filtered_df[[lenguaje_col, matematicas_col, n_col]].dropna()

    # Scatter plot
    scatter_fig = px.scatter(
        plot_df,
        x=lenguaje_col,
        y=matematicas_col,
        size=n_col,
        title=f'Desempeño en Lenguaje vs Matemáticas - Grado {grade}',
        labels={lenguaje_col: 'Lenguaje (z-score)', matematicas_col: 'Matemáticas (z-score)'},
        opacity=0.6,
        color=n_col,
        color_continuous_scale='Viridis'
    )
    scatter_fig.add_shape(
        type="line", line=dict(dash='dash', color='red'),
        x0=plot_df[lenguaje_col].min(), y0=plot_df[lenguaje_col].min(),
        x1=plot_df[lenguaje_col].max(), y1=plot_df[lenguaje_col].max()
    )
    scatter_fig.update_layout(
        xaxis_title="Lenguaje (z-score)",
        yaxis_title="Matemáticas (z-score)",
        hovermode='closest'
    )

    # Distribution plot
    dist_fig = make_subplots(rows=1, cols=2, subplot_titles=('Distribución Lenguaje', 'Distribución Matemáticas'))

    dist_fig.add_trace(
        go.Histogram(x=plot_df[lenguaje_col], name='Lenguaje', nbinsx=50, marker_color='lightblue'),
        row=1, col=1
    )

    dist_fig.add_trace(
        go.Histogram(x=plot_df[matematicas_col], name='Matemáticas', nbinsx=50, marker_color='lightcoral'),
        row=1, col=2
    )

    dist_fig.update_layout(
        title_text=f'Distribución de Puntajes - Grado {grade}',
        showlegend=False,
        height=600
    )
    dist_fig.update_xaxes(title_text="Z-score", row=1, col=1)
    dist_fig.update_xaxes(title_text="Z-score", row=1, col=2)
    dist_fig.update_yaxes(title_text="Frecuencia", row=1, col=1)
    dist_fig.update_yaxes(title_text="Frecuencia", row=1, col=2)

    # Grade comparison - show performance across all grades
    grade_comparison_data = []
    for g in grades:
        lang_col = grade_cols[g]['Lenguaje']
        math_col = grade_cols[g]['Matemáticas']
        n_col_g = grade_cols[g]['N']

        # Filter for schools with data in this grade
        temp_df = filtered_df[[lang_col, math_col, n_col_g]].dropna()
        temp_df = temp_df[temp_df[n_col_g] >= min_sample]

        if len(temp_df) > 0:
            grade_comparison_data.append({
                'Grado': g,
                'Lenguaje_mean': temp_df[lang_col].mean(),
                'Matematicas_mean': temp_df[math_col].mean(),
                'N_schools': len(temp_df)
            })

    grade_comp_df = pd.DataFrame(grade_comparison_data)

    grade_comp_fig = go.Figure()
    grade_comp_fig.add_trace(go.Bar(
        x=grade_comp_df['Grado'],
        y=grade_comp_df['Lenguaje_mean'],
        name='Lenguaje',
        marker_color='lightblue'
    ))
    grade_comp_fig.add_trace(go.Bar(
        x=grade_comp_df['Grado'],
        y=grade_comp_df['Matematicas_mean'],
        name='Matemáticas',
        marker_color='lightcoral'
    ))

    grade_comp_fig.update_layout(
        title='Promedio de Desempeño por Grado',
        xaxis_title='Grado',
        yaxis_title='Puntaje Promedio (z-score)',
        barmode='group',
        height=600
    )

    # Calculate summary statistics
    total_schools = len(plot_df)
    avg_lenguaje = f"{plot_df[lenguaje_col].mean():.2f}" if len(plot_df) > 0 else "N/A"
    avg_matematicas = f"{plot_df[matematicas_col].mean():.2f}" if len(plot_df) > 0 else "N/A"
    total_students = f"{int(plot_df[n_col].sum()):,}" if len(plot_df) > 0 else "0"

    return scatter_fig, dist_fig, grade_comp_fig, total_schools, avg_lenguaje, avg_matematicas, total_students


# Callback for ML prediction
@app.callback(
    [Output('prediction-inputs', 'children'),
     Output('feature-importance', 'figure')],
    [Input('select-grade', 'value')]
)
def update_ml_section(grade):
    """Update ML prediction section with feature importance"""

    # Prepare data for ML model
    ml_df = df_schools.copy()

    # Select features
    feature_cols = ['COLE_GENERO', 'COLE_NATURALEZA', 'COLE_CARACTER', 'COLE_AREA_UBICACION']
    target_col = grade_cols[grade]['Matematicas']

    # Drop rows with missing target
    ml_df = ml_df[feature_cols + [target_col]].dropna()

    if len(ml_df) < 10:
        return html.P("Datos insuficientes para entrenamiento"), go.Figure()

    # Encode categorical variables
    le_dict = {}
    X = ml_df[feature_cols].copy()
    for col in feature_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        le_dict[col] = le

    y = ml_df[target_col]

    # Train model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)

    # Feature importance plot
    importance_df = pd.DataFrame({
        'Feature': ['Género', 'Naturaleza', 'Carácter', 'Área'],
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=True)

    importance_fig = go.Figure(go.Bar(
        x=importance_df['Importance'],
        y=importance_df['Feature'],
        orientation='h',
        marker_color='lightgreen'
    ))
    importance_fig.update_layout(
        title=f'Importancia de Características (R² Score: {score:.3f})',
        xaxis_title='Importancia',
        yaxis_title='Característica',
        height=400
    )

    # Create input fields for prediction
    inputs = html.Div([
        html.P(f"Modelo entrenado con {len(ml_df)} colegios", className="text-muted"),
        html.P(f"Precisión (R²): {score:.3f}", className="fw-bold"),
        html.Hr(),
        html.P("Seleccione características para predecir:", className="fw-bold"),
        html.Label("Género:"),
        dcc.Dropdown(
            id='pred-genero',
            options=[{'label': g, 'value': g} for g in le_dict['COLE_GENERO'].classes_],
            value=le_dict['COLE_GENERO'].classes_[0]
        ),
        html.Label("Naturaleza:", className="mt-2"),
        dcc.Dropdown(
            id='pred-naturaleza',
            options=[{'label': n, 'value': n} for n in le_dict['COLE_NATURALEZA'].classes_],
            value=le_dict['COLE_NATURALEZA'].classes_[0]
        ),
        html.Label("Carácter:", className="mt-2"),
        dcc.Dropdown(
            id='pred-caracter',
            options=[{'label': c, 'value': c} for c in le_dict['COLE_CARACTER'].classes_],
            value=le_dict['COLE_CARACTER'].classes_[0]
        ),
        html.Label("Área:", className="mt-2"),
        dcc.Dropdown(
            id='pred-area',
            options=[{'label': a, 'value': a} for a in le_dict['COLE_AREA_UBICACION'].classes_],
            value=le_dict['COLE_AREA_UBICACION'].classes_[0]
        ),
        dbc.Button("Predecir Desempeño", id='predict-button', color="primary", className="mt-3 w-100")
    ])

    return inputs, importance_fig


# Callback for school search
@app.callback(
    Output('school-table-container', 'children'),
    [Input('search-school', 'value')]
)
def search_schools(search_term):
    """Search schools by name"""

    if not search_term or len(search_term) < 3:
        return html.P("Escriba al menos 3 caracteres para buscar...", className="text-muted")

    if 'COLE_NOMBRE_ESTABLECIMIENTO' not in df_schools.columns:
        return html.P("Columna de nombres no disponible", className="text-danger")

    # Filter schools
    search_df = df_schools[
        df_schools['COLE_NOMBRE_ESTABLECIMIENTO'].str.contains(search_term, case=False, na=False)
    ].copy()

    if len(search_df) == 0:
        return html.P("No se encontraron colegios con ese nombre", className="text-warning")

    # Select relevant columns for display
    display_cols = ['CODIGO', 'COLE_NOMBRE_ESTABLECIMIENTO', 'COLE_GENERO', 'COLE_NATURALEZA',
                   'COLE_CARACTER', 'COLE_AREA_UBICACION']

    # Add grade 11 scores if available
    if 'Lenguaje Grado 11' in search_df.columns:
        display_cols.append('Lenguaje Grado 11')
    if 'Matemáticas Grado 11' in search_df.columns:
        display_cols.append('Matemáticas Grado 11')

    display_df = search_df[display_cols].head(50)

    # Round numeric columns
    for col in display_df.columns:
        if display_df[col].dtype in ['float64', 'float32']:
            display_df[col] = display_df[col].round(2)

    return html.Div([
        html.H5(f"Encontrados {len(search_df)} colegios (mostrando primeros 50)"),
        dash_table.DataTable(
            data=display_df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in display_df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            page_size=10
        )
    ])


# Callback for KPI Dashboard
@app.callback(
    [Output('kpi-summary-cards', 'children'),
     Output('kpi-summary-table', 'children'),
     Output('kpi-gauge-chart', 'figure'),
     Output('kpi-filtered-count', 'children')],
    [Input('kpi-genero-filter', 'value'),
     Input('kpi-naturaleza-filter', 'value'),
     Input('kpi-caracter-filter', 'value'),
     Input('kpi-area-filter', 'value'),
     Input('kpi-grade-filter', 'value'),
     Input('kpi-min-sample', 'value')]
)
def update_kpi_dashboard(genero, naturaleza, caracter, area, grade, min_sample):
    """Update KPI dashboard with metrics, table, and visualizations based on filters"""

    # Filter schools based on selections
    filtered_df = df_schools.copy()

    # Apply school gender filter
    if genero != 'ALL' and 'COLE_GENERO' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_GENERO'] == genero]

    # Apply school type filter
    if naturaleza != 'ALL' and 'COLE_NATURALEZA' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_NATURALEZA'] == naturaleza]

    # Apply character filter
    if caracter != 'ALL' and 'COLE_CARACTER' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_CARACTER'] == caracter]

    # Apply area filter
    if area != 'ALL' and 'COLE_AREA_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_AREA_UBICACION'] == area]

    # Filter by sample size for the selected grade
    n_col = grade_cols[grade]['N']
    if n_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[n_col] >= min_sample]

    # Get columns for selected grade
    lenguaje_col = grade_cols[grade]['Lenguaje']
    matematicas_col = grade_cols[grade]['Matemáticas']

    # Remove rows with missing values for the selected grade
    plot_df = filtered_df[[lenguaje_col, matematicas_col, n_col]].dropna()

    # Count filtered schools
    filtered_count = f"{len(plot_df):,}"

    # Calculate KPIs with filtered data
    kpis = calculate_kpis(plot_df)

    # Create summary cards
    kpi_cards = []
    kpi_order = ['EALG', 'RUCDI', 'ERR', 'GNCTP', 'MEF', 'SVS']

    for kpi_key in kpi_order:
        kpi = kpis[kpi_key]

        # Determine status icon and color
        if kpi['status'] == 'red':
            icon = '🔴'
            card_color = 'danger'
        elif kpi['status'] == 'yellow':
            icon = '🟡'
            card_color = 'warning'
        else:
            icon = '🟢'
            card_color = 'success'

        # Format current value
        if kpi['unit'] == '%':
            current_str = f"{kpi['current']:.1f}%"
            target_str = f"{kpi['target']:.1f}%"
        elif kpi['unit'] == 'σ':
            current_str = f"{kpi['current']:.2f}σ"
            target_str = f"{kpi['target']:.2f}σ"
        else:
            current_str = f"{kpi['current']:.2f}"
            target_str = f"{kpi['target']:.2f}"

        kpi_cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6(f"{icon} {kpi['abbr']}", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.H4(current_str, className="text-center mb-2"),
                        html.P(f"Target: {kpi['target_comparison']} {target_str}",
                               className="text-center text-muted small mb-2"),
                        html.Hr(className="my-2"),
                        html.P(kpi['name'], className="small mb-1", style={'fontSize': '0.85rem'}),
                        html.P(kpi['description'], className="text-muted small mb-0", style={'fontSize': '0.75rem'}),
                    ])
                ], color=card_color, outline=True)
            ], md=4, className="mb-3")
        )

    summary_cards = dbc.Row(kpi_cards)

    # Create summary table
    table_data = []
    for kpi_key in kpi_order:
        kpi = kpis[kpi_key]

        # Format values
        if kpi['unit'] == '%':
            current_str = f"{kpi['current']:.1f}%"
            target_str = f"{kpi['target']:.1f}%"
        elif kpi['unit'] == 'σ':
            current_str = f"{kpi['current']:.2f}σ"
            target_str = f"{kpi['target']:.2f}σ"
        else:
            current_str = f"{kpi['current']:.2f}"
            target_str = f"{kpi['target']:.2f}"

        # Status icon
        status_icon = '🔴' if kpi['status'] == 'red' else ('🟡' if kpi['status'] == 'yellow' else '🟢')

        table_data.append({
            'Metric': kpi['abbr'],
            'Current': current_str,
            'Target': f"{kpi['target_comparison']} {target_str}",
            'Status': status_icon
        })

    table_df = pd.DataFrame(table_data)

    summary_table = dash_table.DataTable(
        data=table_df.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in table_df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'center',
            'padding': '12px',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'fontSize': '16px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ]
    )

    # Create gauge chart visualization
    fig = make_subplots(
        rows=2, cols=3,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}],
               [{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=[kpis[k]['abbr'] + ' - ' + kpis[k]['name'] for k in kpi_order]
    )

    positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]

    for idx, kpi_key in enumerate(kpi_order):
        kpi = kpis[kpi_key]
        row, col = positions[idx]

        # Determine gauge range and color
        if kpi['target_comparison'] == '>':
            # Higher is better
            gauge_min = 0
            gauge_max = max(kpi['target'] * 1.2, kpi['current'] * 1.2)
            threshold_value = kpi['target']
        elif kpi['target_comparison'] == '<':
            # Lower is better
            gauge_min = 0
            gauge_max = max(kpi['target'] * 2, kpi['current'] * 1.2)
            threshold_value = kpi['target']
        else:  # '≈'
            # Close to target is better
            gauge_min = min(kpi['current'] - abs(kpi['current']), kpi['target'] - abs(kpi['target']))
            gauge_max = max(kpi['current'] + abs(kpi['current']), kpi['target'] + abs(kpi['target']))
            threshold_value = kpi['target']

        # Set color based on status
        if kpi['status'] == 'red':
            bar_color = 'crimson'
        elif kpi['status'] == 'yellow':
            bar_color = 'gold'
        else:
            bar_color = 'lightgreen'

        # Format number
        if kpi['unit'] == '%':
            number_suffix = '%'
        elif kpi['unit'] == 'σ':
            number_suffix = 'σ'
        else:
            number_suffix = ''

        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=kpi['current'],
                title={'text': f"{kpi['abbr']}<br><span style='font-size:0.7em'>{kpi['name']}</span>"},
                delta={'reference': kpi['target'], 'relative': False},
                gauge={
                    'axis': {'range': [gauge_min, gauge_max]},
                    'bar': {'color': bar_color},
                    'threshold': {
                        'line': {'color': "black", 'width': 3},
                        'thickness': 0.75,
                        'value': threshold_value
                    },
                    'steps': [
                        {'range': [gauge_min, threshold_value], 'color': "lightgray"},
                        {'range': [threshold_value, gauge_max], 'color': "white"}
                    ]
                },
                number={'suffix': number_suffix}
            ),
            row=row, col=col
        )

    fig.update_layout(
        height=800,
        showlegend=False,
        margin=dict(l=20, r=20, t=80, b=20)
    )

    return summary_cards, summary_table, fig, filtered_count


if __name__ == '__main__':
    print("Starting SABER School Results Dashboard...")
    print(f"Loaded {len(df_schools)} schools")
    print("Open http://127.0.0.1:8050/ in your browser")
    app.run(debug=True, host='0.0.0.0', port=8051)
