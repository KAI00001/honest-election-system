import mysql.connector
from mysql.connector import Error

# Function to create a connection to the MySQL database
def create_connection():
    try:
        # Establish the connection to the MySQL database
        connection = mysql.connector.connect(
            host='localhost',  # Change this if your DB is on another server
            user='your_username',  # Replace with your MySQL username
            password='your_password',  # Replace with your MySQL password
            database='honest_election_system'  # Use the database you created
        )

        # Check if the connection was successful
        if connection.is_connected():
            print("Connected to the database")
            return connection
        else:
            print("Failed to connect to the database")
            return None

    except Error as e:
        print(f"Error: {e}")
        return None
