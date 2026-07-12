import sys
import io
import pandas as pd
import os

# Configure stdout to use UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

csv_files = ["kaggle_housing_data.csv", "dn.csv", "hcm.csv", "hn.csv", "nhatot_data.csv"]

for filename in csv_files:
    if os.path.exists(filename):
        print(f"\n===== Checking {filename} =====")
        try:
            df = pd.read_csv(filename, nrows=5, encoding='utf-8')
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print(df.head())
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'utf-16']:
                try:
                    df = pd.read_csv(filename, nrows=5, encoding=encoding)
                    print(f"Successfully read with encoding {encoding}")
                    print(f"Shape: {df.shape}")
                    print(f"Columns: {list(df.columns)}")
                    print(df.head())
                    break
                except:
                    continue
    else:
        print(f"\n{filename} not found!")
