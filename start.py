from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask("Subject Manager")
app.secret_key = 'qwerty1234'
CSV_FILE = 'users.csv'

# CSVからユーザーを読み込む
def load_users():
    users = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users[row['email']] = row['password']
    return users

# CSVにユーザーを書き込む
def save_user(email, name, password, faculty):
    exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, 'a', newline='') as csvfile:
        fieldnames = ['email', 'name', 'password', 'faculty']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({'email': email,
            'name': name,
            'password': password,
            'faculty': faculty})

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        if email in users:
            session['user_email'] = email
        return f"ログイン成功（{email}）"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        faculty = request.form['faculty']
        
        if not email or not name or not password or not faculty:
            return "すべて入力してください"
        
        with open('users.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([email, name, password, faculty])
        
        return f"サインアップ成功（{name}）"
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)
