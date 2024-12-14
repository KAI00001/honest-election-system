from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

# Initialize the Flask application
app = Flask(__name__)

# Database connection function
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",            # Replace with your database host (e.g., localhost)
            user="root",                 # Replace with your database username
            password="",                 # Replace with your database password
            database="honest_election"   # Replace with your actual database
        )
        if connection.is_connected():
            print("Successfully connected to the database.")
        return connection
    except Error as err:
        print(f"Error: {err}")
        return None

@app.route("/")
def home():
    return render_template("home.html")  # Home page template

@app.route("/add-voter", methods=["POST", "GET"])
def add_voter():
    if request.method == "POST":
        db = connect_to_db()
        if db is None:
            flash("Failed to connect to the database.", "danger")
            return redirect(url_for("home"))

        cursor = db.cursor()

        # Get data from the form
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        course = request.form.get("course")
        year = request.form.get("year")

        # Validate input fields
        if not firstname or not lastname or not course or not year:
            flash("All fields are required!", "danger")
            return render_template("add_voter.html")

        # Insert data into the database
        try:
            sql = "INSERT INTO voters (FIRSTNAME, LASTNAME, COURSE, YEARLEVEL) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (firstname, lastname, course, year))
            db.commit()
            flash("Voter added successfully!", "success")
        except Error as err:
            flash(f"Error: {err}", "danger")
        finally:
            db.close()

        return redirect(url_for("home"))  # Redirect to home page after successful form submission

    return render_template("add_voter.html")  # Render the form if it's a GET request

if __name__ == "__main__":
    app.run(debug=True)
