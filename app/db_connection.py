import traceback  # Module to print detailed error information
import mysql.connector  # MySQL connector module
from mysql.connector import Error  # Importing Error class for exception handling

def create_connection():
    """Create and return a MySQL connection."""
    connection = None  # Initialize connection variable as None
    try:
        print("Before attempting to connect to the database...")
        
        print("Attempting to connect to the database...")
        
        # Attempt to create a connection to MySQL database
        connection = mysql.connector.connect(
            host="127.0.0.1",  # MySQL server address (localhost)
            user="kerbyyy",  # MySQL username
            password="yoou",  # MySQL password
            database="honest_election_system",  # Database name
            charset="utf8mb4",  # Set character encoding to utf8mb4
            connection_timeout=10  # Timeout in seconds for connection attempt
        )
        
        print("Connection attempt complete.")
        
        # After connecting, set the character set explicitly
        if connection.is_connected():  # Check if connection was successful
            print("Connection established and checking charset...")
            cursor = connection.cursor()  # Create a cursor object to execute queries
            cursor.execute("SET NAMES 'utf8mb4';")  # Set character encoding
            cursor.close()  # Close cursor after execution
            print("Connected to MySQL database with utf8mb4 charset")
            return connection  # Return the successful connection object
        else:
            print("Failed to connect to the database (connection.is_connected() returned False).")
            return None  # Return None if connection failed
    
    except Error as e:
        print(f"Error: {e}")  # Print MySQL-related error message
        return None  # Return None on error

    except Exception as e:
        # Catch any general exceptions that might not be MySQL related
        print(f"General Exception: {e}")
        traceback.print_exc()  # Print traceback of the error for debugging
        return None  # Return None on exception

if __name__ == "__main__":  # Ensures this script runs only when executed directly
    print("Before calling create_connection()...")
    
    conn = create_connection()  # Call the function to establish database connection
    
    print("After calling create_connection()...")
    
    if conn:
        print("Connection successful")
        conn.close()  # Close the connection to free up resources
    else:
        print("Connection failed")
