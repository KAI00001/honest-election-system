from flask import Flask, request, redirect, flash, render_template, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import InternalServerError
from .db_connection import create_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Handle Internal Server Errors
@app.errorhandler(InternalServerError)
def internal_error(error):
    return f"An internal error occurred: {error}", 500

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# Registration Route
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        try:
            # Extract form data
            lrn = request.form['lrn']
            full_name = request.form['full_name']
            email = request.form['email']
            password = request.form['password']

            # Basic validation
            if not lrn or not full_name or not email or not password:
                flash("Please fill in all fields.", "danger")
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)

            connection = create_connection()
            if connection is None:
                flash("Database connection error. Please try again later.", "danger")
                return redirect(url_for('register'))

            cursor = connection.cursor(dictionary=True)

            # Check LRN validity
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))
            valid_lrn = cursor.fetchone()

            if valid_lrn:
                cursor.execute("SELECT * FROM voters WHERE lrn = %s", (lrn,))
                existing_voter = cursor.fetchone()

                if existing_voter:
                    flash("This LRN is already registered.", "danger")
                else:
                    cursor.execute(
                        "INSERT INTO voters (lrn, full_name, email, password) VALUES (%s, %s, %s, %s)",
                        (lrn, full_name, email, hashed_password)
                    )
                    connection.commit()
                    flash("Registration successful!", "success")
                    return redirect(url_for('home'))
            else:
                flash("Invalid LRN. Please try again.", "danger")

        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            if connection:
                connection.close()

    return render_template('register.html')

# Admin Login Route
@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if request.method == 'POST':
        password = request.form['password']

        connection = create_connection()
        if connection is None:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('admin'))

        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
            admin_data = cursor.fetchone()

            if admin_data and check_password_hash(admin_data['password'], password):
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid password. Access Denied.", "danger")
                return redirect(url_for('admin'))  # Redirect back to the login page
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('admin'))  # If an error occurs, stay on the login page
        finally:
            cursor.close()
            connection.close()

    return render_template('admin.html')

# Admin Dashboard
@app.route('/admin-dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    connection = create_connection()
    if connection is None:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for('home'))

    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch valid LRNs for adding new valid LRN
        cursor.execute("SELECT * FROM valid_lrns")
        valid_lrns = cursor.fetchall()

        # Fetch all registered voters based on valid LRNs
        cursor.execute("SELECT * FROM voters")
        voters = cursor.fetchall()

        # Fetch all party list requests
        cursor.execute("SELECT * FROM party_list_requests WHERE request_status = 'pending'")
        party_list_requests = cursor.fetchall()

        if request.method == 'POST':
            new_lrn = request.form['new_lrn']
            if new_lrn:
                cursor.execute("INSERT INTO valid_lrns (lrn) VALUES (%s)", (new_lrn,))
                connection.commit()
                flash("New LRN added successfully!", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Please enter a valid LRN.", "danger")

        return render_template(
            'admin_dashboard.html',
            valid_lrns=valid_lrns,
            voters=voters,
            party_list_requests=party_list_requests
        )
    except Exception as e:
        flash(f"Error occurred: {e}", "danger")
        return redirect(url_for('home'))
    finally:
        cursor.close()
        connection.close()

# Create Party List Route
@app.route('/create-party-list', methods=['GET', 'POST'])
def create_party_list():
    connection = create_connection()
    if connection is None:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for('home'))

    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch all voters to fill positions
        cursor.execute("SELECT * FROM voters")
        voters = cursor.fetchall()

        if request.method == 'POST':
            party_name = request.form['party_name']
            president = request.form['president']
            vice_president = request.form['vice_president']
            secretary = request.form['secretary']
            treasurer = request.form['treasurer']
            pro = request.form['pro']

            # Basic validation
            if not party_name or not president or not vice_president or not secretary or not treasurer or not pro:
                flash("Please fill in all fields.", "danger")
                return render_template('create_party_list.html', voters=voters)  # Stay on the same page if validation fails

            # Insert the party list into the database
            cursor.execute(
                "INSERT INTO party_lists (party_name, president, vice_president, secretary, treasurer, pro) VALUES (%s, %s, %s, %s, %s, %s)",
                (party_name, president, vice_president, secretary, treasurer, pro)
            )
            connection.commit()

            flash("Party list created successfully!", "success")
            return render_template('create_party_list.html', voters=voters)  # Stay on the same page after successful submission

        return render_template('create_party_list.html', voters=voters)
    except Exception as e:
        flash(f"Error occurred: {e}", "danger")
        return redirect(url_for('home'))
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)
