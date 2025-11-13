import pandas as pd

# Read the first few lines of the file to understand its structure
file_path = 'Examen_Saber_11_20191.txt'

try:
    # Try to read as CSV with tab delimiter, common for .txt files
    df = pd.read_csv(file_path, sep='\t', nrows=5)
    print("File structure (first 5 rows):")
    print(df.head())
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
except Exception as e:
    print(f"Error reading as tab-delimited CSV: {e}")
    try:
        # Try with comma delimiter
        df = pd.read_csv(file_path, sep=',', nrows=5)
        print("File structure (first 5 rows) with comma delimiter:")
        print(df.head())
    except Exception as e2:
        print(f"Error reading as comma-delimited CSV: {e2}")
        # If both fail, read as plain text
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [next(f) for _ in range(5)]
        print("First 5 lines of the file:")
        for i, line in enumerate(lines, 1):
            print(f"Line {i}: {line.strip()}")