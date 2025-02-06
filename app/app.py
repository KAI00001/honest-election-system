from flask import Flask, jsonify, request, redirect, flash, render_template, session, url_for  # Import necessary modules from Flask
from werkzeug.security import generate_password_hash, check_password_hash  # Import functions for password hashing and verification
from werkzeug.exceptions import InternalServerError  # Import an exception handler for internal server errors
from .db_connection import create_connection  # Import the database connection function from db_connection.py
from flask_cors import CORS  # Import CORS to allow cross-origin requests

app = Flask(__name__)  # Initialize the Flask application
app.secret_key = 'your_secret_key'  # Set a secret key for session management (replace with a secure key)

# Handle Internal Server Errors
@app.errorhandler(InternalServerError)  # Catch internal server errors
def internal_error(error):
    return f"An internal error occurred: {error}", 500  # Return an error message with status code 500

# Home Route (Render signup.html as the homepage)
@app.route('/')  # Define a route for the homepage
def home():
    return render_template('signup.html')  # Render the signup.html template

# Login with LRN Route
@app.route('/login-lrn', methods=['POST', 'GET'])  # Define a route for logging in with LRN (Learner Reference Number)
def login_lrn():
    if request.method == 'POST':  # Check if the request method is POST
        lrn = request.form['lrn']  # Get the LRN input from the form

        if not lrn:  # Check if LRN is empty
            flash("Please enter your LRN.", "danger")  # Show an error message
            return redirect(url_for('login_lrn'))  # Redirect back to the login page

        connection = create_connection()  # Establish a database connection
        if connection is None:  # If connection fails
            flash("Database connection error. Please try again later.", "danger")  # Show an error message
            return redirect(url_for('login_lrn'))  # Redirect back to the login page

        try:
            cursor = connection.cursor(dictionary=True)  # Create a database cursor with dictionary format
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))  # Query the database for the entered LRN
            valid_lrn = cursor.fetchone()  # Fetch the result

            if valid_lrn:  # If LRN exists in the database
                flash("Login successful!", "success")  # Show a success message
                return redirect(url_for('index'))  # Redirect to the homepage or dashboard
            else:
                flash("Invalid LRN. Please try again.", "danger")  # Show an error message for invalid LRN
                return render_template('signup.html')  # Reload the signup page
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")  # Show an error message if an exception occurs
        finally:
            connection.close()  # Close the database connection

    return render_template('loginlrn.html')  # Render the login page if the request method is GET

# Admin Login Route
@app.route('/admin', methods=['POST', 'GET'])  # Define a route for the admin login page
def admin():
    if request.method == 'POST':  # Check if the request method is POST (form submission)
        password = request.form['password']  # Get the password input from the form

        connection = create_connection()  # Establish a database connection
        if connection is None:  # If connection fails
            flash("Database connection error. Please try again later.", "danger")  # Show an error message
            return redirect(url_for('admin'))  # Redirect back to the admin login page

        try:
            cursor = connection.cursor(dictionary=True)  # Create a database cursor with dictionary format
            cursor.execute("SELECT * FROM admins WHERE username = 'admin'")  # Query the database for the admin account
            admin_data = cursor.fetchone()  # Fetch the result

            if admin_data and check_password_hash(admin_data['password'], password):  # Check if the password is correct
                return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard if login is successful
            else:
                flash("Invalid password. Access Denied.", "danger")  # Show an error message for incorrect password
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")  # Show an error message if an exception occurs
        finally:
            connection.close()  # Close the database connection

    return render_template('admin.html')  # Render the admin login page if the request method is GET

