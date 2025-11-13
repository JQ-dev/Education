"""
Test script for app_enhanced.py data loading
"""
import sys
import pandas as pd

print("="*70)
print("TESTING APP_ENHANCED.PY DATA LOADING")
print("="*70)

try:
    # Test 1: Load Saber 11 data
    print("\n1. Testing load_saber11_2024_data()...")

    from app_enhanced import load_saber11_2024_data
    df_students = load_saber11_2024_data()

    print(f"   ✓ Loaded {len(df_students):,} student records")
    print(f"   ✓ Columns: {len(df_students.columns)}")

    # Check for score columns
    score_cols = [c for c in df_students.columns if 'PUNT' in c.upper()]
    print(f"   ✓ Score columns: {len(score_cols)}")
    for col in sorted(score_cols)[:6]:
        print(f"     - {col}")

    # Test 2: Aggregate by school
    print("\n2. Testing aggregate_by_school()...")
    from app_enhanced import aggregate_by_school
    df_schools = aggregate_by_school(df_students)

    print(f"   ✓ Aggregated to {len(df_schools):,} schools")
    print(f"   ✓ Columns: {len(df_schools.columns)}")

    # Show sample columns
    agg_cols = [c for c in df_schools.columns if '_mean' in c]
    print(f"   ✓ Aggregated score columns: {len(agg_cols)}")
    for col in sorted(agg_cols)[:6]:
        print(f"     - {col}")

    # Test 3: Aggregate by municipality
    print("\n3. Testing aggregate_by_municipality()...")
    from app_enhanced import aggregate_by_municipality
    df_municipalities = aggregate_by_municipality(df_students)

    print(f"   ✓ Aggregated to {len(df_municipalities):,} municipalities")

    # Test 4: Grade cols structure
    print("\n4. Testing grade_cols structure...")
    from app_enhanced import grade_cols

    print(f"   ✓ Grades: {list(grade_cols.keys())}")
    if '11' in grade_cols:
        print(f"   ✓ Subjects for Grade 11: {len(grade_cols['11'])}")
        for subj, col in list(grade_cols['11'].items())[:8]:
            print(f"     - {subj}: {col}")

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
