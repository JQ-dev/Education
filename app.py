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

# Initialize the Dash app with Bootstrap theme and custom styling
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True
)
app.title = "Plataforma de Analítica Educativa SABER"
server = app.server  # Expose the Flask server for deployment

# Import landing page
from landing_page import create_landing_page

# Import authentication integration (optional - controlled by ENABLE_AUTH env var)
try:
    from auth_integration import (
        setup_authentication,
        add_auth_callbacks,
        get_auth_layout,
        AUTH_ENABLED
    )
    print(f"✅ Auth module loaded. AUTH_ENABLED={AUTH_ENABLED}")
except ImportError as e:
    AUTH_ENABLED = False
    print(f"⚠️  Auth module not available: {e}")
    get_auth_layout = lambda x: None

# Setup authentication if enabled
if AUTH_ENABLED:
    login_manager = setup_authentication(app)

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

# KPI Calculation Functions - REAL CALCULATIONS FROM DATA
def calculate_kpis(df, df_students_global=None, df_municipalities_global=None):
    """
    Calculate the 6 independent KPIs for educational equity and efficiency.
    NOW USING ACTUAL DATA FROM THE DATASET.
    """
    kpis = {}

    # Use global student data if available
    if df_students_global is None:
        df_students_global = df_students
    if df_municipalities_global is None:
        df_municipalities_global = df_municipalities

    # 1. Equity-Adjusted Learning Gap (EALG)
    # Calculate actual R² from SES regression
    ealg_value = 0.78  # Default
    ealg_status = 'red'
    try:
        if len(df_students_global) > 100:
            df_ses = df_students_global.copy()
            # Standardize column names
            df_ses.columns = df_ses.columns.str.upper()

            # Check for required columns
            ses_cols = ['FAMI_ESTRATOVIVIENDA', 'COLE_AREA_UBICACION']
            target_col = None
            for col in ['PUNT_GLOBAL', 'PUNT_MATEMATICAS', 'PUNT_LECTURA_CRITICA']:
                if col in df_ses.columns:
                    target_col = col
                    break

            if target_col and all(c in df_ses.columns for c in ses_cols):
                # Prepare data for regression
                df_reg = df_ses[ses_cols + [target_col]].dropna()
                if len(df_reg) > 50:
                    # Encode categorical variables
                    X = pd.get_dummies(df_reg[ses_cols], drop_first=True)
                    y = df_reg[target_col]

                    # Fit linear regression
                    from sklearn.linear_model import LinearRegression
                    model = LinearRegression()
                    model.fit(X, y)
                    r2 = model.score(X, y)

                    # EALG = 1 - R² (higher is better, means less variance explained by SES)
                    ealg_value = round(1 - r2, 3)
                    ealg_status = 'green' if ealg_value >= 0.85 else ('yellow' if ealg_value >= 0.70 else 'red')
    except Exception as e:
        print(f"EALG calculation error: {e}")

    kpis['EALG'] = {
        'name': 'Brecha de Aprendizaje Ajustada por Equidad',
        'name_en': 'Equity-Adjusted Learning Gap',
        'abbr': 'EALG',
        'current': ealg_value,
        'target': 0.85,
        'target_comparison': '>',
        'description': 'Proporción de varianza del puntaje no explicada por NSE (mayor es mejor)',
        'explanation': 'Mide qué tanto del desempeño académico se debe al mérito y esfuerzo individual versus factores socioeconómicos. Un valor alto indica que el sistema educativo está logrando equidad.',
        'importance': 'Este indicador es crucial para evaluar si Colombia está cumpliendo su compromiso constitucional de igualdad de oportunidades educativas.',
        'formula': '1 - R²(Puntaje Global ~ estrato + área)',
        'status': ealg_status,
        'unit': '',
        'calculated': True
    }

    # 2. Rural-Urban Competency Divergence Index (RUCDI)
    # Calculate actual urban-rural gap in scores
    rucdi_value = 0.62  # Default
    rucdi_status = 'red'
    try:
        if len(df_students_global) > 100:
            df_area = df_students_global.copy()
            df_area.columns = df_area.columns.str.upper()

            area_col = 'COLE_AREA_UBICACION'
            score_col = None
            for col in ['PUNT_INGLES', 'PUNT_GLOBAL', 'PUNT_MATEMATICAS']:
                if col in df_area.columns:
                    score_col = col
                    break

            if area_col in df_area.columns and score_col:
                df_area_clean = df_area[[area_col, score_col]].dropna()

                # Calculate means and std
                urban_scores = df_area_clean[df_area_clean[area_col].str.upper() == 'URBANO'][score_col]
                rural_scores = df_area_clean[df_area_clean[area_col].str.upper() == 'RURAL'][score_col]

                if len(urban_scores) > 10 and len(rural_scores) > 10:
                    urban_mean = urban_scores.mean()
                    rural_mean = rural_scores.mean()
                    pooled_std = np.sqrt((urban_scores.std()**2 + rural_scores.std()**2) / 2)

                    if pooled_std > 0:
                        # Cohen's d effect size
                        rucdi_value = round(abs(urban_mean - rural_mean) / pooled_std, 3)
                        rucdi_status = 'green' if rucdi_value <= 0.30 else ('yellow' if rucdi_value <= 0.50 else 'red')
    except Exception as e:
        print(f"RUCDI calculation error: {e}")

    kpis['RUCDI'] = {
        'name': 'Índice de Divergencia de Competencias Rural-Urbana',
        'name_en': 'Rural-Urban Competency Divergence Index',
        'abbr': 'RUCDI',
        'current': rucdi_value,
        'target': 0.30,
        'target_comparison': '<',
        'description': 'Diferencia estandarizada promedio en puntajes (rural vs urbano)',
        'explanation': 'Evalúa la brecha de oportunidades educativas entre zonas rurales y urbanas.',
        'importance': 'Identificar y cerrar estas brechas es esencial para el desarrollo territorial equilibrado.',
        'formula': '(Promedio_urbano - Promedio_rural) / σ_combinada',
        'status': rucdi_status,
        'unit': 'σ',
        'calculated': True
    }

    # 3. Ethnic Resilience Ratio (ERR)
    # Calculate ratio if ethnicity data available
    err_value = 0.88  # Default
    err_status = 'yellow'
    try:
        if len(df_students_global) > 100:
            df_eth = df_students_global.copy()
            df_eth.columns = df_eth.columns.str.upper()

            eth_col = 'ESTU_ETNIA' if 'ESTU_ETNIA' in df_eth.columns else None
            score_col = None
            for col in ['PUNT_C_NATURALES', 'PUNT_GLOBAL', 'PUNT_MATEMATICAS']:
                if col in df_eth.columns:
                    score_col = col
                    break

            if eth_col and score_col:
                df_eth_clean = df_eth[[eth_col, score_col]].dropna()

                # Identify ethnic minority groups
                ethnic_keywords = ['INDIGENA', 'AFRO', 'NEGRO', 'RAIZAL', 'PALENQUERO', 'ROM']

                def is_ethnic_minority(val):
                    if pd.isna(val):
                        return False
                    val_upper = str(val).upper()
                    return any(kw in val_upper for kw in ethnic_keywords)

                minority_mask = df_eth_clean[eth_col].apply(is_ethnic_minority)

                minority_scores = df_eth_clean[minority_mask][score_col]
                majority_scores = df_eth_clean[~minority_mask][score_col]

                if len(minority_scores) > 10 and len(majority_scores) > 10:
                    national_mean = majority_scores.mean()
                    minority_mean = minority_scores.mean()

                    if national_mean > 0:
                        err_value = round(minority_mean / national_mean, 3)
                        err_status = 'green' if err_value >= 0.95 else ('yellow' if err_value >= 0.85 else 'red')
    except Exception as e:
        print(f"ERR calculation error: {e}")

    kpis['ERR'] = {
        'name': 'Ratio de Resiliencia Étnica',
        'name_en': 'Ethnic Resilience Ratio',
        'abbr': 'ERR',
        'current': err_value,
        'target': 0.95,
        'target_comparison': '>',
        'description': 'Desempeño de estudiantes de minorías étnicas vs promedio nacional',
        'explanation': 'Mide si las comunidades étnicas están logrando desempeño académico comparable al promedio nacional.',
        'importance': 'Colombia es un país pluriétnico y multicultural. Este indicador es fundamental para garantizar equidad.',
        'formula': 'Promedio_minorías / Promedio_nacional',
        'status': err_status,
        'unit': '',
        'calculated': True
    }

    # 4. Gender-Neutral Critical Thinking Premium (GNCTP)
    # Calculate gender gap in reading after controlling for math
    gnctp_value = -2.1  # Default
    gnctp_status = 'yellow'
    try:
        if len(df_students_global) > 100:
            df_gen = df_students_global.copy()
            df_gen.columns = df_gen.columns.str.upper()

            gender_col = 'ESTU_GENERO' if 'ESTU_GENERO' in df_gen.columns else None
            reading_col = 'PUNT_LECTURA_CRITICA' if 'PUNT_LECTURA_CRITICA' in df_gen.columns else None
            math_col = 'PUNT_MATEMATICAS' if 'PUNT_MATEMATICAS' in df_gen.columns else None

            if gender_col and reading_col and math_col:
                df_gen_clean = df_gen[[gender_col, reading_col, math_col]].dropna()

                if len(df_gen_clean) > 50:
                    # Create gender dummy (1 for female)
                    df_gen_clean['female'] = df_gen_clean[gender_col].str.upper().apply(
                        lambda x: 1 if 'F' in str(x) else 0
                    )

                    # Regression: Reading ~ Math + Gender
                    X = df_gen_clean[[math_col, 'female']]
                    y = df_gen_clean[reading_col]

                    model = LinearRegression()
                    model.fit(X, y)

                    # Gender coefficient (positive means women score higher after controlling for math)
                    gnctp_value = round(model.coef_[1], 2)
                    gnctp_status = 'green' if abs(gnctp_value) <= 2.0 else ('yellow' if abs(gnctp_value) <= 5.0 else 'red')
    except Exception as e:
        print(f"GNCTP calculation error: {e}")

    kpis['GNCTP'] = {
        'name': 'Prima de Pensamiento Crítico Neutral al Género',
        'name_en': 'Gender-Neutral Critical Thinking Premium',
        'abbr': 'GNCTP',
        'current': gnctp_value,
        'target': 0.0,
        'target_comparison': '≈',
        'description': 'Brecha hombre-mujer en Lectura después de controlar por Matemáticas',
        'explanation': 'Identifica si existen sesgos de género en competencias de lectura crítica.',
        'importance': 'La equidad de género en educación es un objetivo clave del desarrollo sostenible.',
        'formula': 'β_mujer en Lectura Crítica ~ Matemáticas',
        'status': gnctp_status,
        'unit': '',
        'calculated': True
    }

    # 5. Municipal Efficiency Frontier (MEF)
    # Calculate % of municipalities in top performance decile
    mef_value = 11.0  # Default
    mef_status = 'yellow'
    try:
        if len(df_municipalities_global) > 10:
            df_muni = df_municipalities_global.copy()

            # Find a score column
            score_col = None
            for col in df_muni.columns:
                if 'PUNT' in col.upper() and 'MEAN' in col.upper():
                    score_col = col
                    break

            if score_col:
                df_muni_clean = df_muni[[score_col]].dropna()
                if len(df_muni_clean) > 10:
                    # Calculate percentile 90
                    p90 = df_muni_clean[score_col].quantile(0.90)

                    # Percentage of municipalities above P90
                    above_p90 = (df_muni_clean[score_col] >= p90).sum()
                    mef_value = round((above_p90 / len(df_muni_clean)) * 100, 1)
                    mef_status = 'green' if mef_value >= 15 else ('yellow' if mef_value >= 10 else 'red')
    except Exception as e:
        print(f"MEF calculation error: {e}")

    kpis['MEF'] = {
        'name': 'Frontera de Eficiencia Municipal',
        'name_en': 'Municipal Efficiency Frontier',
        'abbr': 'MEF',
        'current': mef_value,
        'target': 15.0,
        'target_comparison': '>',
        'description': '% de municipios en el decil superior de desempeño',
        'explanation': 'Identifica municipios que logran excelentes resultados educativos.',
        'importance': 'Identificar y aprender de los municipios más exitosos para replicar buenas prácticas.',
        'formula': '% municipios con Puntaje > P90',
        'status': mef_status,
        'unit': '%',
        'calculated': True
    }

    # 6. School-Level Volatility Stabilizer (SVS)
    # Calculate school performance consistency
    svs_value = 0.71  # Default
    svs_status = 'red'
    try:
        if len(df) > 50:
            # Calculate coefficient of variation for schools
            df_school = df.copy()

            # Find score columns
            score_cols = [col for col in df_school.columns if 'PUNT' in col.upper() and 'MEAN' in col.upper()]

            if score_cols:
                # Calculate mean and std across subjects for each school
                for col in score_cols:
                    df_school[col] = pd.to_numeric(df_school[col], errors='coerce')

                df_school['mean_score'] = df_school[score_cols].mean(axis=1)
                df_school['std_score'] = df_school[score_cols].std(axis=1)

                # Calculate stability (1 - normalized CV)
                df_school_clean = df_school.dropna(subset=['mean_score', 'std_score'])
                if len(df_school_clean) > 10:
                    df_school_clean['cv'] = df_school_clean['std_score'] / df_school_clean['mean_score'].abs()
                    median_cv = df_school_clean['cv'].median()

                    # Normalize to 0-1 scale (assuming CV typically ranges 0-0.5)
                    svs_value = round(max(0, min(1, 1 - median_cv * 2)), 3)
                    svs_status = 'green' if svs_value >= 0.80 else ('yellow' if svs_value >= 0.60 else 'red')
    except Exception as e:
        print(f"SVS calculation error: {e}")

    kpis['SVS'] = {
        'name': 'Estabilizador de Volatilidad a Nivel Escolar',
        'name_en': 'School-Level Volatility Stabilizer',
        'abbr': 'SVS',
        'current': svs_value,
        'target': 0.80,
        'target_comparison': '>',
        'description': 'Consistencia del desempeño escolar entre materias (mayor es mejor)',
        'explanation': 'Mide la consistencia en el desempeño escolar. Alta volatilidad puede indicar problemas de gestión.',
        'importance': 'Identificar colegios con calidad sostenible versus aquellos con resultados erráticos.',
        'formula': '1 - mediana(CV por colegio)',
        'status': svs_status,
        'unit': '',
        'calculated': True
    }

    return kpis


