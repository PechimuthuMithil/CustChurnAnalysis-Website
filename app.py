import os
import sqlite3
from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some_magical_secret_hahahaha'
app.config['UPLOAD_FOLDER'] = './server_data/'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def index():
    return render_template("root.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        query = "SELECT * from users where email=? and password=?"
        cursor = conn.execute(query, (email, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session["email"] = email
            return redirect(url_for("home"))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        try:
            query = "INSERT INTO users (email, password) VALUES (?, ?)"
            conn.execute(query, (email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Email already exists')
            return render_template('signup.html')
        finally:
            conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop("email", None)
    return redirect(url_for('index'))

@app.route('/home', methods=['GET', 'POST'])
def home():
    if "email" not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    query_user_id = "SELECT user_id FROM users WHERE email=?"
    cursor = conn.execute(query_user_id, (session["email"],))
    user = cursor.fetchone()
    u_id = user['user_id'] if user else None
    conn.close()

    if not u_id:
        flash('User not found')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        metadata = request.form.get('metadata', '')

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{u_id}_" + filename)
            file.save(file_path)

            conn = get_db_connection()
            query = "INSERT INTO files (user_id, file_path, file_metadata) VALUES (?, ?, ?)"
            conn.execute(query, (u_id, file_path, metadata))
            conn.commit()
            conn.close()

            flash('File successfully uploaded')

            # [TODO] ADD FUNCTION TO REMOVE UPLOADED FILE
        else:
            flash('Invalid file type. Only CSV files are allowed.')

    conn = get_db_connection()
    query = "SELECT file_id, file_path, upload_time, file_metadata FROM files WHERE user_id=?"
    cursor = conn.execute(query, (u_id,))
    files = cursor.fetchall()
    conn.close()
    
    files = [{'filename': os.path.basename(file['file_path']), 'metadata': file['file_metadata'], 'upload_time': file['upload_time']} for file in files]

    return render_template('home.html', files=files)

@app.route('/analyse', methods=['GET', 'POST'])
def analyse():
    if "email" not in session:
        return redirect(url_for('index'))
    files=request.form.getlist('selected_files')
    
    # USE THE FILES TO DO THE PRICESSING
    # CURRENT IDEA IS TO SAVETHE GRAPHS AS IMAGES AND RENDER INTO THE PAGE

    return render_template('analysis.html', files=files)

if __name__ == '__main__':
    app.run(debug=True)
