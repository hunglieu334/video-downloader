import subprocess
import os
import re
from urllib.parse import urlparse

def is_ffmpeg_installed():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        return True
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False

def is_netscape_cookie_file(file_path):
    """Check if file is in Netscape cookie format"""
    if not os.path.isfile(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Try to read the first few lines
            first_lines = []
            for _ in range(5):
                try:
                    line = next(file)
                    first_lines.append(line)
                except StopIteration:
                    break
                    
            # Check if header comment exists
            if any("# Netscape HTTP Cookie File" in line for line in first_lines):
                return True
                
            # If no header but has correct format
            for line in first_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Check cookie format: domain, flag, path, secure, expiry, name, value
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        return True
        
        return False
    except Exception:
        return False

def is_valid_url(url):
    """Check if URL is valid"""
    if not url:
        return False
        
    # Basic URL validation
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def validate_email(email):
    """Validate email format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_username(username):
    """Validate username"""
    if not username:
        return False
    return len(username) >= 3 and len(username) <= 30

def validate_password(password):
    """Validate password strength"""
    if not password:
        return False
    return len(password) >= 6