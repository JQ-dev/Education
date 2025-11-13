"""
Data Loader Utility for SABER Dashboard Applications
Handles loading and preparing data from multiple sources and years
"""

import pandas as pd
import numpy as np
import glob
import os
from typing import Dict, List, Tuple

# Available subjects in Saber 11
SABER11_SUBJECTS = {
    'lectura_critica': 'Reading/Language',
    'matematicas': 'Mathematics',
    'c_naturales': 'Natural Sciences',
    'sociales_ciudadanas': 'Social Sciences',
    'ingles': 'English',
    'global': 'Global Score'
}

def load_saber11_student_data(years='all', sample_size=None):
    """
    Load Saber 11 student-level data from multiple sources

    Args:
        years: 'all', 'latest', or list of years like [2019, 2024]
        sample_size: Maximum records to load per file (None = all)

    Returns:
        DataFrame with student-level data
    """
    all_data = []

    # Pattern 1: Parquet files (fastest)
    parquet_files = glob.glob('*.parquet') + glob.glob('Examen_Saber_11*.parquet')

    for file in parquet_files:
        try:
            print(f"Loading {file}...")
            df = pd.read_parquet(file)
            df.columns = df.columns.str.upper()

            # Extract year
            if 'PERIODO' in df.columns:
                df['YEAR'] = df['PERIODO'].apply(lambda x: int(str(int(x))[:4]) if pd.notna(x) else None)

            all_data.append(df)
            print(f"  ✓ Loaded {len(df):,} records")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Pattern 2: CSV files
    csv_patterns = ['Saber_11__*.csv', 'ICFES_*.csv']

    for pattern in csv_patterns:
        for file in glob.glob(pattern):
            try:
                print(f"Loading {file}...")
                df = pd.read_csv(file, low_memory=False)
                df.columns = df.columns.str.upper()

                # Extract year
                if 'PERIODO' in df.columns:
                    df['YEAR'] = df['PERIODO'].apply(lambda x: int(str(int(x))[:4]) if pd.notna(x) else None)
                else:
                    # Try from filename
                    import re
                    year_match = re.search(r'20\d{2}', file)
                    if year_match:
                        df['YEAR'] = int(year_match.group())

                all_data.append(df)
                print(f"  ✓ Loaded {len(df):,} records")
            except Exception as e:
                print(f"  ✗ Error: {e}")

    # Pattern 3: ZIP files
    for zipfile in glob.glob('*.zip'):
        if 'Saber' in zipfile or 'ICFES' in zipfile:
            try:
                print(f"Loading {zipfile}...")
                df = pd.read_csv(zipfile, compression='zip', low_memory=False)
                df.columns = df.columns.str.upper()

                if 'PERIODO' in df.columns:
                    df['YEAR'] = df['PERIODO'].apply(lambda x: int(str(int(x))[:4]) if pd.notna(x) else None)
                else:
                    import re
                    year_match = re.search(r'20\d{2}', zipfile)
                    if year_match:
                        df['YEAR'] = int(year_match.group())

                all_data.append(df)
                print(f"  ✓ Loaded {len(df):,} records")
            except Exception as e:
                print(f"  ✗ Error: {e}")

    if not all_data:
        print("⚠️  No data files found")
        return pd.DataFrame()

    # Combine all data
    df_combined = pd.concat(all_data, ignore_index=True)

    # Standardize column names
    column_mapping = {
        'PUNT_LECTURA_CRITICA': 'punt_lectura_critica',
        'PUNT_MATEMATICAS': 'punt_matematicas',
        'PUNT_C_NATURALES': 'punt_c_naturales',
        'PUNT_SOCIALES_CIUDADANAS': 'punt_sociales_ciudadanas',
        'PUNT_INGLES': 'punt_ingles',
        'PUNT_GLOBAL': 'punt_global',
        'COLE_COD_DANE_ESTABLECIMIENTO': 'cole_cod_dane_establecimiento',
        'COLE_NOMBRE_ESTABLECIMIENTO': 'cole_nombre_establecimiento',
        'COLE_DEPTO_UBICACION': 'cole_depto_ubicacion',
        'COLE_MCPIO_UBICACION': 'cole_mcpio_ubicacion',
        'COLE_NATURALEZA': 'cole_naturaleza',
        'COLE_AREA_UBICACION': 'cole_area_ubicacion',
        'COLE_GENERO': 'cole_genero',
        'COLE_CARACTER': 'cole_caracter',
        'FAMI_ESTRATOVIVIENDA': 'fami_estratovivienda',
        'FAMI_EDUCACIONMADRE': 'fami_educacionmadre',
        'FAMI_EDUCACIONPADRE': 'fami_educacionpadre',
        'FAMI_TIENEINTERNET': 'fami_tieneinternet',
        'FAMI_TIENECOMPUTADOR': 'fami_tienecomputador',
        'ESTU_GENERO': 'estu_genero',
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df_combined.columns:
            df_combined[new_col] = df_combined[old_col]

    # Filter by years if specified
    if years != 'all' and 'YEAR' in df_combined.columns:
        if years == 'latest':
            latest_year = df_combined['YEAR'].max()
            df_combined = df_combined[df_combined['YEAR'] == latest_year]
        elif isinstance(years, list):
            df_combined = df_combined[df_combined['YEAR'].isin(years)]

    # Sample if requested
    if sample_size and len(df_combined) > sample_size:
        df_combined = df_combined.sample(n=sample_size, random_state=42)
        print(f"Sampled to {sample_size:,} records")

    print(f"\n✅ Total loaded: {len(df_combined):,} student records")
    if 'YEAR' in df_combined.columns:
        years_available = sorted(df_combined['YEAR'].dropna().unique())
        print(f"📅 Years: {years_available}")

    return df_combined


def aggregate_schools_all_subjects(df_students):
    """
    Aggregate student data to school level for all subjects

    Returns:
        DataFrame with school-level averages for all subjects
    """
    score_cols = [
        'punt_lectura_critica',
        'punt_matematicas',
        'punt_c_naturales',
        'punt_sociales_ciudadanas',
        'punt_ingles',
        'punt_global'
    ]

    groupby_cols = [
        'cole_cod_dane_establecimiento',
        'cole_nombre_establecimiento',
        'cole_depto_ubicacion',
        'cole_mcpio_ubicacion',
        'cole_naturaleza',
        'cole_area_ubicacion',
        'cole_genero',
        'cole_caracter'
    ]

    # Filter to existing columns
    groupby_cols = [c for c in groupby_cols if c in df_students.columns]
    score_cols = [c for c in score_cols if c in df_students.columns]

    if not groupby_cols or not score_cols:
        return pd.DataFrame()

    # Aggregate
    agg_dict = {col: ['mean', 'count', 'std'] for col in score_cols}

    df_agg = df_students[groupby_cols + score_cols].groupby(groupby_cols).agg(agg_dict)
    df_agg.columns = ['_'.join(col).strip('_') for col in df_agg.columns.values]
    df_agg = df_agg.reset_index()

    return df_agg


def load_aggregated_school_data(force_regenerate=False):
    """
    Load or generate aggregated school data with all subjects

    Args:
        force_regenerate: If True, regenerate from student data

    Returns:
        DataFrame with school-level aggregated data
    """
    agg_file = 'Colegios_Saber11_AllSubjects.csv'

    if os.path.exists(agg_file) and not force_regenerate:
        print(f"Loading {agg_file}...")
        df = pd.read_csv(agg_file)
        print(f"✓ Loaded {len(df):,} schools")
        return df

    print("Generating aggregated school data from student records...")
    df_students = load_saber11_student_data(years='all', sample_size=None)

    if len(df_students) == 0:
        print("⚠️  No student data available")
        return pd.DataFrame()

    df_agg = aggregate_schools_all_subjects(df_students)

    # Save for future use
    df_agg.to_csv(agg_file, index=False)
    print(f"✅ Saved {agg_file} with {len(df_agg):,} schools")

    return df_agg


def get_available_subjects(df):
    """Get list of subjects available in dataframe"""
    subjects = []

    for key, name in SABER11_SUBJECTS.items():
        # Check for _mean columns
        if f'punt_{key}_mean' in df.columns:
            subjects.append({
                'key': key,
                'name': name,
                'col_mean': f'punt_{key}_mean',
                'col_count': f'punt_{key}_count',
                'col_std': f'punt_{key}_std'
            })
        # Or direct columns
        elif f'punt_{key}' in df.columns:
            subjects.append({
                'key': key,
                'name': name,
                'col': f'punt_{key}'
            })

    return subjects


def prepare_for_visualization(df, subject_key):
    """
    Prepare dataframe for visualization of a specific subject
    Returns clean dataframe with necessary columns
    """
    # Determine column names
    if f'punt_{subject_key}_mean' in df.columns:
        score_col = f'punt_{subject_key}_mean'
        count_col = f'punt_{subject_key}_count'
    elif f'punt_{subject_key}' in df.columns:
        score_col = f'punt_{subject_key}'
        count_col = None
    else:
        return pd.DataFrame()

    # Select columns
    cols = [score_col]
    if count_col and count_col in df.columns:
        cols.append(count_col)

    # Add metadata columns if available
    meta_cols = [
        'cole_cod_dane_establecimiento',
        'cole_nombre_establecimiento',
        'cole_depto_ubicacion',
        'cole_mcpio_ubicacion',
        'cole_naturaleza',
        'cole_area_ubicacion',
        'cole_genero',
        'cole_caracter'
    ]

    for col in meta_cols:
        if col in df.columns and col not in cols:
            cols.append(col)

    df_viz = df[cols].dropna(subset=[score_col]).copy()

    # Rename for easier use
    df_viz['score'] = df_viz[score_col]
    if count_col:
        df_viz['n_students'] = df_viz[count_col]

    return df_viz


if __name__ == '__main__':
    print("="*70)
    print("SABER DATA LOADER - Testing")
    print("="*70)

    # Test loading
    df = load_aggregated_school_data()

    if len(df) > 0:
        print(f"\n✅ Loaded {len(df):,} schools")

        # Show available subjects
        subjects = get_available_subjects(df)
        print(f"\n📚 Available subjects: {len(subjects)}")
        for subj in subjects:
            print(f"  - {subj['name']}")

        # Show sample
        print(f"\n📊 Sample data:")
        print(df.head(2))
    else:
        print("\n⚠️  No data loaded")
