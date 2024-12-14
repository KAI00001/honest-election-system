from app.db_connection import connect_to_db

# Test the database connection
db = connect_to_db()
if db:
    cursor = db.cursor()
    cursor.execute("SHOW DATABASES;")
    print("Available databases:")
    for db_name in cursor.fetchall():
        print(db_name)
    db.close()
else:
    print("Failed to connect to the database.")
