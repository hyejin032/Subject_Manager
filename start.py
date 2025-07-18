from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
import uuid
from datetime import datetime

app = Flask("Subject Manager")
app.secret_key = 'qwerty1234'
USERS_CSV_FILE = 'users.csv'
SUBJECTS_CSV_FILE = 'subjects.csv'
COMMENTS_CSV_FILE = 'comments.csv'
ARTICLE_CSV_FILE = 'article.csv'
FIELDNAMES = ['email', 'name', 'password', 'faculty', 'c_subjects', 'p_subjects']
ARTICLE_FIELDNAMES = ['id', 'parent_id', 'user_email', 'content', 'created_at']

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

def save_article(articles):
    """掲示板の全投稿を保存する"""
    try:
        with open(ARTICLE_CSV_FILE, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=ARTICLE_FIELDNAMES)
            writer.writeheader()
            writer.writerows(articles)
    except Exception as e:
        print(f"Error saving articles: {e}")

def load_comments(subject):
    comments = []
    
    if os.path.exists(COMMENTS_CSV_FILE):
        try:
            with open(COMMENTS_CSV_FILE, mode='r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['subject'] == subject:
                        comments.append({
                            'comment_id': row['comment_id'],  
                            'user_email': row['user_email'],
                            'comment': row['comment']
                        })
        except (IOError, csv.Error) as e:
            print(f"Error loading comments: {e}")
    
    return comments

# コメントを保存する関数

def save_comment(subject, comment, user_email):
    comment_id = str(uuid.uuid4())  # 一意なID
    with open(COMMENTS_CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['comment_id', 'subject', 'user_email', 'comment'])
        writer.writerow({
            'comment_id': comment_id,
            'subject': subject,
            'user_email': user_email,
            'comment': comment
        })


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
            comment_id = request.form['delete_comment']
            delete_comment(subject, comment_id)
        return redirect(url_for('view_comments', subject=subject))

    return render_template('comment_page.html', subject=subject, comments=comments)

def delete_comment(subject, comment_id):
    try:
        comments = []
        with open(COMMENTS_CSV_FILE, mode='r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not (row['subject'] == subject and row['comment_id'] == comment_id):
                    comments.append(row)

        with open(COMMENTS_CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['comment_id', 'subject', 'user_email', 'comment'])
            writer.writeheader()
            writer.writerows(comments)
    except (IOError, csv.Error) as e:
        print(f"Error deleting comment: {e}")


@app.route('/board', methods=['GET', 'POST'])
def board():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form.get('content')
        user_email = session['user_email']
        
        if content:
            articles = load_articles()
            new_id = 1
            if articles:
                valid_ids = [int(a['id']) for a in articles if a.get('id') and a['id'].isdigit()]
                if valid_ids:
                    new_id = max(valid_ids) + 1

            new_article = {
                'id': str(new_id),
                'parent_id': '',
                'user_email': user_email,
                'content': content,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            articles.append(new_article)
            save_article(articles)
        
        return redirect(url_for('board'))

    # GETリクエスト: 親投稿とそれに紐づく返信を整理して表示
    all_articles = load_articles()
    articles_dict = {article['id']: article for article in all_articles}

    for article in articles_dict.values():
        article['replies'] = []

    posts = []
    for article in articles_dict.values():
        parent_id = article.get('parent_id')
        if parent_id and parent_id in articles_dict:
            articles_dict[parent_id]['replies'].append(article)
        else:
            posts.append(article)
    
    posts.sort(key=lambda p: int(p.get('id', 0)), reverse=True)
    for post in posts:
        post['replies'].sort(key=lambda r: int(r.get('id', 0)))

    return render_template('board.html', posts=posts)

@app.route('/reply/<int:post_id>', methods=['GET', 'POST'])
def reply(post_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))

    articles = load_articles()
    parent_post = next((article for article in articles if article.get('id') == str(post_id)), None)

    if not parent_post:
        return "投稿が見つかりません。", 404

    if request.method == 'POST':
        content = request.form.get('content')
        user_email = session['user_email']

        if content:
            new_id = 1
            if articles:
                valid_ids = [int(a['id']) for a in articles if a.get('id') and a['id'].isdigit()]
                if valid_ids:
                    new_id = max(valid_ids) + 1
            
            new_reply = {
                'id': str(new_id),
                'parent_id': str(post_id),
                'user_email': user_email,
                'content': content,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            articles.append(new_reply)
            save_article(articles)
        
        return redirect(url_for('board'))

    # GETリクエスト: 親投稿と既存の返信を表示
    replies = [reply for reply in articles if reply.get('parent_id') == str(post_id)]
    replies.sort(key=lambda r: int(r.get('id', 0)))

    return render_template('reply.html', post=parent_post, replies=replies)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    """投稿とその返信を削除する"""
    if 'user_email' not in session:
        return redirect(url_for('login'))

    post_id_to_delete = str(post_id)
    user_email = session['user_email']
    all_articles = load_articles()

    # 削除対象の投稿を特定
    post_to_delete = next((p for p in all_articles if p.get('id') == post_id_to_delete), None)

    # 投稿が存在しない、または投稿者本人でない場合は何もしない
    if not post_to_delete or post_to_delete.get('user_email') != user_email:
        return redirect(url_for('board'))

    # 削除する投稿(親)のIDと、その返信のIDをリストアップ
    ids_to_remove = {post_id_to_delete}
    # この実装では返信にさらに返信はできないため、1階層のみチェック
    for article in all_articles:
        if article.get('parent_id') == post_id_to_delete:
            ids_to_remove.add(article.get('id'))

    # 削除対象以外の投稿だけを残す
    articles_to_keep = [p for p in all_articles if p.get('id') not in ids_to_remove]
    
    save_article(articles_to_keep)

    return redirect(url_for('board'))


if __name__ == '__main__':
    # Ensure the users.csv file exists with a header if it's not there
    if not os.path.exists(USERS_CSV_FILE):
        with open(USERS_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
    
    app.run(debug=True)

