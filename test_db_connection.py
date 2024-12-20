import sys
import os

# Ensure that the app folder is added to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.db_connection import create_connection  # Now this import should work

def test_connection():
    conn = create_connection()
    if conn and conn.is_connected():
        print("Database connection successful!")
        conn.close()
    else:
        print("Failed to connect to the database.")

# Run the test
test_connection()
