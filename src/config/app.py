import os

class Config:
    # Xác định thư mục gốc của dự án
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Tạo đường dẫn tuyệt đối đến thư mục instance
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    
    # Tạo thư mục instance nếu nó chưa tồn tại
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    # Cấu hình database với đường dẫn tuyệt đối
    SQLALCHEMY_DATABASE_URI = 'sqlite:///D:/project/video-downloader/instance/users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application configuration
    SECRET_KEY = 'your-secret-key-change-in-production'
    
    # File paths
    DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
    CACHE_FOLDER = os.path.join(BASE_DIR, 'cache')
    COOKIE_FILE = os.path.join(BASE_DIR, 'src', 'public', 'cookies.txt')
    
    # Cache settings
    CACHE_EXPIRY = 7 * 24 * 60 * 60  # 7 days in seconds
    
    # Tạo các thư mục cần thiết khác
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    
    # Debug settings
    DEBUG = True