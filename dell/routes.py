from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, send_file, after_this_request
from flask_login import login_user, logout_user, login_required, current_user
import os

from app.models import User
from app import db
from app.downloader import extract_video_info, download_video
from app.utils import is_netscape_cookie_file, clean_cookie_file
from app.config import Config

# Define blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__, url_prefix='/auth')

# Main routes
@main.route('/')
def index():
    return render_template('index.html', user=current_user)

@main.route('/preview', methods=['POST'])
@login_required
def preview_video():
    platform = request.form.get('platform', 'youtube')
    video_url = request.form['url']
    
    if not video_url:
        return jsonify({'error': 'URL is required'}), 400
        
    result, status_code = extract_video_info(
        video_url, 
        platform, 
        Config.COOKIE_FILE if os.path.exists(Config.COOKIE_FILE) else None
    )
    
    return jsonify(result), status_code

@main.route('/download', methods=['POST'])
@login_required
def download_video_route():
    video_url = request.form['url']
    platform = request.form.get('platform', 'youtube')
    quality = request.form.get('quality', 'best')

    if not video_url:
        flash("Please provide a URL", "error")
        return redirect(url_for('main.index'))

    if os.path.exists(Config.COOKIE_FILE) and not is_netscape_cookie_file(Config.COOKIE_FILE):
        flash("The cookies.txt file is not in Netscape format. Please recreate it.", "error")
        return redirect(url_for('main.index'))

    file_path, error = download_video(
        video_url, 
        platform, 
        quality, 
        Config.COOKIE_FILE if os.path.exists(Config.COOKIE_FILE) else None
    )
    
    if error:
        flash(error, "error")
        return redirect(url_for('main.index'))
        
    @after_this_request
    def remove_file(response):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # Log the error but continue
            pass
        return response
        
    return send_file(file_path, as_attachment=True)

@main.route('/optimize-cookies', methods=['POST'])
@login_required
def optimize_cookies():
    if not os.path.exists(Config.COOKIE_FILE):
        flash("Cookie file not found", "error")
        return redirect(url_for('main.index'))
        
    if clean_cookie_file(Config.COOKIE_FILE):
        flash("Cookie file optimized successfully", "success")
    else:
        flash("Failed to optimize cookie file", "error")
        
    return redirect(url_for('main.index'))

# Authentication routes
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Basic validation
        if not username or not password:
            flash("All fields are required", "error")
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
            
        # Create new user
        hashed_password = User.hash_password(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))
            
        flash('Invalid username or password', 'error')
        
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))