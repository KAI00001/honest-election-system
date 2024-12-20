from app.db_connection import get_db_connection

def test_connection():
    conn = get_db_connection()
    if conn.is_connected():
        print("Database connection successful!")
        conn.close()

test_connection()
