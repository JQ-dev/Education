import os
import glob

def rename_files():
    # Find all files starting with Examen_Saber_11_SS_
    files = glob.glob('Examen_Saber_11_SS_*.parquet')

    for file in files:
        # Extract the year and period from the filename
        # Look for the 5-digit pattern at the end before .parquet
        base = file.replace('.parquet', '')
        parts = base.split('_')
        # Find the last part that is 5 digits
        for i in range(len(parts)-1, -1, -1):
            if len(parts[i]) == 5 and parts[i].isdigit():
                new_name = f'Examen_Saber_11_SS_{parts[i]}.parquet'
                if new_name != file:
                    os.rename(file, new_name)
                    print(f'Renamed {file} to {new_name}')
                break

if __name__ == "__main__":
    rename_files()