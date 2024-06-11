import os
import json
import sqlite3
import itertools
import pickle
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_curve, roc_auc_score
from sklearn.ensemble import VotingClassifier
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some_magical_secret_hahahaha'
app.config['UPLOAD_FOLDER'] = './user_upload_data/'
app.config['CHURN_ENGINE_PATH'] = './churn_engine_dump/churn_engine.pkl'

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
    
    files = [{'User_id': u_id,'filename': os.path.basename(file['file_path']).split('_')[1], 'metadata': file['file_metadata'], 'upload_time': file['upload_time']} for file in files]

    return render_template('home.html', files=files)

@app.route('/analyse', methods=['GET', 'POST'])
def analyse():
    if "email" not in session:
        return redirect(url_for('index'))
    
    files = request.form.getlist('selected_files')
    
    # Log the received files for debugging
    print("Received files:", files)

    data_frame_list = []
    for file in files:
        try:
            # Replace single quotes with double quotes
            file = file.replace("'", '"')
            
            # Attempt to parse the JSON string
            file_dict = json.loads(file)
            print("Parsed file_dict:", file_dict)

            # Construct the file path
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_dict['User_id']}_" + file_dict['filename'])
            df = pd.read_csv(file_path)
            data_frame_list.append(df)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for file: {file} - {str(e)}")
        except Exception as e:
            print(f"Error processing file: {file} - {str(e)}")
    
    if not data_frame_list:
        return "No valid files processed.", 400

    df = pd.concat(data_frame_list, ignore_index=True)

    # Load the churn engine model
    with open(app.config['CHURN_ENGINE_PATH'], 'rb') as file:
        churn_engine = pickle.load(file)

    # Preprocess the dataframe
    df = df.drop('customerID', axis=1)
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df = df.dropna()
    df = pd.get_dummies(df, drop_first=True)
    
    scaler = StandardScaler()
    numeric_features = ['tenure', 'MonthlyCharges', 'TotalCharges']
    df[numeric_features] = scaler.fit_transform(df[numeric_features])
    
    X = df.drop('Churn_Yes', axis=1)
    y = df['Churn_Yes']

    # Apply PCA
    pca = PCA(n_components=0.95)
    X_pca = pca.fit_transform(X)
    X_test = X_pca
    
    y_pred = churn_engine.predict(X_test)

    X_pca_top_two = PCA(n_components=2).fit_transform(X)
    X_true = X_pca_top_two[y_pred]
    X_false = X_pca_top_two[~y_pred]

    plt.figure(figsize=(10, 6))
    plt.scatter(X_true[:, 0], X_true[:, 1], color='blue', label='True', alpha=0.5)
    plt.scatter(X_false[:, 0], X_false[:, 1], color='red', label='False', alpha=0.5)
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.title('Scatter Plot of PCA-transformed X values')
    plt.legend()
    plt.grid(True)

    plt.savefig('./static/plots/plot.png')
    plt.show()

    ## ADD THE PREDICTIONS TO THE DATFRAME AND SAVE AS A CSV
    df["Churn_Yes"] = y_pred
    df.to_csv("./engine_gen_data/result.csv")
    return render_template('analysis.html')

@app.route('/download', methods=['POST'])
def download():
    return send_file("./engine_gen_data/result.csv", as_attachment=True)



# def plot_confusion_matrix(cm, classes, title='Confusion Matrix', cmap=plt.cm.Blues):
#     plt.imshow(cm, interpolation='nearest', cmap=cmap)
#     plt.title(title)
#     plt.colorbar()
#     tick_marks = np.arange(len(classes))
#     plt.xticks(tick_marks, classes, rotation=45)
#     plt.yticks(tick_marks, classes)
    
#     fmt = 'd'
#     thresh = cm.max() / 2.
#     for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
#         plt.text(j, i, format(cm[i, j], fmt),
#                  horizontalalignment="center",
#                  color="white" if cm[i, j] > thresh else "black")
    
#     plt.tight_layout()
#     plt.ylabel('True label')
#     plt.xlabel('Predicted label')

if __name__ == '__main__':
    app.run(debug=True)
