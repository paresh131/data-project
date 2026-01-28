import os

# This calculates the path to the main folder (WP_HubaBubba_Projekt_Gruppe7)
# It goes up 3 levels from this file: backend.py -> backend folder -> src folder -> root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# THESE NAMES MUST BE EXACT
DB_PATH = os.path.join(BASE_DIR, "airline_operations.db")
TABLE_NAME = "flight_data"

print(f"Backend initialized. DB Path: {DB_PATH}")