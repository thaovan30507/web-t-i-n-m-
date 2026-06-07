from flask import Flask, render_template, request, session, redirect, url_for, flash
from models import db, User, Word
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Cấu hình Database SQLite và Mã bảo mật cho Session
app.config['SECRET_KEY'] = 'tu_dien_bi_mat_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///opent_dict.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Kết nối SQLAlchemy với Flask app
db.init_app(app)

# Hàm nạp dữ liệu mẫu từ csv vào database (chỉ chạy khi DB trống)
def seed_data():
    if not Word.query.first(): 
        print("Phát hiện database đang trống. Đang nạp từ vựng từ file CSV...")
        try:
            # Tạo sẵn 1 tài khoản admin mặc định để gán vào added_by
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(username='admin', password='admin123', role='admin')
                db.session.add(admin_user)
                db.session.commit() 

            # Đọc file CSV 
            with open('word.csv', mode='r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    new_word = Word(
                        english_word=row['english_word'].strip(),
                        phonetics=row['phonetics'].strip(),
                        word_type=row['word_type'].strip(),
                        vietnamese_meaning=row['vietnamese_meaning'].strip(), 
                        example_sentence=row['example_sentence'].strip(),
                        added_by=admin_user.id
                    )
                    db.session.add(new_word)
                db.session.commit()
                print("Nạp dữ liệu từ điển từ file CSV thành công!")
        except Exception as e:
            print(f"Lỗi khi đọc file CSV hoặc nạp Database: {e}")

#ROUTE TRANG CHỦ & TÌM KIẾM
@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    words = [] 
    
    if search_query:
        words = Word.query.filter(
            (Word.english_word.like(f"%{search_query}%")) | 
            (Word.vietnamese_meaning.like(f"%{search_query}%"))
        ).all()
        
    return render_template('index.html', words=words, search_query=search_query)

#TÍNH NĂNG ĐĂNG KÝ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Tài khoản này đã tồn tại!', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Đăng ký thành công! Hãy đăng nhập.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

#TÍNH NĂNG ĐĂNG NHẬP
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Chào mừng {user.username} đã quay trở lại!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Sai tài khoản hoặc mật khẩu!', 'danger')
            
    return render_template('login.html')

# TÍNH NĂNG ĐĂNG XUẤT 
@app.route('/logout')
def logout():
    session.clear() 
    flash('Bạn đã đăng xuất thành công.', 'info')
    return redirect(url_for('index'))

#TÍNH NĂNG THÊM TỪ MỚI 
@app.route('/add', methods=['GET', 'POST'])
def add_word():
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để sử dụng tính năng thêm từ!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        english_word = request.form.get('english_word').strip()
        phonetics = request.form.get('phonetics').strip()
        word_type = request.form.get('word_type').strip()
        vietnamese_meaning = request.form.get('vietnamese_meaning').strip()
        example_sentence = request.form.get('example_sentence').strip()

        if not english_word or not vietnamese_meaning:
            flash('Vui lòng nhập đầy đủ Từ tiếng Anh và Nghĩa tiếng Việt!', 'danger')
            return redirect(url_for('add_word'))

        word_exists = Word.query.filter_by(english_word=english_word).first()
        if word_exists:
            flash(f"Từ '{english_word}' đã có sẵn trong từ điển rồi!", 'warning')
            return redirect(url_for('add_word'))

        try:
            new_word = Word(
                english_word=english_word,
                phonetics=phonetics,
                word_type=word_type,
                vietnamese_meaning=vietnamese_meaning,
                example_sentence=example_sentence,
                added_by=session['user_id']
            )
            db.session.add(new_word)
            db.session.commit()

            flash(f"Thêm từ '{english_word}' vào từ điển thành công!", 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Đã xảy ra lỗi khi thêm từ: {e}", 'danger')

    return render_template('add_word.html')
#SỬA TỪ VỰNG
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_word(id):

    # Chỉ admin mới được sửa
    if session.get('username') != 'admin':
        flash('Bạn không có quyền sửa từ vựng!', 'danger')
        return redirect(url_for('index'))

    word = Word.query.get_or_404(id)

    if request.method == 'POST':
        word.english_word = request.form['english_word']
        word.phonetics = request.form['phonetics']
        word.word_type = request.form['word_type']
        word.vietnamese_meaning = request.form['vietnamese_meaning']
        word.example_sentence = request.form['example_sentence']

        db.session.commit()
        flash('Cập nhật từ vựng thành công!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_word.html', word=word)

# XÓA TỪ VỰNG
@app.route('/delete/<int:id>')
def delete_word(id):

    # Chỉ admin mới được xóa
    if session.get('username') != 'admin':
        flash('Bạn không có quyền xóa từ vựng!', 'danger')
        return redirect(url_for('index'))

    word = Word.query.get_or_404(id)

    db.session.delete(word)
    db.session.commit()

    flash('Đã xóa từ vựng!', 'success')
    return redirect(url_for('index'))
# Khởi chạy hệ thống
if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # Tự động tạo bảng nếu chưa có
        seed_data()       # Tự động nạp dữ liệu từ file CSV
    app.run(debug=True)
