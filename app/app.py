from flask import Flask, jsonify, request, redirect, flash, render_template, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import InternalServerError
from .db_connection import create_connection
from flask_cors import CORS


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Handle Internal Server Errors
@app.errorhandler(InternalServerError)
def internal_error(error):
    return f"An internal error occurred: {error}", 500

# Home Route (Render signup.html as the homepage)
@app.route('/')
def home():
    return render_template('signup.html')

# Login with LRN Route
@app.route('/login-lrn', methods=['POST', 'GET'])
def login_lrn():
    if request.method == 'POST':
        lrn = request.form['lrn']

        if not lrn:
            flash("Please enter your LRN.", "danger")
            return redirect(url_for('login_lrn'))

        connection = create_connection()
        if connection is None:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('login_lrn'))

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))
            valid_lrn = cursor.fetchone()

            if valid_lrn:
                flash("Login successful!", "success")
                return redirect(url_for('index'))
            else:
                flash("Invalid LRN. Please try again.", "danger")
                return render_template('signup.html')
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            connection.close()

    return render_template('loginlrn.html')

# Admin Login Route
@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if request.method == 'POST':
        password = request.form['password']

        connection = create_connection()
        if connection is None:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('admin'))

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
            admin_data = cursor.fetchone()

            if admin_data and check_password_hash(admin_data['password'], password):
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid password. Access Denied.", "danger")
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            connection.close()

    return render_template('admin.html')

# Admin Dashboard
@app.route('/admin-dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    connection = create_connection()
    if connection is None:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for('home'))

    try:
        cursor = connection.cursor(dictionary=True)

        # Fetch valid LRN list and voters data
        cursor.execute("SELECT * FROM valid_lrns")
        valid_lrns = cursor.fetchall()
        cursor.execute("SELECT * FROM voters")
        voters = cursor.fetchall()

        # Fetch pending party list applications and solo applications
        cursor.execute("SELECT * FROM party_lists WHERE status = 'pending'")
        party_list_requests = cursor.fetchall()  # Fetch pending party list requests from party_lists
        cursor.execute("SELECT * FROM solo_applications WHERE status = 'pending'")
        solo_applications = cursor.fetchall()  # Fetch pending solo applications

        if request.method == 'POST':
            new_lrn = request.form.get('new_lrn')
            if new_lrn:
                cursor.execute("INSERT INTO valid_lrns (lrn) VALUES (%s)", (new_lrn,))
                connection.commit()
                flash("New LRN added successfully!", "success")
                return redirect(url_for('admin_dashboard'))

            # Handle approval or decline of party list requests
            if 'approve_party_list' in request.form:
                party_list_id = request.form.get('party_list_id')
                if party_list_id:
                    cursor.execute("UPDATE party_lists SET status = 'approved' WHERE id = %s", (party_list_id,))
                    connection.commit()
                    flash("Party list request approved.", "success")
                return redirect(url_for('admin_dashboard'))

            elif 'decline_party_list' in request.form:
                party_list_id = request.form.get('party_list_id')
                if party_list_id:
                    cursor.execute("UPDATE party_lists SET status = 'rejected' WHERE id = %s", (party_list_id,))
                    connection.commit()
                    flash("Party list request declined.", "danger")
                return redirect(url_for('admin_dashboard'))

            # Handle approval or decline of solo applications
            if 'approve_solo_application' in request.form:
                application_id = request.form.get('application_id')
                if application_id:
                    cursor.execute("UPDATE solo_applications SET status = 'approved' WHERE id = %s", (application_id,))
                    connection.commit()
                    flash("Solo application approved.", "success")
                return redirect(url_for('admin_dashboard'))

            elif 'decline_solo_application' in request.form:
                application_id = request.form.get('application_id')
                if application_id:
                    cursor.execute("UPDATE solo_applications SET status = 'rejected' WHERE id = %s", (application_id,))
                    connection.commit()
                    flash("Solo application rejected.", "danger")
                return redirect(url_for('admin_dashboard'))

        # Render the admin dashboard template with fetched data
        return render_template('admin_dashboard.html', 
                               valid_lrns=valid_lrns, 
                               voters=voters, 
                               party_list_requests=party_list_requests, 
                               solo_applications=solo_applications)

    except Exception as e:
        flash(f"Error occurred: {e}", "danger")
    finally:
        connection.close()

    return redirect(url_for('home'))