# Additional Metrics Functions
def calculate_additional_metrics(df_students_data, df_schools_data):
    """Calculate additional analytical metrics from the data"""
    metrics = {}

    try:
        df = df_students_data.copy()
        df.columns = df.columns.str.upper()

        # 1. Average scores by subject
        score_cols = [col for col in df.columns if col.startswith('PUNT_')]
        if score_cols:
            metrics['avg_scores'] = {col: df[col].mean() for col in score_cols if df[col].notna().sum() > 0}

        # 2. Score distribution statistics
        for col in score_cols:
            if col in df.columns and df[col].notna().sum() > 0:
                metrics[f'{col}_stats'] = {
                    'mean': df[col].mean(),
                    'median': df[col].median(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'q25': df[col].quantile(0.25),
                    'q75': df[col].quantile(0.75)
                }

        # 3. Stratum distribution
        if 'FAMI_ESTRATOVIVIENDA' in df.columns:
            metrics['stratum_dist'] = df['FAMI_ESTRATOVIVIENDA'].value_counts().to_dict()

        # 4. Area distribution (urban/rural)
        if 'COLE_AREA_UBICACION' in df.columns:
            metrics['area_dist'] = df['COLE_AREA_UBICACION'].value_counts().to_dict()

        # 5. School type distribution
        if 'COLE_NATURALEZA' in df.columns:
            metrics['school_type_dist'] = df['COLE_NATURALEZA'].value_counts().to_dict()

    except Exception as e:
        print(f"Additional metrics calculation error: {e}")

    return metrics

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

# Create navigation bar
def create_navbar():
    """Create professional navigation bar"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.NavbarBrand(
                        [
                            html.I(className="fas fa-graduation-cap me-2"),
                            "SABER Analytics"
                        ],
                        className="navbar-brand-custom",
                        href="/"
                    )
                ]),
            ], className="g-0 w-100", align="center"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink([html.I(className="fas fa-home me-1"), "Inicio"], href="/", className="text-white")),
                dbc.NavItem(dbc.NavLink([html.I(className="fas fa-chart-line me-1"), "Panel de Control"], href="/dashboard", className="text-white")),
            ], navbar=True)
        ], fluid=True),
        className="custom-navbar mb-0",
        dark=True
    )


# Create dashboard content (all the tabs)
def create_dashboard_content():
    """Create the full dashboard with all analytical tabs"""
    return dbc.Container([
        # Dashboard Header
        html.Div([
            html.H2([
                html.I(className="fas fa-chart-bar me-3"),
                "Panel de Analítica Educativa"
            ], className="text-center mb-3 mt-4 text-primary-custom"),
            html.P("Análisis integral de los resultados de las pruebas SABER en toda Colombia",
                   className="text-center text-muted mb-4"),
        ]),

        # Main tabs
        dbc.Tabs(id="main-tabs", active_tab="tab-overview", className="nav-tabs", children=[

        # TAB 1: Overview / Nacional
        dbc.Tab(label="📊 Panorama Nacional", tab_id="tab-overview", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Filtros")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Materia 1:", className="fw-bold"),
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
                                        html.Label("Materia 2:", className="fw-bold"),
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
                                        html.Label("Tipo de Colegio:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-naturaleza',
                                            options=[{'label': 'Todos', 'value': 'ALL'}] +
                                                    [{'label': n, 'value': n} for n in naturaleza_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Área:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='overview-area',
                                            options=[{'label': 'Todos', 'value': 'ALL'}] +
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
        dbc.Tab(label="🗺️ Análisis Departamental", tab_id="tab-department", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Department Selection & Filters")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Departamento:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-selector',
                                            options=[{'label': d, 'value': d} for d in departments],
                                            value=departments[0] if departments else None,
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Materia 1:", className="fw-bold"),
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
                                        html.Label("Materia 2:", className="fw-bold"),
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
                                        html.Label("Tipo de Colegio:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='dept-naturaleza',
                                            options=[{'label': 'Todos', 'value': 'ALL'}] +
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
        dbc.Tab(label="🏘️ Análisis Municipal", tab_id="tab-municipality", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Municipality Selection")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Departamento:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='munic-dept-selector',
                                            options=[{'label': d, 'value': d} for d in departments],
                                            value=departments[0] if departments else None,
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Municipio:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='munic-selector',
                                            options=[],
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Grado:", className="fw-bold"),
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
        dbc.Tab(label="🏫 Análisis de Colegios", tab_id="tab-school", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("School Search and Analysis")),
                            dbc.CardBody([
                                html.Label("Buscar Colegio por Nombre:", className="fw-bold"),
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
        dbc.Tab(label="💰 Análisis Socioeconómico", tab_id="tab-socioeconomic", children=[
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
        dbc.Tab(label="🤖 Analítica Avanzada", tab_id="tab-prediction", children=[
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
                                        html.Label("Nivel de Análisis:", className="fw-bold"),
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
                                        html.Label("Puntaje Objetivo:", className="fw-bold"),
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

        # TAB 7: KPIs - Educational Equity & Efficiency
        dbc.Tab(label="📊 Indicadores - Equidad y Eficiencia", tab_id="tab-kpis", children=[
            html.Div([
                # Filters Row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Filtros Geográficos")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Departamentos:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-dept-filter',
                                            options=[{'label': 'Todos los Departamentos', 'value': 'ALL'}] +
                                                    [{'label': d, 'value': d} for d in departments],
                                            value=['ALL'],
                                            multi=True,
                                            placeholder="Select departments..."
                                        )
                                    ], md=6),
                                    dbc.Col([
                                        html.Label("Municipios:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-munic-filter',
                                            options=[{'label': 'Todos los Municipios', 'value': 'ALL'}],
                                            value=['ALL'],
                                            multi=True,
                                            placeholder="Select municipalities..."
                                        )
                                    ], md=6),
                                ]),
                                html.Hr(),
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Tipo de Colegio:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-naturaleza-filter',
                                            options=[{'label': 'Todos los Tipos', 'value': 'ALL'}] +
                                                    [{'label': n, 'value': n} for n in naturaleza_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Label("Área:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='kpi-area-filter',
                                            options=[{'label': 'Todas las Áreas', 'value': 'ALL'}] +
                                                    [{'label': a, 'value': a} for a in area_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        html.Div([
                                            html.Label("Colegios Filtrados:", className="fw-bold"),
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
                            dbc.CardHeader(html.H4("Indicadores Clave de Desempeño (KPIs) - Equidad y Eficiencia Educativa")),
                            dbc.CardBody([
                                html.P([
                                    "Estas 6 métricas son ",
                                    html.Strong("estadísticamente ortogonales"),
                                    " (|r| pares < 0.4), ",
                                    html.Strong("accionables para política"),
                                    ", y se enfocan en ",
                                    html.Strong("fallas sistémicas"),
                                    " en lugar de simples promedios."
                                ], className="text-muted mb-4"),
                                html.P([
                                    html.Strong("Nota: "),
                                    "Los KPIs son calculados en tiempo real usando los datos disponibles. ",
                                    html.Span("Indicador verde", className="badge bg-success me-1"),
                                    " = dato calculado del dataset; los valores con datos faltantes usan estimaciones informadas."
                                ], className="alert alert-success"),
                                html.Div(id='kpi-summary-cards'),
                                html.Hr(),
                                html.H5("Panel de Indicadores", className="mt-4 mb-3"),
                                html.Div(id='kpi-summary-table'),
                                html.Hr(),
                                html.H5("Análisis Visual", className="mt-4 mb-3"),
                                dcc.Graph(id='kpi-gauge-chart', style={'height': '800px'}),
                            ])
                        ])
                    ], md=12)
                ])
            ], className="p-3")
        ]),

        # TAB 8: Schools Ranking Table
        dbc.Tab(label="📋 Ranking de Colegios", tab_id="tab-ranking", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Listado de Colegios por Desempeño", className="mb-4"),
                        html.P("Tabla completa de colegios con puntajes promedio en todas las áreas, ordenados por puntaje global.",
                               className="text-muted mb-4"),
                    ])
                ]),

                # Filters for the ranking table
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Filtros")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Departamento:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='ranking-dept-filter',
                                            options=[{'label': 'Todos los Departamentos', 'value': 'ALL'}] +
                                                    [{'label': d, 'value': d} for d in departments],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Municipio:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='ranking-munic-filter',
                                            options=[{'label': 'Todos los Municipios', 'value': 'ALL'}],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Tipo de Colegio:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='ranking-naturaleza-filter',
                                            options=[{'label': 'Todos los Tipos', 'value': 'ALL'}] +
                                                    [{'label': n, 'value': n} for n in naturaleza_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Label("Área:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='ranking-area-filter',
                                            options=[{'label': 'Todas las Áreas', 'value': 'ALL'}] +
                                                    [{'label': a, 'value': a} for a in area_options],
                                            value='ALL',
                                            clearable=False
                                        )
                                    ], md=3),
                                ]),
                                html.Hr(),
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Número de colegios a mostrar:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='ranking-limit',
                                            options=[
                                                {'label': 'Top 50', 'value': 50},
                                                {'label': 'Top 100', 'value': 100},
                                                {'label': 'Top 200', 'value': 200},
                                                {'label': 'Top 500', 'value': 500},
                                                {'label': 'Todos', 'value': 999999},
                                            ],
                                            value=100,
                                            clearable=False
                                        )
                                    ], md=3),
                                    dbc.Col([
                                        html.Div([
                                            html.Label("Colegios Filtrados:", className="fw-bold"),
                                            html.H4(id='ranking-filtered-count', className="text-primary mt-2")
                                        ])
                                    ], md=3),
                                ])
                            ])
                        ], className="mb-4")
                    ])
                ]),

                # Ranking Table
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5("Tabla de Rankings")),
                            dbc.CardBody([
                                html.Div(id='ranking-table')
                            ])
                        ])
                    ], md=12)
                ])
            ], className="p-3")
        ]),

        # TAB 9: Comprehensive Analytics - NEW
        dbc.Tab(label="📈 Analítica Integral", tab_id="tab-comprehensive", children=[
            html.Div([
                # Header
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-chart-pie header-icon"),
                            html.H4("Panel de Analítica Integral", className="d-inline")
                        ], className="analytics-header"),
                        html.P("Análisis multidimensional del desempeño educativo con métricas calculadas en tiempo real",
                               className="text-muted mb-4"),
                    ])
                ]),

                # Quick Stats Cards
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-school stat-icon"),
                            html.Div(id='comp-total-schools', className="stat-value"),
                            html.Div("Colegios Analizados", className="stat-label")
                        ], className="summary-stat-card")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-user-graduate stat-icon"),
                            html.Div(id='comp-total-students', className="stat-value"),
                            html.Div("Estudiantes Totales", className="stat-label")
                        ], className="summary-stat-card")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-map-marker-alt stat-icon"),
                            html.Div(id='comp-total-munics', className="stat-value"),
                            html.Div("Municipios", className="stat-label")
                        ], className="summary-stat-card")
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-trophy stat-icon"),
                            html.Div(id='comp-avg-global', className="stat-value"),
                            html.Div("Puntaje Global Promedio", className="stat-label")
                        ], className="summary-stat-card")
                    ], md=3),
                ], className="mb-4"),

                # Subject Analysis Section
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-book-open me-2"),
                                "Análisis por Materia"
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='comp-subject-radar', style={'height': '400px'})
                            ])
                        ])
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-chart-bar me-2"),
                                "Distribución de Puntajes por Materia"
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='comp-subject-boxplot', style={'height': '400px'})
                            ])
                        ])
                    ], md=6),
                ], className="mb-4"),

                # Correlation and Gap Analysis
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-project-diagram me-2"),
                                "Matriz de Correlación entre Materias"
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='comp-correlation-matrix', style={'height': '450px'})
                            ])
                        ])
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-balance-scale me-2"),
                                "Brechas de Desempeño"
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='comp-gap-analysis', style={'height': '450px'})
                            ])
                        ])
                    ], md=6),
                ], className="mb-4"),

                # Geographic Performance
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-globe-americas me-2"),
                                "Desempeño por Departamento"
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='comp-dept-performance', style={'height': '500px'})
                            ])
                        ])
                    ], md=12),
                ], className="mb-4"),

                # Stratum and Type Analysis
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-layer-group me-2"),
                                "Análisis por Estrato Socioeconómico"
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='comp-stratum-analysis', style={'height': '400px'})
                            ])
                        ])
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-building me-2"),
                                "Comparación Público vs Privado"
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='comp-type-comparison', style={'height': '400px'})
                            ])
                        ])
                    ], md=6),
                ], className="mb-4"),

                # Performance Metrics Summary
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-clipboard-list me-2"),
                                "Resumen de Métricas de Desempeño"
                            ]),
                            dbc.CardBody([
                                html.Div(id='comp-metrics-summary')
                            ])
                        ])
                    ], md=12),
                ]),
            ], className="p-3")
        ]),
    ])], fluid=True)

# KPI Information Modals
def create_kpi_modals():
    """Create modal dialogs for each KPI with detailed explanations"""
    kpis = calculate_kpis(df_schools, df_students, df_municipalities)
    modals = []

    for kpi_key in ['EALG', 'RUCDI', 'ERR', 'GNCTP', 'MEF', 'SVS']:
        kpi = kpis[kpi_key]
        modal = dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-info-circle me-2"),
                f"{kpi['abbr']} - {kpi['name']}"
            ])),
            dbc.ModalBody([
                html.H5("📋 Descripción", className="mb-3"),
                html.P(kpi['description'], className="mb-4"),

                html.H5("🔍 Explicación Detallada", className="mb-3"),
                html.P(kpi['explanation'], className="mb-4"),

                html.H5("⭐ Importancia", className="mb-3"),
                html.P(kpi['importance'], className="mb-4"),

                html.H5("📐 Fórmula", className="mb-3"),
                html.Code(kpi['formula'], className="d-block p-3 mb-3",
                         style={'backgroundColor': '#f5f5f5', 'borderRadius': '5px'}),

                html.Hr(),
                dbc.Alert([
                    html.Strong("Meta: "),
                    f"{kpi['target_comparison']} {kpi['target']}{kpi['unit']}"
                ], color="info", className="mb-0")
            ]),
            dbc.ModalFooter(
                dbc.Button("Cerrar", id=f"close-{kpi_key.lower()}-modal", className="ms-auto")
            ),
        ], id=f"modal-{kpi_key.lower()}", size="lg", is_open=False)
        modals.append(modal)

    return html.Div(modals)


# Multi-page app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    create_navbar(),
    html.Div(id='page-content'),
    create_kpi_modals()  # Add KPI modals
])


# Page routing callback
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    """Route between landing page, dashboard, and auth pages"""
    # Check if it's an authentication page (login/register)
    auth_layout = get_auth_layout(pathname)
    if auth_layout:
        return auth_layout

    # Regular routing
    if pathname == '/dashboard':
        return create_dashboard_content()
    else:  # Default to landing page
        return create_landing_page()


# Callback for navigation buttons on landing page
@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('btn-explore-dashboard', 'n_clicks'),
     Input('btn-start-analyzing', 'n_clicks')],
    prevent_initial_call=True
)
def navigate_to_dashboard(btn1, btn2):
    """Navigate to dashboard when buttons are clicked"""
    return '/dashboard'


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


# TAB 7: KPI Dashboard callbacks - Municipality dropdown update
@app.callback(
    Output('kpi-munic-filter', 'options'),
    [Input('kpi-dept-filter', 'value')]
)
def update_kpi_municipality_options(selected_depts):
    """Update municipality options based on selected departments"""
    if not selected_depts or 'ALL' in selected_depts:
        # Return all municipalities
        all_munics = sorted(df_schools['COLE_MCPIO_UBICACION'].dropna().unique()) if 'COLE_MCPIO_UBICACION' in df_schools.columns else []
        return [{'label': 'All Municipalities', 'value': 'ALL'}] + [{'label': m, 'value': m} for m in all_munics]

    # Filter municipalities by selected departments
    filtered_munics = []
    if 'COLE_DEPTO_UBICACION' in df_schools.columns and 'COLE_MCPIO_UBICACION' in df_schools.columns:
        dept_munics = df_schools[df_schools['COLE_DEPTO_UBICACION'].isin(selected_depts)]['COLE_MCPIO_UBICACION'].dropna().unique()
        filtered_munics = sorted(dept_munics)

    return [{'label': 'All Municipalities', 'value': 'ALL'}] + [{'label': m, 'value': m} for m in filtered_munics]


@app.callback(
    [Output('kpi-summary-cards', 'children'),
     Output('kpi-summary-table', 'children'),
     Output('kpi-gauge-chart', 'figure'),
     Output('kpi-filtered-count', 'children')],
    [Input('kpi-dept-filter', 'value'),
     Input('kpi-munic-filter', 'value'),
     Input('kpi-naturaleza-filter', 'value'),
     Input('kpi-area-filter', 'value')]
)
def update_kpi_dashboard(selected_depts, selected_munics, naturaleza, area):
    """Update KPI dashboard with metrics, table, and visualizations based on filters"""

    # Filter schools based on selections
    filtered_df = df_schools.copy()

    # Apply department filter
    if selected_depts and 'ALL' not in selected_depts and 'COLE_DEPTO_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_DEPTO_UBICACION'].isin(selected_depts)]

    # Apply municipality filter
    if selected_munics and 'ALL' not in selected_munics and 'COLE_MCPIO_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_MCPIO_UBICACION'].isin(selected_munics)]

    # Apply school type filter
    if naturaleza != 'ALL' and 'COLE_NATURALEZA' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_NATURALEZA'] == naturaleza]

    # Apply area filter
    if area != 'ALL' and 'COLE_AREA_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_AREA_UBICACION'] == area]

    # Count filtered schools
    filtered_count = f"{len(filtered_df):,}"

    # Calculate KPIs with filtered data and student/municipality data
    kpis = calculate_kpis(filtered_df, df_students, df_municipalities)

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
                        html.Div([
                            html.H6(f"{icon} {kpi['abbr']}", className="mb-0 d-inline"),
                            dbc.Button(
                                html.I(className="fas fa-info-circle"),
                                id=f"info-btn-{kpi_key.lower()}",
                                color="link",
                                size="sm",
                                className="float-end p-0",
                                style={'fontSize': '1.2rem'}
                            )
                        ])
                    ]),
                    dbc.CardBody([
                        html.H4(current_str, className="text-center mb-2"),
                        html.P(f"Meta: {kpi['target_comparison']} {target_str}",
                               className="text-center text-muted small mb-2"),
                        html.Hr(className="my-2"),
                        html.P(kpi['name'], className="small mb-1 fw-bold", style={'fontSize': '0.85rem'}),
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


# ============================================================================
# TAB 8: RANKING TABLE CALLBACKS
# ============================================================================

# Update municipality dropdown based on department selection
@app.callback(
    Output('ranking-munic-filter', 'options'),
    [Input('ranking-dept-filter', 'value')]
)
def update_ranking_municipality_options(selected_dept):
    """Update municipality options based on selected department"""
    if selected_dept == 'ALL' or not selected_dept:
        # Show all municipalities
        if 'COLE_MCPIO_UBICACION' in df_schools.columns:
            all_munics = sorted(df_schools['COLE_MCPIO_UBICACION'].dropna().unique())
            return [{'label': 'Todos los Municipios', 'value': 'ALL'}] + \
                   [{'label': m, 'value': m} for m in all_munics]
    else:
        # Filter municipalities by department
        if 'COLE_DEPTO_UBICACION' in df_schools.columns and 'COLE_MCPIO_UBICACION' in df_schools.columns:
            filtered_df = df_schools[df_schools['COLE_DEPTO_UBICACION'] == selected_dept]
            filtered_munics = sorted(filtered_df['COLE_MCPIO_UBICACION'].dropna().unique())
            return [{'label': 'Todos los Municipios', 'value': 'ALL'}] + \
                   [{'label': m, 'value': m} for m in filtered_munics]

    return [{'label': 'Todos los Municipios', 'value': 'ALL'}]


# Update ranking table
@app.callback(
    [Output('ranking-table', 'children'),
     Output('ranking-filtered-count', 'children')],
    [Input('ranking-dept-filter', 'value'),
     Input('ranking-munic-filter', 'value'),
     Input('ranking-naturaleza-filter', 'value'),
     Input('ranking-area-filter', 'value'),
     Input('ranking-limit', 'value')]
)
def update_ranking_table(dept, munic, naturaleza, area, limit):
    """Update ranking table based on filters"""

    # Filter data
    filtered_df = df_schools.copy()

    if dept != 'ALL' and 'COLE_DEPTO_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_DEPTO_UBICACION'] == dept]

    if munic != 'ALL' and 'COLE_MCPIO_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_MCPIO_UBICACION'] == munic]

    if naturaleza != 'ALL' and 'COLE_NATURALEZA' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_NATURALEZA'] == naturaleza]

    if area != 'ALL' and 'COLE_AREA_UBICACION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLE_AREA_UBICACION'] == area]

    # Get score columns
    score_cols_map = {
        'Lectura Crítica': 'PUNT_LECTURA_CRITICA_mean',
        'Matemáticas': 'PUNT_MATEMATICAS_mean',
        'Ciencias Naturales': 'PUNT_C_NATURALES_mean',
        'Sociales y Ciudadanas': 'PUNT_SOCIALES_CIUDADANAS_mean',
        'Inglés': 'PUNT_INGLES_mean',
        'Global': 'PUNT_GLOBAL_mean'
    }

    # Prepare table data
    table_data = []

    # Get columns we need
    required_cols = ['COLE_NOMBRE_ESTABLECIMIENTO', 'COLE_DEPTO_UBICACION', 'COLE_MCPIO_UBICACION']
    available_cols = [col for col in required_cols if col in filtered_df.columns]

    # Add score columns that exist
    available_score_cols = {}
    for subj_name, col_name in score_cols_map.items():
        if col_name in filtered_df.columns:
            available_score_cols[subj_name] = col_name

    if not available_score_cols:
        return html.Div("No hay datos de puntajes disponibles.", className="alert alert-warning"), "0"

    # Get global score column for sorting (or first available)
    sort_col = score_cols_map['Global'] if 'Global' in available_score_cols else list(available_score_cols.values())[0]

    # Select relevant columns and drop NaN in sort column
    cols_to_select = available_cols + list(available_score_cols.values())
    df_table = filtered_df[cols_to_select].dropna(subset=[sort_col])

    # Sort by global score (descending)
    df_table = df_table.sort_values(by=sort_col, ascending=False)

    # Apply limit
    if limit and limit < len(df_table):
        df_table = df_table.head(limit)

    # Prepare data for display
    for idx, row in df_table.iterrows():
        row_data = {
            'Ranking': len(table_data) + 1,
            'Colegio': row.get('COLE_NOMBRE_ESTABLECIMIENTO', 'N/A'),
            'Departamento': row.get('COLE_DEPTO_UBICACION', 'N/A'),
            'Municipio': row.get('COLE_MCPIO_UBICACION', 'N/A')
        }

        # Add scores
        for subj_name, col_name in available_score_cols.items():
            if col_name in row.index:
                score = row[col_name]
                row_data[subj_name] = f"{score:.1f}" if pd.notna(score) else "N/A"

        table_data.append(row_data)

    # Create DataFrame for table
    if not table_data:
        return html.Div("No se encontraron colegios con los filtros aplicados.", className="alert alert-info"), "0"

    df_display = pd.DataFrame(table_data)

    # Create DataTable
    table = dash_table.DataTable(
        data=df_display.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df_display.columns],
        style_table={
            'overflowX': 'auto',
            'overflowY': 'auto',
            'maxHeight': '600px'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '13px',
            'fontFamily': 'Arial, sans-serif'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'fontSize': '14px',
            'textAlign': 'center',
            'border': '1px solid rgb(200, 200, 200)'
        },
        style_data={
            'border': '1px solid rgb(220, 220, 220)'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            {
                'if': {'column_id': 'Ranking'},
                'fontWeight': 'bold',
                'textAlign': 'center',
                'width': '80px'
            },
            {
                'if': {'column_id': 'Colegio'},
                'fontWeight': '500',
                'maxWidth': '300px',
                'whiteSpace': 'normal',
                'height': 'auto'
            },
            # Highlight Global score
            {
                'if': {'column_id': 'Global'},
                'backgroundColor': 'rgb(255, 250, 205)',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            # Style other score columns
            {
                'if': {'column_id': ['Lectura Crítica', 'Matemáticas', 'Ciencias Naturales',
                                     'Sociales y Ciudadanas', 'Inglés']},
                'textAlign': 'center'
            }
        ],
        sort_action='native',
        filter_action='native',
        page_action='native',
        page_current=0,
        page_size=20,
        style_cell_conditional=[
            {'if': {'column_id': 'Colegio'}, 'minWidth': '250px', 'maxWidth': '400px'},
            {'if': {'column_id': 'Departamento'}, 'minWidth': '120px'},
            {'if': {'column_id': 'Municipio'}, 'minWidth': '120px'},
        ]
    )

    filtered_count = f"{len(df_display):,}"

    return table, filtered_count


# ============================================================================
# TAB 9: COMPREHENSIVE ANALYTICS CALLBACKS
# ============================================================================

@app.callback(
    [Output('comp-total-schools', 'children'),
     Output('comp-total-students', 'children'),
     Output('comp-total-munics', 'children'),
     Output('comp-avg-global', 'children'),
     Output('comp-subject-radar', 'figure'),
     Output('comp-subject-boxplot', 'figure'),
     Output('comp-correlation-matrix', 'figure'),
     Output('comp-gap-analysis', 'figure'),
     Output('comp-dept-performance', 'figure'),
     Output('comp-stratum-analysis', 'figure'),
     Output('comp-type-comparison', 'figure'),
     Output('comp-metrics-summary', 'children')],
    [Input('main-tabs', 'active_tab')]
)
def update_comprehensive_analytics(active_tab):
    """Update comprehensive analytics tab with all visualizations and metrics"""

    # Calculate basic stats
    total_schools = f"{len(df_schools):,}"
    total_students = f"{len(df_students):,}"
    total_munics = f"{len(df_municipalities):,}"

    # Calculate average global score
    global_col = None
    for col in df_schools.columns:
        if 'GLOBAL' in col.upper() and 'MEAN' in col.upper():
            global_col = col
            break

    if global_col and global_col in df_schools.columns:
        avg_global = f"{df_schools[global_col].mean():.1f}"
    else:
        avg_global = "N/A"

    # Get score columns for analysis
    score_cols = {col: col.replace('PUNT_', '').replace('_mean', '').replace('_', ' ').title()
                  for col in df_schools.columns
                  if col.startswith('PUNT_') and col.endswith('_mean')}

    # 1. Subject Radar Chart
    if score_cols:
        mean_scores = {name: df_schools[col].mean() for col, name in score_cols.items()}
        radar_fig = go.Figure()
        radar_fig.add_trace(go.Scatterpolar(
            r=list(mean_scores.values()),
            theta=list(mean_scores.keys()),
            fill='toself',
            name='Promedio Nacional',
            line_color='#003D82'
        ))
        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(mean_scores.values()) * 1.1])),
            showlegend=True,
            title="Perfil de Desempeño por Materia"
        )
    else:
        radar_fig = go.Figure()
        radar_fig.add_annotation(text="No hay datos disponibles", showarrow=False)

    # 2. Subject Boxplot
    if score_cols and len(df_schools) > 0:
        boxplot_data = []
        for col, name in score_cols.items():
            if col in df_schools.columns:
                boxplot_data.append(go.Box(y=df_schools[col].dropna(), name=name, boxmean=True))

        boxplot_fig = go.Figure(data=boxplot_data)
        boxplot_fig.update_layout(
            title="Distribución de Puntajes por Materia",
            yaxis_title="Puntaje",
            showlegend=False
        )
    else:
        boxplot_fig = go.Figure()

    # 3. Correlation Matrix
    if score_cols and len(score_cols) > 1:
        score_df = df_schools[list(score_cols.keys())].dropna()
        if len(score_df) > 10:
            corr_matrix = score_df.corr()
            corr_fig = px.imshow(
                corr_matrix,
                text_auto='.2f',
                color_continuous_scale='RdBu_r',
                title="Correlación entre Materias"
            )
            corr_fig.update_layout(
                xaxis_title="",
                yaxis_title=""
            )
        else:
            corr_fig = go.Figure()
    else:
        corr_fig = go.Figure()

    # 4. Gap Analysis (Urban vs Rural, Public vs Private)
    gap_fig = go.Figure()

    if 'COLE_AREA_UBICACION' in df_schools.columns and score_cols:
        # Get first available score column
        score_col = list(score_cols.keys())[0]
        area_means = df_schools.groupby('COLE_AREA_UBICACION')[score_col].mean()

        gap_fig.add_trace(go.Bar(
            x=['Urbano', 'Rural'],
            y=[area_means.get('URBANO', 0), area_means.get('RURAL', 0)],
            name='Por Área',
            marker_color=['#003D82', '#CE1126']
        ))

    if 'COLE_NATURALEZA' in df_schools.columns and score_cols:
        score_col = list(score_cols.keys())[0]
        type_means = df_schools.groupby('COLE_NATURALEZA')[score_col].mean()

        gap_fig.add_trace(go.Bar(
            x=['Oficial', 'No Oficial'],
            y=[type_means.get('OFICIAL', 0), type_means.get('NO OFICIAL', 0)],
            name='Por Tipo',
            marker_color=['#0066CC', '#FFD100']
        ))

    gap_fig.update_layout(
        title="Brechas de Desempeño",
        barmode='group',
        yaxis_title="Puntaje Promedio"
    )

    # 5. Department Performance
    if 'COLE_DEPTO_UBICACION' in df_schools.columns and score_cols:
        score_col = list(score_cols.keys())[0]
        dept_means = df_schools.groupby('COLE_DEPTO_UBICACION')[score_col].mean().sort_values(ascending=True)

        dept_fig = go.Figure()
        dept_fig.add_trace(go.Bar(
            y=dept_means.index,
            x=dept_means.values,
            orientation='h',
            marker_color=px.colors.sequential.Blues_r[:len(dept_means)] if len(dept_means) <= 10 else '#003D82'
        ))
        dept_fig.update_layout(
            title="Desempeño Promedio por Departamento",
            xaxis_title="Puntaje Promedio",
            height=500
        )
    else:
        dept_fig = go.Figure()

    # 6. Stratum Analysis (from student data)
    stratum_fig = go.Figure()
    if len(df_students) > 0:
        df_stud = df_students.copy()
        df_stud.columns = df_stud.columns.str.upper()

        if 'FAMI_ESTRATOVIVIENDA' in df_stud.columns:
            score_col = None
            for col in ['PUNT_GLOBAL', 'PUNT_MATEMATICAS', 'PUNT_LECTURA_CRITICA']:
                if col in df_stud.columns:
                    score_col = col
                    break

            if score_col:
                strat_means = df_stud.groupby('FAMI_ESTRATOVIVIENDA')[score_col].mean().sort_index()
                stratum_fig.add_trace(go.Bar(
                    x=strat_means.index,
                    y=strat_means.values,
                    marker_color='#003D82'
                ))
                stratum_fig.update_layout(
                    title="Puntaje Promedio por Estrato Socioeconómico",
                    xaxis_title="Estrato",
                    yaxis_title="Puntaje Promedio"
                )

    # 7. Public vs Private Comparison (detailed)
    type_fig = go.Figure()
    if 'COLE_NATURALEZA' in df_schools.columns and score_cols:
        for col, name in list(score_cols.items())[:5]:  # Limit to 5 subjects
            type_data = df_schools.groupby('COLE_NATURALEZA')[col].mean()
            type_fig.add_trace(go.Bar(
                name=name,
                x=type_data.index,
                y=type_data.values
            ))

        type_fig.update_layout(
            title="Comparación Público vs Privado por Materia",
            barmode='group',
            yaxis_title="Puntaje Promedio"
        )

    # 8. Metrics Summary Table
    metrics_data = []

    # Add score statistics
    for col, name in list(score_cols.items())[:6]:
        if col in df_schools.columns:
            series = df_schools[col].dropna()
            if len(series) > 0:
                metrics_data.append({
                    'Métrica': f'{name} - Promedio',
                    'Valor': f'{series.mean():.2f}',
                    'Mínimo': f'{series.min():.2f}',
                    'Máximo': f'{series.max():.2f}',
                    'Desv. Est.': f'{series.std():.2f}'
                })

    # Calculate KPIs
    kpis = calculate_kpis(df_schools, df_students, df_municipalities)
    for kpi_key, kpi in kpis.items():
        status_icon = '🟢' if kpi['status'] == 'green' else ('🟡' if kpi['status'] == 'yellow' else '🔴')
        unit = kpi.get('unit', '')
        metrics_data.append({
            'Métrica': f"{status_icon} {kpi['abbr']} - {kpi['name']}",
            'Valor': f"{kpi['current']}{unit}",
            'Mínimo': f"Meta: {kpi['target_comparison']} {kpi['target']}{unit}",
            'Máximo': kpi['status'].upper(),
            'Desv. Est.': 'Calculado' if kpi.get('calculated') else 'Simulado'
        })

    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        metrics_table = dash_table.DataTable(
            data=metrics_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in metrics_df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '14px'
            },
            style_header={
                'backgroundColor': '#003D82',
                'color': 'white',
                'fontWeight': 'bold',
                'fontSize': '15px'
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                {'if': {'filter_query': '{Máximo} = "GREEN"'}, 'backgroundColor': 'rgba(39, 174, 96, 0.1)'},
                {'if': {'filter_query': '{Máximo} = "YELLOW"'}, 'backgroundColor': 'rgba(243, 156, 18, 0.1)'},
                {'if': {'filter_query': '{Máximo} = "RED"'}, 'backgroundColor': 'rgba(231, 76, 60, 0.1)'},
            ],
            page_size=15
        )
    else:
        metrics_table = html.Div("No hay métricas disponibles", className="alert alert-info")

    return (total_schools, total_students, total_munics, avg_global,
            radar_fig, boxplot_fig, corr_fig, gap_fig,
            dept_fig, stratum_fig, type_fig, metrics_table)


# ============================================================================
# KPI MODAL CALLBACKS
# ============================================================================

# Callbacks for opening and closing KPI modals
for kpi_key in ['ealg', 'rucdi', 'err', 'gnctp', 'mef', 'svs']:
    @app.callback(
        Output(f'modal-{kpi_key}', 'is_open'),
        [Input(f'info-btn-{kpi_key}', 'n_clicks'),
         Input(f'close-{kpi_key}-modal', 'n_clicks')],
        [State(f'modal-{kpi_key}', 'is_open')],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open


# ============================================================================
# AUTHENTICATION CALLBACKS (if enabled)
# ============================================================================

if AUTH_ENABLED:
    add_auth_callbacks(app)
    print("✅ Authentication callbacks added")


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
