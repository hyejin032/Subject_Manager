from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os

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
        fieldnames = ['email', 'name', 'password', 'faculty', 'c_subjects', 'p_subjects']
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
        if email in users and users[email] == password:
            session['user_email'] = email
            return redirect(url_for('main'))
        return '<p>ログイン失敗しました。</p><p><a href="/">ホームに戻る</a></p>'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        faculty = request.form['faculty']

        users = load_users()
        if email in users:
            return "すでに登録されています。別のメールを使ってください。"

        
        if not email or not name or not password or not faculty:
            return "すべて入力してください"

        save_user(email, name, password, faculty)
        
        return '<p>サインアップ成功</p><p><a href="/">ホームに戻る</a></p>'
    return render_template('signup.html')


@app.route('/main')
def main():
    if 'user_email' not in session:
        return redirect(url_for('login'))  # ログインしていない場合はログイン画面へ
    return render_template('main.html')

@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    users = load_users_with_all_info()
    email = session.get('user_email')
    if email and email in users:
        user = users[email]
        return render_template('mypage.html', user=user)
    return redirect(url_for('login'))

def load_users_with_all_info():
    users = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users[row['email']] = row
    return users

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    email = session.get('user_email')
    users = load_users_with_all_info()
    if not email or email not in users:
        return redirect(url_for('login'))

    user = users[email]

    if request.method == 'POST':
        new_email = request.form['email']
        new_password = request.form['password']
        new_name = request.form['name']
        new_faculty = request.form['faculty']

        # CSV を更新
        update_user_info(email, new_email, new_password, new_name, new_faculty)

        return redirect(url_for('mypage'))

    return render_template('edit_profile.html', user=user)

def update_user_info(email, new_email, new_password, new_name, new_faculty):
    users = []
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['email'] == email:
                row['email'] = new_email
                row['password'] = new_password
                row['name'] = new_name
                row['faculty'] = new_faculty
            users.append(row)

    with open(CSV_FILE, 'w', newline='') as csvfile:
        fieldnames = ['email', 'name', 'password', 'faculty']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

SUBJECTS_CSV = 'subjects.csv'

def load_subjects():
    subjects = []
    if os.path.exists(SUBJECTS_CSV):
        with open(SUBJECTS_CSV, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:  # 空行を無視
                    subjects.append(row[0])
    return subjects

def save_all_users(email, new_c_subjects):
    users  = []
    fieldnames = ['email', 'name', 'password', 'faculty', 'c_subjects', 'p_subjects']
    with open(CSV_FILE, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for row in writer:
            if row['email'] == email:
                row['c_subjects'] = new_c_subjects
            users.append(row)

    with open(CSV_FILE, 'w', newline='') as csvfile:
        fieldnames = ['email', 'name', 'password', 'faculty']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

@app.route('/subjects', methods=['GET', 'POST'])
def subjects():
    subjects = load_subjects()  # ここはSUBJECTSの代わりにCSV読み込み関数でもOK

    email = session.get('user_email')
    if not email:
        return redirect(url_for('login'))

    if request.method == 'POST':
        selected = request.form.getlist('c_subjects')

        users = load_users_with_all_info()
        user = users.get(email)
        if user is None:
            return "ユーザー情報が見つかりません"

        # 現在の科目を取得（空欄なら空リスト）
        current_subjects = user.get('c_subjects', '')
        current_list = [s.strip() for s in current_subjects.split(',')] if current_subjects else []

        # 重複を避けて科目を更新
        updated_subjects = list(set(current_list + selected))

        # カンマ区切りで文字列にして保存
        user['c_subjects'] = ', '.join(updated_subjects)

        # CSVに書き戻す
        save_all_users(email, new_c_subjects)

        return render_template('subjects_confirm.html', selected=selected)

    return render_template('subjects.html', subjects=subjects)



if __name__ == '__main__':
    app.run(debug=True)
