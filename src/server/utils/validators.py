import subprocess
import os
import re

def is_ffmpeg_installed():
    """Check if FFmpeg is installed on the system"""
    try:
        with subprocess.Popen(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            proc.communicate()
            return proc.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False

def is_valid_url(url):
    """Check if a URL is valid"""
    if not url:
        return False
    
    # Basic URL validation pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ipv4
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
    return bool(url_pattern.match(url))

def is_netscape_cookie_file(file_path):
    """Check if a file is a valid Netscape cookie file"""
    if not os.path.isfile(file_path):
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first few lines
            header_lines = [next(f, '').strip() for _ in range(5)]
            
            # Check for Netscape cookie file header
            if any('# Netscape HTTP Cookie File' in line for line in header_lines):
                return True
                
            # Check cookie format (domain, flag, path, secure, expiration, name, value)
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        return True
    except Exception:
        return False
        
    return False