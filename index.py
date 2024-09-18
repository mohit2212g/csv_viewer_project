from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import os
import hashlib
import jwt
import datetime
import csv
import json 

app = Flask(__name__)
CORS(app)

SECRET_KEY = 'your_secret_key_here'

# Create folders if they don't exist
database_folder = 'sqllite3_database'
uploads_folder = 'uploads'
if not os.path.exists(database_folder):
    os.makedirs(database_folder)
if not os.path.exists(uploads_folder):
    os.makedirs(uploads_folder)

# Path to the user database
USER_DATABASE_PATH = os.path.join(database_folder, 'user.db')

def get_db_connection(db_name):
    conn = sqlite3.connect(os.path.join(database_folder, db_name))
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    conn = get_db_connection('user.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    mobile_number TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

def init_user_table(db_name, columns):
    conn = get_db_connection(db_name)
    column_defs = ', '.join([f'col{idx+1} TEXT' for idx in range(len(columns))])
    conn.execute(f'''CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {column_defs}
                )''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id, username):
    payload = {
        'sub': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = hash_password(data.get('password'))
        mobile_number = data.get('mobile_number')

        conn = get_db_connection('user.db')
        conn.execute('INSERT INTO users (username, email, password, mobile_number) VALUES (?, ?, ?, ?)',
                     (username, email, password, mobile_number))
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "User with this username or email already exists"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = hash_password(data.get('password'))

        conn = get_db_connection('user.db')
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            token = generate_token(user['id'], user['username'])
            return jsonify({"message": "Login successful", "token": token, "user": {"username": user['username'], "email": user['email']}}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload-csv/<username>', methods=['POST'])
def upload_csv(username):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        file_path = os.path.join(uploads_folder, f'{username}.csv')
        file.save(file_path)

        db_name = f'{username}.db'
        db_path = os.path.join(database_folder, db_name)

        # If the database already exists, delete it
        if os.path.exists(db_path):
            os.remove(db_path)

        # Read the CSV file and get columns dynamically
        try:
            with open(file_path, 'r') as csv_file:
                reader = csv.reader(csv_file)
                columns = next(reader)  # Get the first row as column names

                init_user_table(db_name, columns)  # Initialize table with dynamic columns

                conn = get_db_connection(db_name)
                for row in reader:
                    conn.execute(f'INSERT INTO data ({", ".join([f"col{idx+1}" for idx in range(len(columns))])}) VALUES ({", ".join(["?" for _ in columns])})', row)
                conn.commit()
                conn.close()

            return jsonify({"message": "File processed and data uploaded successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file format"}), 400

@app.route('/total-records/<username>', methods=['GET'])
def get_total_records(username):
    try:
        db_name = f'{username}.db'
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM data')
        total_records = cursor.fetchone()[0]
        conn.close()
        return jsonify({"total_records": total_records}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/table-data/<username>', methods=['GET'])
def get_table_data(username):
    try:
        page = int(request.args.get('page', 1))
        rows_per_page = 1000  # Adjust the number of rows per page as needed

        db_name = f'{username}.db'
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        print("username$$$$$$", username)

        # Fetch total number of records for pagination
        cursor.execute('SELECT COUNT(*) FROM data')
        total_records = cursor.fetchone()[0]

        # Fetch the data for the current page
        offset = (page - 1) * rows_per_page
        cursor.execute(f'SELECT * FROM data LIMIT ? OFFSET ?', (rows_per_page, offset))
        data = cursor.fetchall()
        conn.close()

        return jsonify({
            "total_records": total_records,
            "data": [dict(row) for row in data]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/filtered-data/<username>', methods=['GET'])
def get_filtered_data(username):
    try:
        filters = request.args.get('filters', '{}')
        page = int(request.args.get('page', 1))
        rows_per_page = 1000  # Adjust the number of rows per page as needed

        filters = json.loads(filters)  
        db_name = f'{username}.db'
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        print("############filters", filters, db_name, username)

        # Construct SQL query with filters
        query = 'SELECT * FROM data WHERE 1=1'
        params = []

        for column, value in filters.items():
            if value:
                query += f' AND {column} LIKE ?'
                params.append(f'%{value}%')

        # Fetch total number of records for pagination
        cursor.execute(query, params)
        total_records = cursor.rowcount

        # Fetch the data for the current page
        offset = (page - 1) * rows_per_page
        query += f' LIMIT ? OFFSET ?'
        params.extend([rows_per_page, offset])
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()

        return jsonify({
            "total_records": total_records,
            "data": [dict(row) for row in data]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/total-filter-records/<username>', methods=['GET'])
def get_total_filtered_records(username):
    try:
        filters = request.args.get('filters', '{}')
        filters = json.loads(filters)
        
        db_name = f'{username}.db'
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        # Construct SQL query with filters
        query = 'SELECT COUNT(*) FROM data WHERE 1=1'
        params = []

        for column, value in filters.items():
            if value:
                query += f' AND {column} LIKE ?'
                params.append(f'%{value}%')

        cursor.execute(query, params)
        total_records = cursor.fetchone()[0]
        conn.close()

        return jsonify({"total_records": total_records}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    init_user_db()
    app.run(port=5001, debug=True)
