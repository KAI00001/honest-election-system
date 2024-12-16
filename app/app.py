from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

# Database connection function
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Update with your DB password
            database="honest_election"
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for flash messages

# Home Route
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')  # Ensure 'home.html' exists in your templates folder

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Collect form data
            aadhaar = request.form['aadhaar']
            fname = request.form['fname']
            lname = request.form['lname']
            gender = request.form['gender']
            birthday = request.form['birthday']
            phone = request.form['phone']
            email = request.form['email']
            locality = request.form['locality']
            city = request.form['city']
            state = request.form['state']
            password = request.form['password']

            # Validate inputs
            if len(aadhaar) != 12 or not aadhaar.isnumeric():
                flash("Invalid Aadhaar number!", "danger")
                return redirect(url_for('signup'))

            if len(phone) != 10 or not phone.isnumeric():
                flash("Invalid phone number!", "danger")
                return redirect(url_for('signup'))

            if '@' not in email or '.' not in email:
                flash("Invalid email address!", "danger")
                return redirect(url_for('signup'))

            # Validate and insert into database
            db = connect_to_db()
            cursor = db.cursor()

            # Check if Aadhaar is already registered
            query = "SELECT FirstName FROM voter_table WHERE Aadhaar=%s"
            cursor.execute(query, (aadhaar,))
            result = cursor.fetchone()
            if result:
                flash("You are already registered!", "danger")
                return redirect(url_for('signup'))

            # Insert voter details into the database
            insert_query = """
            INSERT INTO voter_table (Aadhaar, FirstName, LastName, Gender, DOB, Phone, Email, Locality, City, State, Password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (aadhaar, fname, lname, gender, birthday, phone, email, locality, city, state, password))
            db.commit()

            flash("Signup successful! Please save your voter ID.", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            if db.is_connected():
                cursor.close()
                db.close()

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            aadhaar = request.form['aadhaar']
            voter_id = request.form['voter_id']
            password = request.form['password']

            # Authenticate user
            db = connect_to_db()
            cursor = db.cursor()
            query = "SELECT _Password FROM user_table WHERE VoterId=%s AND Aadhaar=%s"
            cursor.execute(query, (voter_id, aadhaar))
            result = cursor.fetchone()

            if result and result[0] == password:
                flash("Login successful!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid Aadhaar, Voter ID, or Password", "danger")
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            if db.is_connected():
                cursor.close()
                db.close()

    return render_template('login.html')

# Party Registration Route
@app.route('/party-registration', methods=['GET', 'POST'])
def party_registration():
    if request.method == 'POST':
        try:
            # Collect form data
            party_name = request.form['party_name']
            symbol = request.form['symbol']
            leader_name = request.form['leader_name']
            leader_aadhaar = request.form['leader_aadhaar']

            # Validate inputs
            if not party_name.isalpha():
                flash("Party name can only contain letters.", "danger")
                return redirect(url_for('party_registration'))

            if not symbol.isalpha():
                flash("Party symbol can only contain letters.", "danger")
                return redirect(url_for('party_registration'))

            # Validate and insert into database
            db = connect_to_db()
            cursor = db.cursor()
            query = """
            INSERT INTO party_table (PartyName, Symbol, PartyLeader, LeaderAadhaar)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (party_name, symbol, leader_name, leader_aadhaar))
            db.commit()

            flash("Party registered successfully!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        finally:
            if db.is_connected():
                cursor.close()
                db.close()

    return render_template('party_registration.html')

if __name__ == '__main__':
    app.run(debug=True)
