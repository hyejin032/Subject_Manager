from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
from datetime import datetime

app = Flask("Subject Manager")
app.secret_key = 'qwerty1234'
USERS_CSV_FILE = 'users.csv'
SUBJECTS_CSV_FILE = 'subjects.csv'
COMMENTS_CSV_FILE = 'comments.csv'
ARTICLE_CSV_FILE = 'article.csv'
FIELDNAMES = ['email', 'name', 'password', 'faculty', 'c_subjects', 'p_subjects']

# --- CSV Helper Functions ---
def load_articles():
    """掲示板の投稿一覧を読み込む"""
    articles = []
    if os.path.exists(ARTICLE_CSV_FILE):
        print("DEBUG - article.csv found")
        with open(ARTICLE_CSV_FILE, mode='r', newline='', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print("DEBUG - Loaded row:", row) 
                articles.append(row)
    else:
        print("DEBUG - article.csv not found")
    return articles

def save_article(user_email, content, parent_id=None):
    """新しい投稿または返信を保存"""
    new_id = 1
    articles = load_articles()
    
    if articles:
        new_id = max(int(article['id']) for article in articles) + 1  # 最新のIDを生成

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    article = {
        'id': str(new_id),
        'parent_id': parent_id,  # 親投稿がある場合は親ID
        'user_email': user_email,
        'content': content,
        'created_at': timestamp
    }

    # 既存の投稿に追加
    articles.append(article)

    with open(ARTICLE_CSV_FILE, mode='w', newline='', encoding='utf-8-sig') as file:
        fieldnames = ['id', 'parent_id', 'user_email', 'content', 'created_at']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(articles)

def load_comments(subject):
    comments = []
    
    if os.path.exists(COMMENTS_CSV_FILE):
        try:
            with open(COMMENTS_CSV_FILE, mode='r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['subject'] == subject:
                        comments.append({
                            'user_email': row['user_email'],
                            'comment': row['comment']
                        })
        except (IOError, csv.Error) as e:
            print(f"Error loading comments: {e}")
    
    return comments

# コメントを保存する関数
def save_comment(subject, comment_text, user_email):
    try:
        # コメントがなければ、ファイルのヘッダーを作成
        if not os.path.exists(COMMENTS_CSV_FILE):
            with open(COMMENTS_CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['subject', 'user_email', 'comment'])
                writer.writeheader()
        
        # コメントをファイルに追加
        with open(COMMENTS_CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['subject', 'user_email', 'comment'])
            writer.writerow({
                'subject': subject,
                'user_email': user_email,
                'comment': comment_text
            })
    except IOError as e:
        print(f"Error saving comment: {e}")


def load_all_users():
    if not os.path.exists(USERS_CSV_FILE):
        return {}
    
    users = {}
    try:
        # Use utf-8-sig to handle potential BOM (Byte Order Mark) and ensure correct encoding
        with open(USERS_CSV_FILE, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Ensure all expected keys exist
                if 'email' in row:
                    users[row['email']] = row
    except (IOError, csv.Error) as e:
        print(f"Error loading users: {e}")
        return {}
    return users

def save_all_users(users_dict):
    """
    Writes the entire dictionary of users to the CSV file, overwriting it.
    """
    try:
        with open(USERS_CSV_FILE, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(users_dict.values())
    except IOError as e:
        print(f"Error saving users: {e}")

# --- Route Definitions ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_all_users()
        
        # Check if user exists and password matches
        if email in users and users[email].get('password') == password:
            session['user_email'] = email
            return redirect(url_for('main'))
        
        return '<p>ログイン失敗しました。メールアドレスまたはパスワードが間違っています。</p><p><a href="/">ホームに戻る</a></p>'
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        faculty = request.form.get('faculty')

        if not all([email, name, password, faculty]):
            return "すべての項目を入力してください。"

        users = load_all_users()
        if email in users:
            return "このメールアドレスはすでに登録されています。別のメールアドレスを使用してください。"

        # Add new user to the dictionary
        users[email] = {
            'email': email,
            'name': name,
            'password': password,
            'faculty': faculty,
            'c_subjects': '',
            'p_subjects': ''
        }
        
        # Save all users back to the file
        save_all_users(users)
        
        return '<p>サインアップ成功</p><p><a href="/login">ログインページへ</a></p>'
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('home'))

@app.route('/main')
def main():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/mypage')
def mypage():
    if 'user_email' not in session:
        return redirect(url_for('login'))
        
    email = session['user_email']
    users = load_all_users()
    user = users.get(email)

    if not user:
        # If user somehow doesn't exist in CSV, clear session and redirect to login
        session.pop('user_email', None)
        return redirect(url_for('login'))
        
    return render_template('mypage.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    current_email = session['user_email']
    users = load_all_users()
    user_data = users.get(current_email)

    if not user_data:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get new data from form
        new_email = request.form['email']
        new_name = request.form['name']
        new_password = request.form['password']
        new_faculty = request.form['faculty']

        # If email is changed, we need to handle the key change in the dictionary
        if current_email != new_email:
            # Check if the new email already exists
            if new_email in users:
                return "そのメールアドレスは既に使用されています。"
            # Remove old entry
            users.pop(current_email)
        
        # Update user data
        updated_user = {
            'email': new_email,
            'name': new_name,
            'password': new_password,
            'faculty': new_faculty,
            'c_subjects': user_data.get('c_subjects', ''), # Preserve subjects
            'p_subjects': user_data.get('p_subjects', '')  # Preserve subjects
        }
        
        users[new_email] = updated_user
        save_all_users(users)
        
        # Update session with new email
        session['user_email'] = new_email
        
        return redirect(url_for('mypage'))

    return render_template('edit_profile.html', user=user_data)


def load_subjects_from_csv():
    """Loads all subjects from the subjects CSV file."""
    subjects = []
    if os.path.exists(SUBJECTS_CSV_FILE):
        try:
            with open(SUBJECTS_CSV_FILE, mode='r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                # Skip header if it exists
                next(reader, None) 
                for row in reader:
                    if row: 
                        subjects.append(row[0])
        except (IOError, csv.Error) as e:
            print(f"Error loading subjects: {e}")
    return subjects


@app.route('/subjects', methods=['GET', 'POST'])
def subjects():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    email = session['user_email']
    all_subjects = load_subjects_from_csv()

    if request.method == 'POST':
        print("DEBUG subjects form:", request.form)  # フォーム全体の内容を表示
        selected_subjects = request.form.getlist('subjects')
        print("DEBUG selected subjects:", selected_subjects)  # チェックされた科目を表示
        action = request.form.get('action')
        print("DEBUG action:", action)  # 選ばれたアクションを表示

        print("DEBUG session email:", email)  # セッションのemailを表示
        
        users = load_all_users()
        user = users.get(email)

        if not user:
            return "ユーザー情報が見つかりません。"

        updated_list = sorted(list(set(selected_subjects)))
        subjects_str = ', '.join(updated_list)
        
        confirmation_message = ""

        if action == 'completed':
            user['c_subjects'] = subjects_str
            confirmation_message = "以下の科目を履修済みとして登録しました。"
        elif action == 'planned':
            user['p_subjects'] = subjects_str
            confirmation_message = "以下の科目を履修予定として登録しました。"
        else:
            # actionが不正な場合は科目選択ページにリダイレクト
            return redirect(url_for('subjects'))

        save_all_users(users)

        # 確認ページにメッセージを渡す
        return render_template('subjects_confirm.html', selected=updated_list, message=confirmation_message)

    # GETリクエストの場合、チェックボックスはすべて未チェックの状態で表示
    return render_template('subjects.html', subjects=all_subjects)


@app.route('/subject_comment')
def subject_comment():
    all_subjects = load_subjects_from_csv()  # すでに作成した関数で科目を読み込み
    return render_template('subject_comment.html', subjects=all_subjects)

@app.route('/comments/<subject>', methods=['GET', 'POST'])
def view_comments(subject):
    if 'user_email' not in session:
        return redirect(url_for('login'))

    comments = load_comments(subject)  # コメントを読み込む

    if request.method == 'POST':
        if 'comment' in request.form:
            # 新しいコメントを投稿
            comment_text = request.form['comment']
            user_email = session['user_email']
            save_comment(subject, comment_text, user_email)  # コメントを保存
            return redirect(url_for('view_comments', subject=subject))

        if 'delete_comment' in request.form:
            # 削除ボタンが押された場合
            comment_id = request.form['delete_comment']
            delete_comment(subject, comment_id)  # コメントを削除
            return redirect(url_for('view_comments', subject=subject))

    return render_template('comment_page.html', subject=subject, comments=comments)

def delete_comment(subject, comment_text):
    try:
        # 既存のコメントを読み込む
        comments = []
        with open(COMMENTS_CSV_FILE, mode='r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['subject'] == subject and row['comment'] != comment_text:
                    comments.append(row)

        # 更新されたコメントリストをファイルに書き込み
        with open(COMMENTS_CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['subject', 'user_email', 'comment'])
            writer.writeheader()
            writer.writerows(comments)
    except (IOError, csv.Error) as e:
        print(f"Error deleting comment: {e}")

@app.route('/board', methods=['GET', 'POST'])
def board():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    articles = load_articles()
    # 親投稿と返信を分ける
    posts = [article for article in articles if article['parent_id'] is None]
    
    if request.method == 'POST':
        # 投稿または返信の保存
        content = request.form['content']
        parent_id = request.form.get('parent_id')
        user_email = session['user_email']
        
        save_article(user_email, content, parent_id)
        return redirect(url_for('board'))
    print("DEBUG - posts:", posts)
    
    return render_template('board.html', posts=posts)

@app.route('/reply/<int:post_id>', methods=['GET', 'POST'])
def reply(post_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        content = request.form['content']
        user_email = session['user_email']
        
        # 返信を保存
        save_article(user_email, content, parent_id=post_id)
        return redirect(url_for('board'))
    
    return render_template('reply.html', post_id=post_id)




if __name__ == '__main__':
    # Ensure the users.csv file exists with a header if it's not there
    if not os.path.exists(USERS_CSV_FILE):
        with open(USERS_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
    
    app.run(debug=True)

