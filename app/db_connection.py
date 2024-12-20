import mysql.connector
from mysql.connector import Error

def create_connection():
    """Create and return a MySQL connection."""
    connection = None  # Initialize connection variable
    try:
        print("Attempting to connect to the database...")

        connection = mysql.connector.connect(
            host="localhost",                # MySQL server host
            user="kerbyyy",                  # MySQL username
            password="yoou",                 # MySQL password
            database="honest_election_system",  # Database name
            charset="utf8mb4"                # Ensuring utf8mb4 charset is used
        )
        
        # After connecting, set the character set explicitly
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SET NAMES 'utf8mb4';")
            cursor.close()
            print("Connected to MySQL database with utf8mb4 charset")
            return connection
        else:
            print("Failed to connect to database")
            return None
    
    except Error as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Test the connection
    conn = create_connection()
    if conn:
        print("Connection successful")
        conn.close()
    else:
        print("Connection failed")
