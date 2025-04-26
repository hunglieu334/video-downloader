import os

def is_netscape_cookie_file(file_path):
    """Check if the cookie file follows Netscape format"""
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            # Either the file starts with the Netscape header comment or has valid cookie lines
            if first_line.startswith('# Netscape HTTP Cookie File'):
                return True
            # If not, read a few more lines to check for valid cookie format
            lines = [first_line] + [f.readline().strip() for _ in range(5)]
            # Check if any non-comment line has typical cookie format (contains at least 6 tabs)
            return any(not line.startswith('#') and line.count('\t') >= 6 for line in lines if line)
    except Exception:
        return False

def clean_cookie_file(file_path):
    """Remove unnecessary cookies to optimize file size"""
    if not os.path.exists(file_path):
        return False
        
    # List of common video domains we want to keep cookies for
    important_domains = [
        'youtube.com', 
        'tiktok.com', 
        'facebook.com', 
        'vimeo.com',
        'dailymotion.com',
        'twitch.tv'
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Keep header and cookies for important domains
        header = [line for line in lines if line.startswith('#')]
        cookies = [line for line in lines if any(domain in line for domain in important_domains) 
                   and not line.startswith('#')]
        
        with open(file_path + '.optimized', 'w', encoding='utf-8') as f:
            f.writelines(header + cookies)
            
        # Replace original with optimized version if successful
        os.replace(file_path + '.optimized', file_path)
        return True
    except Exception:
        return False