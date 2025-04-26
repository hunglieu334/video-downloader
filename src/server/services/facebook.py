import yt_dlp
import os
import re
from src.config.constants import QUALITY_MAP, DEFAULT_USER_AGENT
from src.server.utils.validators import is_ffmpeg_installed
from src.server.utils.fileManager import get_cache_path

def get_facebook_info(video_url, cookie_file=None):
    """Get information about a Facebook video with improved error handling"""
    if not validate_facebook_url(video_url):
        raise ValueError("Invalid Facebook video URL")

    # Facebook-specific options
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'format_sort': ['res', 'ext:mp4:m4a'],
        'user_agent': DEFAULT_USER_AGENT,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            result = {
                'thumbnail': info.get('thumbnail'),
                'title': info.get('title', 'Facebook Video'),
                'embed_url': f"https://www.facebook.com/plugins/video.php?href={video_url}",
                'original_url': video_url,
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'ffmpeg_installed': is_ffmpeg_installed(),
                'platform': 'facebook'
            }
            
            # Extract available formats
            formats = info.get('formats', [])
            best_formats = {}
            
            # Find best format for each resolution
            for fmt in formats:
                height = fmt.get('height')
                if height:
                    if height not in best_formats:
                        best_formats[height] = fmt
                    else:
                        current_bitrate = fmt.get('tbr', 0)
                        best_bitrate = best_formats[height].get('tbr', 0)
                        if current_bitrate > best_bitrate:
                            best_formats[height] = fmt
            
            # Generate quality options
            qualities = []
            standard_resolutions = [1080, 720, 480, 360]
            
            for height in sorted(best_formats.keys(), reverse=True):
                if height in standard_resolutions or len(qualities) < 6:
                    bitrate = best_formats[height].get('tbr', 0)
                    bitrate_str = f" ({int(bitrate)}kbps)" if bitrate else ""
                    
                    qualities.append({
                        'value': str(height),
                        'label': f"{height}p{bitrate_str}"
                    })
            
            # Add best quality option
            if formats:
                qualities.insert(0, {'value': 'best', 'label': 'Tốt nhất (cao nhất có sẵn)'})
            
            result['qualities'] = qualities
            return result
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Video unavailable" in error_msg:
            raise ValueError("Video Facebook này là riêng tư hoặc không khả dụng")
        elif "Please log in or create an account" in error_msg:
            raise ValueError("Video này yêu cầu đăng nhập. Vui lòng cung cấp cookies.txt hợp lệ")
        else:
            raise ValueError(f"Lỗi Facebook: {error_msg}")
    except Exception as e:
        raise ValueError(f"Lỗi xảy ra: {str(e)}")

def download_facebook_video(video_url, quality='best', cookie_file=None):
    """Download a Facebook video with specified quality"""
    if not validate_facebook_url(video_url):
        raise ValueError("Invalid Facebook URL")
        
    # Get download options
    ydl_opts = get_facebook_download_options(quality, cookie_file)
    
    # Set output path
    cache_path = get_cache_path(video_url, quality)
    ydl_opts['outtmpl'] = cache_path
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        raise ValueError(f"Không thể tải video: {str(e)}")

def get_facebook_download_options(quality, cookie_file=None):
    """Generate optimized yt-dlp options for Facebook videos"""
    ffmpeg_available = is_ffmpeg_installed()
    
    # Facebook-specific format optimization
    if quality == 'best':
        selected_format = 'bestvideo+bestaudio/best'
    elif quality.isdigit():
        height = int(quality)
        if ffmpeg_available:
            selected_format = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
        else:
            selected_format = f'best[height<={height}]/best'
    else:
        selected_format = QUALITY_MAP.get(quality, 'bestvideo+bestaudio/best')
    
    # Facebook-specific options
    opts = {
        'format': selected_format,
        'noplaylist': True,
        'user_agent': DEFAULT_USER_AGENT,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
        'retries': 5,  # More retries for Facebook
        'fragment_retries': 10,
    }
    
    # Add optimizations if FFmpeg is available
    if ffmpeg_available:
        opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
        opts['merge_output_format'] = 'mp4'
    
    return opts

def validate_facebook_url(url):
    """Improved validation for Facebook video URLs"""
    if not url:
        return False
        
    # Facebook domains
    fb_domains = ['facebook.com', 'fb.com', 'www.facebook.com', 'm.facebook.com', 'fb.watch', 'web.facebook.com']
    has_valid_domain = any(domain in url.lower() for domain in fb_domains)
    
    # Facebook video URL patterns
    patterns = [
        r'facebook\.com\/.*\/videos\/',
        r'facebook\.com\/watch\?v=',
        r'fb\.watch\/',
        r'facebook\.com\/.*\/posts\/.*',
        r'facebook\.com\/reel\/',
    ]
    
    matches_pattern = any(re.search(pattern, url.lower()) for pattern in patterns)
    
    return has_valid_domain and matches_pattern