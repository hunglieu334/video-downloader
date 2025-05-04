import os
import secrets

class Config:
    # Base configuration
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    
    # Create instance directory if it doesn't exist
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    
    # Database configuration
    DB_NAME = 'app.db'
    DB_PATH = os.path.join(INSTANCE_PATH, DB_NAME)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SECRET_KEY = secrets.token_hex(32)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = secrets.token_hex(32)
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(INSTANCE_PATH, 'sessions')
    SESSION_COOKIE_NAME = 'video_downloader_session'
    SESSION_COOKIE_SECURE = False  # Set to True in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'