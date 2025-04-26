from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from src.server.models import User, db
from src.config.constants import PLATFORMS

def register_page_routes(app):
    @app.route('/')
    def index():
        """Home page route"""
        platforms = PLATFORMS
        return render_template('index.html', user=current_user, platforms=platforms)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page route"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                
                # Update last login timestamp
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                flash('Đăng nhập thành công!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('index'))
            
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')
            
        return render_template('login.html', user=current_user)  # Thêm user=current_user
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Registration page route"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')  # Không strip() mật khẩu
            password_confirm = request.form.get('password_confirm', '')  # Đảm bảo tên trường đúng
            
            # In ra để debug (có thể xóa sau khi sửa xong)
            print(f"Password: '{password}'")
            print(f"Confirm: '{password_confirm}'")
            print(f"Match: {password == password_confirm}")
            
            # Validation
            if not username or len(username) < 3:
                flash('Tên đăng nhập phải có ít nhất 3 ký tự!', 'error')
                return render_template('register.html')
                
            if not password or len(password) < 6:
                flash('Mật khẩu phải có ít nhất 6 ký tự!', 'error')
                return render_template('register.html')
                
            if password != password_confirm:
                flash('Mật khẩu xác nhận không khớp!', 'error')
                return render_template('register.html')
                
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash('Tên đăng nhập đã tồn tại!', 'error')
                return render_template('register.html')
                
            # Create new user
            user = User(username=username)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html')