@app.route('/application', methods=['GET', 'POST'])
def application():
    if request.method == 'POST':
        try:
            print("Raw Form Data:", request.form)

            # Get form fields
            position = request.form.get('position')  # For solo applications
            is_party = request.form.get('is_party') is not None  # Boolean from checkbox
            party_name = request.form.get('party_name') if is_party else None
            lrn = request.form.get('lrn')

            print(f"Position: {position}, Is Party: {is_party}, Party Name: {party_name}, LRN: {lrn}")

            if not lrn or (not is_party and not position) or (is_party and not party_name):
                flash("Please fill in all required fields.", "danger")
                return redirect(url_for('application'))

            connection = create_connection()
            if connection is None:
                flash("Database connection error. Please try again later.", "danger")
                return redirect(url_for('application'))

            cursor = connection.cursor(dictionary=True)

            # Validate the LRN
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))
            valid_lrn = cursor.fetchone()
            if not valid_lrn:
                flash("Invalid LRN. Please check your LRN and try again.", "danger")
                return redirect(url_for('application'))

            if is_party:
                required_positions = {
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
                    flash("Please fill all positions for the party list.", "danger")
                    return redirect(url_for('application'))

                # Validate LRNs for positions
                for position_name, position_lrn in required_positions.items():
                    cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (position_lrn,))
                    if not cursor.fetchone():
                        flash(f"Invalid LRN for position {position_name}. Please check the LRNs.", "danger")
                        return redirect(url_for('application'))

                # Check if party name is unique
                cursor.execute("SELECT id FROM party_lists WHERE party_name = %s", (party_name,))
                if cursor.fetchone():
                    flash("Party name already exists. Choose another name.", "danger")
                    return redirect(url_for('application'))

                print(f"Inserting into party_lists: {party_name}, {required_positions}")

                cursor.execute("""
                    INSERT INTO party_lists 
                    (party_name, president_lrn, vice_president_lrn, secretary_lrn, treasurer_lrn, 
                    auditor_lrn, po_lrn, pio_lrn, g7_rep_lrn, g8_rep_lrn, g9_rep_lrn, g10_rep_lrn, g11_rep_lrn, g12_rep_lrn, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                """, (party_name, *required_positions.values()))
                connection.commit()

                party_list_id = cursor.lastrowid
                print(f"Party list inserted successfully with ID: {party_list_id}")

                for position_name, position_lrn in required_positions.items():
                    cursor.execute("""
                        INSERT INTO party_members (party_list_id, lrn, position)
                        VALUES (%s, %s, %s)
                    """, (party_list_id, position_lrn, position_name))
                connection.commit()

                print("Party members inserted successfully!")

            else:
                # Prevent duplicate solo applications
                cursor.execute("SELECT id FROM solo_applications WHERE lrn = %s", (lrn,))
                if cursor.fetchone():
                    flash("You have already applied for a position.", "danger")
                    return redirect(url_for('application'))

                cursor.execute("INSERT INTO solo_applications (position, lrn) VALUES (%s, %s)", (position, lrn))
                connection.commit()
                print("Solo application inserted successfully!")

            flash("Application submitted successfully.", "success")
            return redirect(url_for('application'))

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('application'))

    return render_template('application.html')

# Edit Page Route
@app.route('/edit-page', methods=['GET', 'POST'])
def edit_page():
    if request.method == 'POST':
        lrn = request.form.get('lrn')
        new_password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')

        # Check if LRN, password, full_name, and email are not empty
        if not lrn or not new_password or not full_name or not email:
            flash("All fields (LRN, password, full name, and email) are required.", "danger")
            return redirect(url_for('edit_page'))

        connection = create_connection()
        if connection is None:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('edit_page'))

        try:
            cursor = connection.cursor(dictionary=True)

            # Check if the LRN exists in the valid_lrns table
            cursor.execute("SELECT * FROM valid_lrns WHERE lrn = %s", (lrn,))
            valid_lrn = cursor.fetchone()

            if not valid_lrn:
                flash("Invalid LRN. Only valid LRNs can set a password.", "danger")
                return redirect(url_for('edit_page'))

            # Check if the voter already exists in the voters table
            cursor.execute("SELECT * FROM voters WHERE lrn = %s", (lrn,))
            voter = cursor.fetchone()

            if voter:
                # Check if the password is already set (i.e., don't update if it already exists)
                if voter['password']:
                    flash("Password has already been set and cannot be changed.", "danger")
                else:
                    # Update the password, full name, and email
                    cursor.execute("""
                        UPDATE voters
                        SET password = %s, full_name = %s, email = %s
                        WHERE lrn = %s
                    """, (new_password, full_name, email, lrn))
                    flash("Password, full name, and email updated successfully!", "success")  # Success message
            else:
                # Insert new voter data into the database
                cursor.execute("""
                    INSERT INTO voters (lrn, full_name, email, password)
                    VALUES (%s, %s, %s, %s)
                """, (lrn, full_name, email, new_password))
                flash("Password, full name, and email set successfully!", "success")  # Success message

            connection.commit()

        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            connection.close()

        return redirect(url_for('edit_page'))

    return render_template('edit.html')


# Home route to render index.html at /home
@app.route('/home')
def index():
    return render_template('index.html')

# Voters Route to fetch and display all voters
import traceback