# Admin Dashboard Route
@app.route('/admin-dashboard', methods=['GET', 'POST'])  # Define a route for the admin dashboard
def admin_dashboard():
    connection = create_connection()  # Establish a database connection
    if connection is None:  # If the connection fails
        flash("Database connection error. Please try again later.", "danger")  # Show an error message
        return redirect(url_for('home'))  # Redirect to the homepage

    try:
        cursor = connection.cursor(dictionary=True)  # Create a cursor for executing SQL queries

        # Fetch valid LRN list and voters data
        cursor.execute("SELECT * FROM valid_lrns")  # Get all valid LRNs from the database
        valid_lrns = cursor.fetchall()  # Store the fetched LRNs in a variable
        cursor.execute("SELECT * FROM voters")  # Get all voters
        voters = cursor.fetchall()  # Store the fetched voters data

        # Fetch pending party list applications and solo applications
        cursor.execute("SELECT * FROM party_lists WHERE status = 'pending'")  # Get pending party list requests
        party_list_requests = cursor.fetchall()  # Store them in a variable
        cursor.execute("SELECT * FROM solo_applications WHERE status = 'pending'")  # Get pending solo applications
        solo_applications = cursor.fetchall()  # Store them in a variable

        if request.method == 'POST':  # Check if the request method is POST (form submission)
            new_lrn = request.form.get('new_lrn')  # Get the new LRN from the form input
            if new_lrn:  # If an LRN is provided
                cursor.execute("INSERT INTO valid_lrns (lrn) VALUES (%s)", (new_lrn,))  # Insert into the database
                connection.commit()  # Save changes
                flash("New LRN added successfully!", "success")  # Show a success message
                return redirect(url_for('admin_dashboard'))  # Reload the admin dashboard

            # Handle approval or decline of party list requests
            if 'approve_party_list' in request.form:  # If the approve button is clicked
                party_list_id = request.form.get('party_list_id')  # Get the party list ID
                if party_list_id:
                    cursor.execute("UPDATE party_lists SET status = 'approved' WHERE id = %s", (party_list_id,))  # Approve the request
                    connection.commit()
                    flash("Party list request approved.", "success")  # Show success message
                return redirect(url_for('admin_dashboard'))  # Reload the dashboard

            elif 'decline_party_list' in request.form:  # If the decline button is clicked
                party_list_id = request.form.get('party_list_id')  # Get the party list ID
                if party_list_id:
                    cursor.execute("UPDATE party_lists SET status = 'rejected' WHERE id = %s", (party_list_id,))  # Reject the request
                    connection.commit()
                    flash("Party list request declined.", "danger")  # Show error message
                return redirect(url_for('admin_dashboard'))  # Reload the dashboard

            # Handle approval or decline of solo applications
            if 'approve_solo_application' in request.form:  # If the approve button is clicked
                application_id = request.form.get('application_id')  # Get the solo application ID
                if application_id:
                    cursor.execute("UPDATE solo_applications SET status = 'approved' WHERE id = %s", (application_id,))  # Approve the request
                    connection.commit()
                    flash("Solo application approved.", "success")  # Show success message
                return redirect(url_for('admin_dashboard'))  # Reload the dashboard

            elif 'decline_solo_application' in request.form:  # If the decline button is clicked
                application_id = request.form.get('application_id')  # Get the solo application ID
                if application_id:
                    cursor.execute("UPDATE solo_applications SET status = 'rejected' WHERE id = %s", (application_id,))  # Reject the request
                    connection.commit()
                    flash("Solo application rejected.", "danger")  # Show error message
                return redirect(url_for('admin_dashboard'))  # Reload the dashboard

        # Render the admin dashboard template with fetched data
        return render_template('admin_dashboard.html', 
                               valid_lrns=valid_lrns,  # Pass valid LRN list to the template
                               voters=voters,  # Pass voters data to the template
                               party_list_requests=party_list_requests,  # Pass party list requests
                               solo_applications=solo_applications)  # Pass solo applications

    except Exception as e:  # Handle errors
        flash(f"Error occurred: {e}", "danger")  # Show an error message
    finally:
        connection.close()  # Close the database connection

    return redirect(url_for('home'))  # Redirect to the homepage if an error occurs

