import sys
import os

# Ensure that the 'app' folder is added to the system path
# This is needed to import modules from the 'app' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Import the create_connection function from db_connection.py inside the 'app' folder
from app.db_connection import create_connection  

def test_connection():
    # Create a connection to the database
    conn = create_connection()
    
    # Check if the connection is successful
    if conn and conn.is_connected():
        print("Database connection successful!")  # Print success message
        conn.close()  # Close the connection after testing
    else:
        print("Failed to connect to the database.")  # Print failure message

# Run the test function
test_connection()