@app.route('/voters', methods=['GET', 'POST'])
def voters():
    connection = create_connection()
    if connection is None:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for('home'))  # Redirect to home if database connection fails

    try:
        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':
            lrn = request.form.get('username')
            password = request.form.get('password')

            if not lrn or not password:
                flash("LRN and Password are required!", "danger")
                return redirect(url_for('voters'))  # Redirect back to voters page if fields are empty

            cursor.execute("SELECT * FROM voters WHERE lrn = %s", (lrn,))
            voter = cursor.fetchone()

            if voter:
                if voter['password'] == password:  
                    session['lrn'] = voter['lrn']
                    session['full_name'] = voter['full_name']
                    flash(f"Welcome, {voter['full_name']}!", "success")
                    return redirect(url_for('vote_page'))  # Should redirect to vote_page
                else:
                    flash("Incorrect password!", "danger")
            else:
                flash("LRN not found!", "danger")

            return redirect(url_for('voters'))  # Return to voters page if login fails

        # Render the login page for GET requests
        return render_template('voter_login.html')

    except Exception as e:
        # Print full error traceback for debugging
        print("Error occurred:", e)
        traceback.print_exc()  # Prints the stack trace to the console
        flash(f"An error occurred: {e}", "danger")
    finally:
        if connection:
            connection.close()

    return redirect(url_for('home'))  # Redirect to home in case of an error


@app.route('/vote-page', methods=['GET', 'POST'])
def vote_page():
    connection = create_connection()
    if connection is None:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for('home'))

    try:
        cursor = connection.cursor(dictionary=True)

        # Fetch positions from positions table
        cursor.execute("SELECT * FROM positions")
        positions = cursor.fetchall()

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
        vote_results = cursor.fetchall()

        # Handle POST request (voting)
        if request.method == 'POST':
            position = request.form.get('position')
            candidate_id = request.form.get('candidate')
            candidate_type = request.form.get('candidate_type')  # Fetch the candidate type

            if not position or not candidate_id or not candidate_type:
                flash("You must select a position, a candidate, and the candidate type!", "danger")
                return redirect(url_for('vote_page'))

            try:
                position = int(position)
                candidate_id = int(candidate_id)
            except ValueError:
                flash("Invalid position or candidate ID.", "danger")
                return redirect(url_for('vote_page'))

            voter_lrn = session.get('lrn')
            if not voter_lrn:
                flash("Session expired. Please log in again.", "danger")
                return redirect(url_for('voters'))

            # Check if the voter has already voted for the selected position (solo or party)
            cursor.execute("""
                SELECT * FROM votes 
                WHERE voter_lrn = %s AND position = %s AND candidate_type = %s
            """, (voter_lrn, position, candidate_type))
            existing_vote = cursor.fetchone()

            if existing_vote:
                flash(f"You have already voted for {position_map.get(position, 'this position')}!", "danger")
                return redirect(url_for('vote_page'))

            # Validate candidate based on type (solo or party_member)
            valid_candidate = None
            if candidate_type == 'party_member':
                cursor.execute("""
                    SELECT party_members.id
                    FROM party_members
                    JOIN party_lists ON party_members.party_list_id = party_lists.id
                    WHERE party_members.id = %s AND party_lists.status = 'approved'
                """, (candidate_id,))
                valid_candidate = cursor.fetchone()

            elif candidate_type == 'solo':
                cursor.execute("""
                    SELECT id FROM solo_applications
                    WHERE id = %s AND status = 'approved'
                """, (candidate_id,))
                valid_candidate = cursor.fetchone()

            if not valid_candidate:
                flash("Invalid candidate selection.", "danger")
                return redirect(url_for('vote_page'))

            # Insert the vote into the votes table, including the candidate type
            cursor.execute("""
                INSERT INTO votes (voter_lrn, position, candidate_id, candidate_type)
                VALUES (%s, %s, %s, %s)
            """, (voter_lrn, position, candidate_id, candidate_type))
            connection.commit()
            flash("Vote submitted successfully!", "success")
            return redirect(url_for('vote_page'))

        # Handle GET request to fetch candidates based on selected position
        position_id = request.args.get('position')
        if position_id:
            try:
                position_id = int(position_id)
                position_name = position_map.get(position_id)

                if position_name:
                    # Fetch approved solo applicants based on the position
                    cursor.execute("""
                        SELECT id AS candidate_id, full_name 
                        FROM solo_applications 
                        WHERE position = %s AND status = 'approved'
                    """, (position_name,))
                    solo_candidates = cursor.fetchall()

                    # Fetch approved party list members for the selected position
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
                        return jsonify({'message': 'No candidates available for this position.'})
                    return jsonify({'candidates': candidates})

            except ValueError:
                flash("Invalid position ID.", "danger")
            except Exception as e:
                flash(f"Error fetching candidates: {e}", "danger")
                return jsonify({'error': 'Error fetching candidates'}), 500

        # Render the vote page with fetched data
        return render_template(
            'vote_page.html',
            positions=positions,
            vote_results=vote_results
        )

    except Exception as e:
        print(f"Error occurred in vote_page: {e}")
        flash(f"An error occurred: {e}", "danger")
    finally:
        if connection:
            connection.close()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