@app.route('/application', methods=['GET', 'POST'])  # Route for the application page, handles both GET and POST methods
def application():
    if request.method == 'POST':  # If the form is submitted (POST request)
        try:
            print("Raw Form Data:", request.form)  # Print raw form data for debugging

            # Get form fields
            position = request.form.get('position')  # Get the position for solo applications
            is_party = request.form.get('is_party') is not None  # Check if the user selected 'party' (boolean from checkbox)
            party_name = request.form.get('party_name') if is_party else None  # Get party name if 'is_party' is selected
            lrn = request.form.get('lrn')  # Get the LRN (Learner's Reference Number) from the form

            print(f"Position: {position}, Is Party: {is_party}, Party Name: {party_name}, LRN: {lrn}")  # Print the form data for debugging

            # Check if all required fields are filled
            if not lrn or (not is_party and not position) or (is_party and not party_name):
                flash("Please fill in all required fields.", "danger")  # Flash a message if any field is missing
                return redirect(url_for('application'))  # Redirect back to the application page

            connection = create_connection()  # Create a database connection
            if connection is None:
                flash("Database connection error. Please try again later.", "danger")  # Flash error if connection fails
                return redirect(url_for('application'))

            cursor = connection.cursor(dictionary=True)  # Create a cursor for database operations

            # Validate the LRN (check if it's valid)
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))
            valid_lrn = cursor.fetchone()
            if not valid_lrn:
                flash("Invalid LRN. Please check your LRN and try again.", "danger")  # Flash error if LRN is invalid
                return redirect(url_for('application'))

            if is_party:  # If the user is applying as a party
                required_positions = {  # Dictionary of required positions for the party list
                    'President': request.form.get('president'),
                    'Vice President': request.form.get('vice_president'),
                    'Secretary': request.form.get('secretary'),
                    'Treasurer': request.form.get('treasurer'),
                    'Auditor': request.form.get('auditor'),
                    'P.O': request.form.get('po'),
                    'P.I.O': request.form.get('pio'),
                    'G-7 Rep': request.form.get('g7_rep'),
                    'G-8 Rep': request.form.get('g8_rep'),
                    'G-9 Rep': request.form.get('g9_rep'),
                    'G-10 Rep': request.form.get('g10_rep'),
                    'G-11 Rep': request.form.get('g11_rep'),
                    'G-12 Rep': request.form.get('g12_rep')
                }

                # Check if all positions are filled
                if None in required_positions.values():
                    flash("Please fill all positions for the party list.", "danger")  # Flash error if any position is missing
                    return redirect(url_for('application'))

                # Validate LRNs for party positions
                for position_name, position_lrn in required_positions.items():
                    cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (position_lrn,))
                    if not cursor.fetchone():  # If any LRN is invalid, flash an error
                        flash(f"Invalid LRN for position {position_name}. Please check the LRNs.", "danger")
                        return redirect(url_for('application'))

                # Check if party name is unique
                cursor.execute("SELECT id FROM party_lists WHERE party_name = %s", (party_name,))
                if cursor.fetchone():  # If party name already exists, flash an error
                    flash("Party name already exists. Choose another name.", "danger")
                    return redirect(url_for('application'))

                print(f"Inserting into party_lists: {party_name}, {required_positions}")

                # Insert party details into the database
                cursor.execute("""
                    INSERT INTO party_lists 
                    (party_name, president_lrn, vice_president_lrn, secretary_lrn, treasurer_lrn, 
                    auditor_lrn, po_lrn, pio_lrn, g7_rep_lrn, g8_rep_lrn, g9_rep_lrn, g10_rep_lrn, g11_rep_lrn, g12_rep_lrn, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                """, (party_name, *required_positions.values()))
                connection.commit()

                party_list_id = cursor.lastrowid  # Get the ID of the newly inserted party list
                print(f"Party list inserted successfully with ID: {party_list_id}")

                # Insert members into the party_members table
                for position_name, position_lrn in required_positions.items():
                    cursor.execute("""
                        INSERT INTO party_members (party_list_id, lrn, position)
                        VALUES (%s, %s, %s)
                    """, (party_list_id, position_lrn, position_name))
                connection.commit()

                print("Party members inserted successfully!")

            else:  # If the user is applying solo
                # Prevent duplicate solo applications
                cursor.execute("SELECT id FROM solo_applications WHERE lrn = %s", (lrn,))
                if cursor.fetchone():  # If the user has already applied, flash an error
                    flash("You have already applied for a position.", "danger")
                    return redirect(url_for('application'))

                # Insert solo application into the database
                cursor.execute("INSERT INTO solo_applications (position, lrn) VALUES (%s, %s)", (position, lrn))
                connection.commit()
                print("Solo application inserted successfully!")

            flash("Application submitted successfully.", "success")  # Flash success message
            return redirect(url_for('application'))  # Redirect to the application page

        except Exception as e:  # If any error occurs, handle it
            print(f"Error occurred: {str(e)}")  # Print the error for debugging
            flash(f"An error occurred: {str(e)}", "danger")  # Flash error message
            return redirect(url_for('application'))  # Redirect back to the application page

    return render_template('application.html')  # Render the application page when the request is GET

