import os
import yt_dlp
from src.config.constants import PLATFORM_DOMAINS
from src.server.utils.fileManager import get_cache_path
from src.server.services.youtube import get_youtube_info, get_youtube_download_options
from src.server.services.facebook import get_facebook_info, get_facebook_download_options
from src.server.services.tiktok import get_tiktok_info, get_tiktok_download_options

def detect_platform(url):
    """Detect which platform a URL belongs to"""
    url = url.lower()
    
    for platform, domains in PLATFORM_DOMAINS.items():
        if any(domain in url for domain in domains):
            return platform
            
    return "unknown"

def get_video_info(video_url, platform=None, cookie_file=None):
    """Get information about a video without downloading it"""
    if not platform or platform == 'auto':
        platform = detect_platform(video_url)
    
    if platform == 'youtube':
        return get_youtube_info(video_url, cookie_file)
    elif platform == 'facebook':
        return get_facebook_info(video_url, cookie_file)
    elif platform == 'tiktok':
        return get_tiktok_info(video_url, cookie_file)
    else:
        # Try youtube as fallback for unknown platforms
        try:
            return get_youtube_info(video_url, cookie_file)
        except:
            raise ValueError(f"Unsupported platform or URL: {video_url}")

def download_video(video_url, platform=None, quality='best', cookie_file=None):
    """Download a video with the specified quality"""
    if not platform or platform == 'auto':
        platform = detect_platform(video_url)
    
    # Get platform-specific download options
    if platform == 'youtube':
        ydl_opts = get_youtube_download_options(quality, cookie_file)
    elif platform == 'facebook':
        ydl_opts = get_facebook_download_options(quality, cookie_file)
    elif platform == 'tiktok':
        ydl_opts = get_tiktok_download_options(quality, cookie_file)
    else:
        # Use YouTube options as fallback
        ydl_opts = get_youtube_download_options(quality, cookie_file)
    
    # Set cache path as output
    cache_path = get_cache_path(video_url, quality)
    ydl_opts['outtmpl'] = cache_path
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
            # If the file doesn't exist, yt-dlp might have chosen a different extension
            if not os.path.exists(filename):
                base_path = os.path.splitext(filename)[0]
                for ext in ['.mp4', '.webm', '.mkv', '.mov']:
                    if os.path.exists(base_path + ext):
                        filename = base_path + ext
                        break
                        
            return filename
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "This video is unavailable" in error_msg:
            raise ValueError("This video is unavailable or private")
        elif "Sign in" in error_msg or "log in" in error_msg.lower():
            raise ValueError("This video requires login. Please provide a valid cookies.txt file")
        else:
            raise ValueError(f"Download error: {error_msg}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")