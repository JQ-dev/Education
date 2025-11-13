import pandas as pd
import os
import glob

def convert_txt_to_parquet(txt_file_path, parquet_file_path):
    """
    Convert a semicolon-delimited .txt file to Parquet format.
    """
    try:
        # Read the .txt file with semicolon delimiter
        df = pd.read_csv(txt_file_path, sep=';', encoding='utf-8', low_memory=False)
        # Convert to Parquet
        df.to_parquet(parquet_file_path, index=False)
        print(f"Successfully converted {txt_file_path} to {parquet_file_path}")
    except Exception as e:
        print(f"Error converting {txt_file_path}: {e}")

def main():
    # Find all Examen_Saber_11_*.txt files
    txt_files = glob.glob('Examen_Saber_11_*.txt')

    for txt_file in txt_files:
        # Create corresponding parquet file name
        parquet_file = txt_file.replace('.txt', '.parquet')
        convert_txt_to_parquet(txt_file, parquet_file)

if __name__ == "__main__":
    main()