# Edit Page Route
@app.route('/edit-page', methods=['GET', 'POST'])  # Route for handling GET and POST requests for the edit page
def edit_page():
    if request.method == 'POST':  # Check if the form was submitted via POST
        lrn = request.form.get('lrn')  # Get the LRN from the form
        new_password = request.form.get('password')  # Get the new password from the form
        full_name = request.form.get('full_name')  # Get the full name from the form
        email = request.form.get('email')  # Get the email from the form

        # Check if LRN, password, full_name, and email are not empty
        if not lrn or not new_password or not full_name or not email:
            flash("All fields (LRN, password, full name, and email) are required.", "danger")  # Flash error message if any field is empty
            return redirect(url_for('edit_page'))  # Redirect back to the edit page if validation fails

        connection = create_connection()  # Create a connection to the database
        if connection is None:  # If connection fails
            flash("Database connection error. Please try again later.", "danger")  # Flash database error message
            return redirect(url_for('edit_page'))  # Redirect back to the edit page

        try:
            cursor = connection.cursor(dictionary=True)  # Create a cursor to interact with the database

            # Check if the LRN exists in the valid_lrns table
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))  # Execute query to check LRN in valid_lrns table
            valid_lrn = cursor.fetchone()  # Fetch result

            if not valid_lrn:  # If LRN is invalid
                flash("Invalid LRN. Only valid LRNs can set a password.", "danger")  # Flash error message
                return redirect(url_for('edit_page'))  # Redirect back to the edit page

            # Check if the voter already exists in the voters table
            cursor.execute("SELECT * FROM voters WHERE lrn = %s", (lrn,))  # Execute query to check if voter exists
            voter = cursor.fetchone()  # Fetch result

            if voter:  # If the voter exists
                # Check if the password is already set (i.e., don't update if it already exists)
                if voter['password']:  # If password is already set
                    flash("Password has already been set and cannot be changed.", "danger")  # Flash error message
                else:
                    # Update the password, full name, and email
                    cursor.execute("""
                        UPDATE voters
                        SET password = %s, full_name = %s, email = %s
                        WHERE lrn = %s
                    """, (new_password, full_name, email, lrn))  # Execute update query
                    flash("Password, full name, and email updated successfully!", "success")  # Success message
            else:
                # Insert new voter data into the database
                cursor.execute("""
                    INSERT INTO voters (lrn, full_name, email, password)
                    VALUES (%s, %s, %s, %s)
                """, (lrn, full_name, email, new_password))  # Execute insert query
                flash("Password, full name, and email set successfully!", "success")  # Success message

            connection.commit()  # Commit the changes to the database

        except Exception as e:  # Catch any exceptions
            flash(f"An error occurred: {e}", "danger")  # Flash error message
        finally:
            connection.close()  # Close the database connection

        return redirect(url_for('edit_page'))  # Redirect back to the edit page

    return render_template('edit.html')  # Render the edit page template

# Home route to render index.html at /home
@app.route('/home')  # Define the route for '/home'
def index():
    return render_template('index.html')  # Render the index.html template when accessing '/home'

# Voters Route to fetch and display all voters
import traceback  # Import traceback to handle and display errors in case of an exception

