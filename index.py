from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import os
import hashlib
import jwt
import datetime
import csv
import json 
from flask import send_file

app = Flask(__name__)
CORS(app)

# Set the maximum request size to 10GB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024

SECRET_KEY = 'your_secret_key_here'

database_folder = 'sqllite3_database'
uploads_folder = 'uploads'
if not os.path.exists(database_folder):
    os.makedirs(database_folder)
if not os.path.exists(uploads_folder):
    os.makedirs(uploads_folder)

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
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
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
    print("file : " , file)
    print("filename : ", file.filename)
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    print("###############", file)

    if file and file.filename.lower().endswith('.csv'):
        print("###############", file)
        file_path = os.path.join(uploads_folder, f'{username}.csv')
        file.save(file_path)

        db_name = f'{username}.db'
        db_path = os.path.join(database_folder, db_name)

        print("If the database already exists, delete it")
        if os.path.exists(db_path):
            os.remove(db_path)

        try:
            with open(file_path, 'r') as csv_file:
                reader = csv.reader(csv_file)
                columns = next(reader)  

                print("file_path, columns and db_name: ", file_path , columns, db_name)

                init_user_table(db_name, columns)  

                conn = get_db_connection(db_name)
                for row in reader:
                    conn.execute(f'INSERT INTO data ({", ".join([f"col{idx+1}" for idx in range(len(columns))])}) VALUES ({", ".join(["?" for _ in columns])})', row)
                conn.commit()
                conn.close()

                print("File processed and data uploaded successfully")

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
        rows_per_page = 1000 

        db_name = f'{username}.db'
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        print("username$$$$$$", username)

        cursor.execute('SELECT COUNT(*) FROM data')
        total_records = cursor.fetchone()[0]

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
    print("get_filtered_data called")
    try:
        filters = request.args.get('filters', '{}')
        page = int(request.args.get('page', 1))
        rows_per_page = 1000  

        filters = json.loads(filters)  
        db_name = f'{username}.db'
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        print("############filters", filters, db_name, username)

        query = 'SELECT * FROM data WHERE 1=1'
        params = []

        for column, value in filters.items():
            if value:
                query += f' AND {column} LIKE ?'
                params.append(f'%{value}%')

        cursor.execute(query, params)
        total_records = cursor.rowcount

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

@app.route('/download-filtered-file/<username>', methods=['GET'])
def download_filtered_file(username):
    try:
        filters = request.args.get('filters', '{}')
        filters = json.loads(filters)

        db_name = f'{username}.db'
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        query = 'SELECT * FROM data WHERE 1=1'
        params = []

        for column, value in filters.items():
            if value:
                query += f' AND {column} LIKE ?'
                params.append(f'%{value}%')

        cursor.execute(query, params)
        data = cursor.fetchall()

        csv_file = os.path.join(uploads_folder, 'filtered_data.csv')
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            # Write headers
            headers = [desc[0] for desc in cursor.description]
            writer.writerow(headers)
            # Write data rows
            for row in data:
                writer.writerow(row)

        conn.close()

        # Send the CSV file as response
        return send_file(csv_file, mimetype='text/csv', as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    init_user_db()
    app.run(host='192.168.10.107',  port=5001, debug=True)
    # app.run(port=5001, debug=True)
