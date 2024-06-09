import sqlite3

print("<<<<<<<<<<<<<<<<<<<<<<< SETTING UP DATABASE >>>>>>>>>>>>>>>>>>>>>")

connection = sqlite3.connect('CustChurnDB.db')
cursor = connection.cursor()

create_users_table = '''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
'''

create_files_table = '''
CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_metadata TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
'''

cursor.execute(create_users_table)
print("[+]  Created User Table")
cursor.execute(create_files_table)
print("[+]  Created File Table")

connection.commit()
connection.close()

print("<<<<<<<<<<<<<<<<<<<<<< DATABASE SETUP COMPLETE >>>>>>>>>>>>>>>>>>")
