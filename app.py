import sqlite3
from flask import Flask, render_template, redirect, url_for, request, flash, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some_magical_secret_hahahaha'

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

@app.route('/logout')
def logout():
    session.pop("email", None)
    return redirect(url_for('index'))

@app.route('/home')
def home():
    if "email" not in session:
        return redirect(url_for('index'))
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
