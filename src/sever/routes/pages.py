from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from src.server.models import User, DownloadHistory, db
from src.config.constants import SUPPORTED_PLATFORMS, ERROR_MESSAGES

def register_page_routes(app):
    """Register page routes with the Flask application"""
    
    @app.route('/')
    def index():
        """Render the main page"""
        platforms = SUPPORTED_PLATFORMS
        return render_template(
            'index.html', 
            user=current_user,
            platforms=platforms
        )
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validate input
            if not username or len(username) < 3:
                flash('Username must be at least 3 characters.', 'danger')
                return render_template('register.html')
                
            if not password or len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('register.html')
                
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html')
                
            # Check if username exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'danger')
                return render_template('register.html')
                
            # Create new user
            new_user = User(username=username)
            new_user.set_password(password)
            
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Registration error: {str(e)}")
                flash(ERROR_MESSAGES['registration_failed'], 'danger')
            
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember = 'remember' in request.form
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                user.update_last_login()
                db.session.commit()
                
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
            
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Log out the current user"""
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('index'))
        
    @app.route('/history')
    @login_required
    def history():
        """Show user download history"""
        downloads = DownloadHistory.query.filter_by(
            user_id=current_user.id
        ).order_by(DownloadHistory.downloaded_at.desc()).limit(50).all()
        
        return render_template('history.html', downloads=downloads)