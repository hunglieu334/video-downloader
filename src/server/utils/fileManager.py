import os
import time
import hashlib
import shutil
from src.config.app import Config

def get_cache_path(url, quality):
    """Generate a unique cache path for a video URL and quality"""
    # Create hash of URL + quality to avoid filename issues
    url_hash = hashlib.md5(f"{url}_{quality}".encode()).hexdigest()
    return os.path.join(Config.CACHE_FOLDER, f"{url_hash}.mp4")

def clean_expired_cache():
    """Remove expired files from cache directory"""
    current_time = time.time()
    
    try:
        # If cache folder doesn't exist, create it
        if not os.path.exists(Config.CACHE_FOLDER):
            os.makedirs(Config.CACHE_FOLDER, exist_ok=True)
            return
            
        # Scan all files in cache directory
        for filename in os.listdir(Config.CACHE_FOLDER):
            file_path = os.path.join(Config.CACHE_FOLDER, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Check if file is old enough to be deleted
            file_modified = os.path.getmtime(file_path)
            if current_time - file_modified > Config.CACHE_EXPIRY:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting cache file {file_path}: {e}")
    except Exception as e:
        print(f"Error cleaning cache: {e}")

def get_cache_size():
    """Get the total size of cache directory in bytes"""
    total_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(Config.CACHE_FOLDER):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
    except Exception as e:
        print(f"Error calculating cache size: {e}")
        
    return total_size

def clear_all_cache():
    """Clear all files from cache directory"""
    try:
        if os.path.exists(Config.CACHE_FOLDER):
            for filename in os.listdir(Config.CACHE_FOLDER):
                file_path = os.path.join(Config.CACHE_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    except Exception as e:
        print(f"Error clearing cache: {e}")