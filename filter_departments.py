import pandas as pd
import glob

def filter_parquets_by_period():
    """
    Read all Examen_Saber_11_*.parquet files, filter for Santander and Norte de Santander departments,
    and save separate filtered Parquet files for each period.
    """
    # Find all Parquet files
    parquet_files = glob.glob('Examen_Saber_11_*.parquet')

    for file in parquet_files:
        try:
            # Read Parquet file
            df = pd.read_parquet(file)
            # Filter for the specified departments (case-insensitive match)
            filtered_df = df[df['cole_depto_ubicacion'].str.upper().isin(['SANTANDER', 'NORTE DE SANTANDER'])]
            if not filtered_df.empty:
                # Extract period from filename (e.g., 20191 from Examen_Saber_11_20191.parquet)
                period = file.split('_')[-1].replace('.parquet', '')
                # Save to new Parquet file
                output_file = f'filtered_santander_norte_santander_{period}.parquet'
                filtered_df.to_parquet(output_file, index=False)
                print(f"Filtered {len(filtered_df)} rows from {file} and saved to {output_file}")
            else:
                print(f"No data found for specified departments in {file}")
        except Exception as e:
            print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    filter_parquets_by_period()