# Voters Route to handle login and redirect to vote page
@app.route('/voters', methods=['GET', 'POST'])
def voters():
    connection = create_connection()  # Create a connection to the database
    if connection is None:
        flash("Database connection error. Please try again later.", "danger")  # Flash message if connection fails
        return redirect(url_for('home'))  # Redirect to home if database connection fails

    try:
        cursor = connection.cursor(dictionary=True)  # Initialize cursor to interact with the database

        if request.method == 'POST':  # Handle POST request when the form is submitted
            lrn = request.form.get('username')  # Get the LRN (username) from the form
            password = request.form.get('password')  # Get the password from the form

            if not lrn or not password:  # Check if both LRN and password are provided
                flash("LRN and Password are required!", "danger")  # Show error message if missing
                return redirect(url_for('voters'))  # Redirect back to voters page if fields are empty

            cursor.execute("SELECT * FROM voters WHERE lrn = %s", (lrn,))  # Query database for the voter with the given LRN
            voter = cursor.fetchone()  # Fetch the result of the query

            if voter:
                if voter['password'] == password:  # Check if the entered password matches the stored password
                    session['lrn'] = voter['lrn']  # Store the LRN in the session
                    session['full_name'] = voter['full_name']  # Store the full name in the session
                    flash(f"Welcome, {voter['full_name']}!", "success")  # Show success message on successful login
                    return redirect(url_for('vote_page'))  # Redirect to vote_page after successful login
                else:
                    flash("Incorrect password!", "danger")  # Show error if the password is incorrect
            else:
                flash("LRN not found!", "danger")  # Show error if the LRN is not found in the database

            return redirect(url_for('voters'))  # Return to voters page if login fails

        # Render the login page for GET requests
        return render_template('voter_login.html')  # Render the login template

    except Exception as e:
        # Print full error traceback for debugging
        print("Error occurred:", e)
        traceback.print_exc()  # Prints the stack trace to the console
        flash(f"An error occurred: {e}", "danger")  # Show error message if an exception occurs
    finally:
        if connection:
            connection.close()  # Ensure the database connection is closed when done

    return redirect(url_for('home'))  # Redirect to home in case of an error

