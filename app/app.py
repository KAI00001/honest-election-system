from flask import Flask, render_template, request, redirect, url_for, flash
from .db_connection import create_connection
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import InternalServerError

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Handle Internal Server Errors
@app.errorhandler(InternalServerError)
def internal_error(error):
    return f"An internal error occurred: {error}", 500

@app.route('/')
def home():
    return render_template('index.html')

# Example of a route to register a voter
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        try:
            lrn = request.form['lrn']
            full_name = request.form['full_name']
            email = request.form['email']
            password = request.form['password']

            # Basic validation to ensure the fields are not empty
            if not lrn or not full_name or not email or not password:
                flash("Please fill in all fields.", "danger")
                return redirect(url_for('register'))

            # Hash the password before storing it in the database
            hashed_password = generate_password_hash(password)

            # Create a database connection
            connection = create_connection()
            cursor = connection.cursor()

            # Check if the LRN is valid
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))
            valid_lrn = cursor.fetchone()

            if valid_lrn:
                # Check if the LRN already exists in the voters table
                cursor.execute("SELECT * FROM voters WHERE lrn = %s", (lrn,))
                existing_voter = cursor.fetchone()

                if existing_voter:
                    flash("This LRN is already registered.", "danger")
                else:
                    # Insert the new voter with the hashed password
                    cursor.execute("INSERT INTO voters (lrn, full_name, email, password) VALUES (%s, %s, %s, %s)",
                                   (lrn, full_name, email, hashed_password))
                    connection.commit()
                    flash("Registration successful!", "success")
                    return redirect(url_for('home'))
            else:
                flash("Invalid LRN. Please try again.", "danger")

        except Exception as e:
            # Flash any exception message that occurs
            flash(f"An error occurred: {e}", "danger")
        finally:
            # Ensure the connection is closed
            if connection:
                connection.close()

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
