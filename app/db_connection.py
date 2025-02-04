import traceback
import mysql.connector
from mysql.connector import Error

def create_connection():
    """Create and return a MySQL connection."""
    connection = None  # Initialize connection variable
    try:
        print("Before attempting to connect to the database...")
        
        print("Attempting to connect to the database...")
        
        # Attempt to create a connection
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="kerbyyy",
            password="yoou",
            database="honest_election_system",
            charset="utf8mb4",
            connection_timeout=10  
        )
        
        print("Connection attempt complete.")
        
        # After connecting, set the character set explicitly
        if connection.is_connected():
            print("Connection established and checking charset...")
            cursor = connection.cursor()
            cursor.execute("SET NAMES 'utf8mb4';")
            cursor.close()
            print("Connected to MySQL database with utf8mb4 charset")
            return connection
        else:
            print("Failed to connect to the database (connection.is_connected() returned False).")
            return None
    
    except Error as e:
        print(f"Error: {e}")
        return None

    except Exception as e:
        # Catch any general exceptions that might not be MySQL related
        print(f"General Exception: {e}")
        traceback.print_exc()  # Print traceback of the error for debugging
        return None

if __name__ == "__main__":
    print("Before calling create_connection()...")
    
    conn = create_connection()
    
    print("After calling create_connection()...")
    
    if conn:
        print("Connection successful")
        conn.close()
    else:
        print("Connection failed")
