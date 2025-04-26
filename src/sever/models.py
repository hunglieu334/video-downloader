from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=None, nullable=True)
    
    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Download history model (optional enhancement)
class DownloadHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    platform = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(20), nullable=False)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('downloads', lazy=True))

def init_db():
    """Initialize the database"""
    db.create_all()