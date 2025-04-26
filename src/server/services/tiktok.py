import yt_dlp
import os
import re
from src.config.constants import DEFAULT_USER_AGENT
from src.server.utils.validators import is_ffmpeg_installed
from src.server.utils.fileManager import get_cache_path

def get_tiktok_info(video_url, cookie_file=None):
    """Get information about a TikTok video with improved error handling"""
    if not validate_tiktok_url(video_url):
        raise ValueError("Invalid TikTok URL")

    # TikTok-specific options
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'noplaylist': True,
        'user_agent': DEFAULT_USER_AGENT,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            result = {
                'thumbnail': info.get('thumbnail'),
                'title': info.get('title', 'TikTok Video'),
                'embed_url': clean_tiktok_url(video_url),
                'original_url': video_url,
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'ffmpeg_installed': is_ffmpeg_installed(),
                'platform': 'tiktok'
            }
            
            # TikTok typically has limited format options
            qualities = [{'value': 'best', 'label': 'Tốt nhất (HD)'}]
            
            # Add no-watermark option if available
            result['qualities'] = qualities
            result['has_no_watermark'] = True
            
            return result
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "This video is private" in error_msg:
            raise ValueError("Video TikTok này là riêng tư")
        elif "Video currently unavailable" in error_msg:
            raise ValueError("Video TikTok này không khả dụng")
        else:
            raise ValueError(f"Lỗi TikTok: {error_msg}")
    except Exception as e:
        raise ValueError(f"Lỗi xảy ra: {str(e)}")

def download_tiktok_video(video_url, quality='best', cookie_file=None):
    """Download a TikTok video with specified quality"""
    if not validate_tiktok_url(video_url):
        raise ValueError("Invalid TikTok URL")
        
    # Get download options
    ydl_opts = get_tiktok_download_options(quality, cookie_file)
    
    # Set output path
    cache_path = get_cache_path(video_url, quality)
    ydl_opts['outtmpl'] = cache_path
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        raise ValueError(f"Không thể tải video: {str(e)}")

def get_tiktok_download_options(quality, cookie_file=None):
    """Generate optimized yt-dlp options for TikTok videos"""
    ffmpeg_available = is_ffmpeg_installed()
    
    # TikTok videos don't need quality selection as they usually have only one stream
    selected_format = 'best'
    
    # TikTok-specific options
    opts = {
        'format': selected_format,
        'noplaylist': True,
        'user_agent': DEFAULT_USER_AGENT,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
    }
    
    # Add optimizations if FFmpeg is available
    if ffmpeg_available:
        opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    
    return opts

def clean_tiktok_url(url):
    """Clean TikTok URL for embedding"""
    # Extract video ID for embedding
    video_id_match = re.search(r'\/video\/(\d+)', url)
    if video_id_match:
        video_id = video_id_match.group(1)
        return f"https://www.tiktok.com/embed/v2/{video_id}"
    return url

def validate_tiktok_url(url):
    """Validate if URL is a TikTok video URL"""
    if not url:
        return False
        
    # TikTok domains
    tiktok_domains = ['tiktok.com', 'www.tiktok.com', 'm.tiktok.com', 'vm.tiktok.com']
    domain_match = any(domain in url.lower() for domain in tiktok_domains)
    
    # TikTok video URL patterns
    patterns = [
        r'tiktok\.com\/@[^\/]+\/video\/\d+',
        r'vm\.tiktok\.com\/\w+',
    ]
    
    pattern_match = any(re.search(pattern, url.lower()) for pattern in patterns)
    
    return domain_match and pattern_match