import sys
import os
import pandas as pd
import kagglehub
import logging

# --- MANDATORY PATH FIX ---
# This ensures Python finds the 'src' folder for imports and the root for config
current_file_path = os.path.abspath(__file__)
src_path = os.path.dirname(os.path.dirname(current_file_path))

if src_path not in sys.path:
    sys.path.insert(0, src_path)

# --- MANDATORY UTILITY IMPORTS ---
try:
    from utils.read_utils import AppConfig
    from utils.db_utils import AirlineDBConnection
    from utils.decorators import log_execution_time
except ImportError as e:
    print(f"Import Error: Make sure src/utils/ contains __init__.py. Error: {e}")
    sys.exit(1)

# --- INITIALIZE CONFIG (SINGLETON) ---
try:
    config_instance = AppConfig()
    # Check if settings loaded correctly to avoid 'NoneType' error
    if not config_instance.settings:
        raise ValueError("Config settings are empty. Check your config.yaml path.")
        
    DB_PATH = config_instance.settings['database']['path']
    TABLE_NAME = config_instance.settings['database']['table_name']
except Exception as e:
    print(f"Configuration Loading Error: {e}")
    sys.exit(1)

@log_execution_time  # Mandatory Decorator
def run_etl():
    """
    Performs the full Extraction, Transformation, and Loading process.
    Uses a custom Context Manager for database operations.
    """
    print("--- STARTING ETL PROCESS ---")

    # 1. EXTRACTION
    print("Step 1: Downloading full dataset from Kaggle...")
    try:
        # Downloads the latest version of the Airline Dataset
        dataset_path = kagglehub.dataset_download("iamsouravbanerjee/airline-dataset")
        files = [f for f in os.listdir(dataset_path) if f.endswith('.csv')]
        full_csv_path = os.path.join(dataset_path, files[0])
        
        # Load all 15+ attributes (Select All)
        df = pd.read_csv(full_csv_path)
        print(f"Successfully extracted {len(df.columns)} columns.")
    except Exception as e:
        print(f"Extraction Failed: {e}")
        return

    # 2. TRANSFORMATION
    print("Step 2: Cleaning and transforming attributes...")
    # Standardize column names (lowercase, no spaces)
    df.columns = [c.strip().replace(' ', '_').replace('/', '_').lower() for c in df.columns]
    
    # Ensure date types are correct
    if 'departure_date' in df.columns:
        df['departure_date'] = pd.to_datetime(df['departure_date'], errors='coerce')
    
    # Add a derived column for Dashboard logic (On-Time Performance)
    if 'flight_status' in df.columns:
        df['is_delayed'] = df['flight_status'].apply(lambda x: 1 if str(x).lower() == 'delayed' else 0)

    # 3. LOADING (Using Custom Context Manager)
    print(f"Step 3: Loading data into {DB_PATH}...")
    try:
        # Use our mandatory class-based Context Manager
        with AirlineDBConnection(DB_PATH) as conn:
            # Load the dataframe into the SQLite table
            df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
            df.to_excel("data.xlsx", index=False)  # For verification
        print("--- ETL SUCCESSFUL: ALL DATA LOADED ---")
    except Exception as e:
        print(f"Database Load Failed: {e}")

if __name__ == "__main__":
    run_etl()