@app.route('/vote-page', methods=['GET', 'POST'])
def vote_page():
    connection = create_connection()  # Create a connection to the database
    if connection is None:
        flash("Database connection error. Please try again later.", "danger")  # Flash an error if the connection fails
        return redirect(url_for('home'))  # Redirect to home page if the connection fails

    try:
        cursor = connection.cursor(dictionary=True)  # Initialize cursor for the database

        # Fetch positions from the positions table
        cursor.execute("SELECT * FROM positions")
        positions = cursor.fetchall()  # Fetch all positions

        # Create a mapping of position ID to name
        position_map = {pos['id']: pos['name'] for pos in positions}

        # Fetch ongoing vote results, grouped by position and candidate type
        cursor.execute("""
            SELECT v.position, v.candidate_id, COUNT(*) AS votes, 
                   c.full_name, c.type, c.party_name
            FROM votes v
            LEFT JOIN (
                SELECT id AS candidate_id, full_name, 'solo' AS type, NULL AS party_name
                FROM solo_applications
                WHERE status = 'approved'
                UNION ALL
                SELECT party_members.id AS candidate_id, party_members.full_name, 
                       'party_member' AS type, party_lists.party_name
                FROM party_lists
                JOIN party_members ON party_lists.id = party_members.party_list_id
                WHERE party_lists.status = 'approved'
            ) c ON v.candidate_id = c.candidate_id
            GROUP BY v.position, v.candidate_id, c.full_name, c.type, c.party_name
            ORDER BY v.position, votes DESC
        """)
        vote_results = cursor.fetchall()  # Fetch the results of the votes

        # Handle POST request for voting
        if request.method == 'POST':
            position = request.form.get('position')  # Get selected position from the form
            candidate_id = request.form.get('candidate')  # Get selected candidate from the form
            candidate_type = request.form.get('candidate_type')  # Get candidate type (solo or party member)

            if not position or not candidate_id or not candidate_type:
                flash("You must select a position, a candidate, and the candidate type!", "danger")
                return redirect(url_for('vote_page'))  # Redirect to vote page if fields are empty

            try:
                position = int(position)  # Convert position to an integer
                candidate_id = int(candidate_id)  # Convert candidate ID to an integer
            except ValueError:
                flash("Invalid position or candidate ID.", "danger")  # Handle invalid ID format
                return redirect(url_for('vote_page'))

            voter_lrn = session.get('lrn')  # Get the voter LRN from the session
            if not voter_lrn:
                flash("Session expired. Please log in again.", "danger")  # Handle expired session
                return redirect(url_for('voters'))  # Redirect to login page

            # Check if the voter has already voted for the selected position
            cursor.execute("""
                SELECT * FROM votes 
                WHERE voter_lrn = %s AND position = %s AND candidate_type = %s
            """, (voter_lrn, position, candidate_type))
            existing_vote = cursor.fetchone()

            if existing_vote:
                flash(f"You have already voted for {position_map.get(position, 'this position')}!", "danger")
                return redirect(url_for('vote_page'))  # Redirect if the voter already voted

            # Validate candidate based on type (solo or party)
            valid_candidate = None
            if candidate_type == 'party_member':
                cursor.execute("""
                    SELECT party_members.id
                    FROM party_members
                    JOIN party_lists ON party_members.party_list_id = party_lists.id
                    WHERE party_members.id = %s AND party_lists.status = 'approved'
                """, (candidate_id,))
                valid_candidate = cursor.fetchone()  # Check if party member is valid

            elif candidate_type == 'solo':
                cursor.execute("""
                    SELECT id FROM solo_applications
                    WHERE id = %s AND status = 'approved'
                """, (candidate_id,))
                valid_candidate = cursor.fetchone()  # Check if solo applicant is valid

            if not valid_candidate:
                flash("Invalid candidate selection.", "danger")
                return redirect(url_for('vote_page'))  # Redirect if candidate is invalid

            # Insert the vote into the votes table
            cursor.execute("""
                INSERT INTO votes (voter_lrn, position, candidate_id, candidate_type)
                VALUES (%s, %s, %s, %s)
            """, (voter_lrn, position, candidate_id, candidate_type))
            connection.commit()  # Commit the transaction
            flash("Vote submitted successfully!", "success")
            return redirect(url_for('vote_page'))  # Redirect after voting successfully

        # Handle GET request to fetch candidates for a selected position
        position_id = request.args.get('position')  # Get position ID from query parameters
        if position_id:
            try:
                position_id = int(position_id)  # Convert position ID to integer
                position_name = position_map.get(position_id)  # Get the position name

                if position_name:
                    # Fetch approved solo applicants for the position
                    cursor.execute("""
                        SELECT id AS candidate_id, full_name 
                        FROM solo_applications 
                        WHERE position = %s AND status = 'approved'
                    """, (position_name,))
                    solo_candidates = cursor.fetchall()

                    # Fetch approved party list members for the position
                    cursor.execute("""
                        SELECT party_members.id AS candidate_id, party_lists.party_name, party_members.full_name
                        FROM party_lists
                        JOIN party_members ON party_lists.id = party_members.party_list_id
                        WHERE party_lists.status = 'approved' AND party_members.position = %s
                    """, (position_name,))
                    party_lists = cursor.fetchall()

                    # Combine solo applicants and party list members
                    candidates = []
                    for solo in solo_candidates:
                        candidates.append({
                            'id': solo['candidate_id'],
                            'name': solo['full_name'],
                            'type': 'solo'
                        })

                    for party in party_lists:
                        candidates.append({
                            'id': party['candidate_id'],
                            'name': party['full_name'],
                            'type': 'party_member',
                            'party_name': party['party_name']
                        })

                    if not candidates:
                        return jsonify({'message': 'No candidates available for this position.'})  # Return if no candidates
                    return jsonify({'candidates': candidates})  # Return list of candidates

            except ValueError:
                flash("Invalid position ID.", "danger")  # Handle invalid position ID
            except Exception as e:
                flash(f"Error fetching candidates: {e}", "danger")  # Flash error if something goes wrong
                return jsonify({'error': 'Error fetching candidates'}), 500  # Return error response

        # Render the vote page with positions and vote results
        return render_template(
            'vote_page.html',
            positions=positions,
            vote_results=vote_results
        )

    except Exception as e:
        print(f"Error occurred in vote_page: {e}")  # Print error for debugging
        flash(f"An error occurred: {e}", "danger")  # Flash a general error message
    finally:
        if connection:
            connection.close()  # Close the connection to the database

    return redirect(url_for('home'))  # Redirect to home in case of error


if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask application
