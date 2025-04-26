import os
import time
import hashlib
import shutil
from src.config.app import Config

def get_cache_path(url, quality):
    """Create a cache path based on URL and quality"""
    # Create a unique hash from the URL and quality
    url_hash = hashlib.md5((url + quality).encode()).hexdigest()
    
    # Create the cache directory if it doesn't exist
    os.makedirs(Config.CACHE_FOLDER, exist_ok=True)
    
    return os.path.join(Config.CACHE_FOLDER, f"{url_hash}.%(ext)s")

def clean_expired_cache():
    """Delete expired cache files and manage cache size"""
    try:
        now = time.time()
        deleted_count = 0
        deleted_bytes = 0
        total_size = 0
        
        # Skip if cache directory doesn't exist
        if not os.path.exists(Config.CACHE_FOLDER):
            return
        
        # Get all cache files with their size and modification time
        cache_files = []
        for filename in os.listdir(Config.CACHE_FOLDER):
            file_path = os.path.join(Config.CACHE_FOLDER, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                cache_files.append((file_path, file_size, file_mtime))
                total_size += file_size
        
        # First delete expired files
        for file_path, file_size, file_mtime in cache_files:
            if now - file_mtime > Config.CACHE_EXPIRY:
                os.remove(file_path)
                deleted_count += 1
                deleted_bytes += file_size
                
        # Then check if we still need to clean up based on total size
        if total_size - deleted_bytes > Config.MAX_CACHE_SIZE:
            # Sort remaining files by modification time (oldest first)
            remaining_files = [(p, s, m) for p, s, m in cache_files 
                              if os.path.exists(p)]
            remaining_files.sort(key=lambda x: x[2])  # Sort by mtime
            
            # Delete oldest files until we're under the size limit
            for file_path, file_size, _ in remaining_files:
                if total_size - deleted_bytes <= Config.MAX_CACHE_SIZE:
                    break
                    
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    deleted_bytes += file_size
        
        return deleted_count, deleted_bytes
        
    except Exception as e:
        print(f"Error cleaning cache: {e}")
        return 0, 0

def ensure_directory_exists(directory):
    """Ensure that a directory exists, creating it if necessary"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return directory