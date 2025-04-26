import yt_dlp
import os
from src.config.constants import PLATFORMS, DEFAULT_USER_AGENT
from src.server.utils.validators import is_ffmpeg_installed
from src.server.utils.fileManager import get_cache_path

def detect_platform(url):
    """Detect which platform a URL belongs to"""
    url_lower = url.lower()
    
    for platform, data in PLATFORMS.items():
        if any(domain in url_lower for domain in data.get('domains', [])):
            return platform
    
    # Default to youtube for unknown URLs
    return 'youtube'

def get_video_info(video_url, platform='auto', cookie_file=None):
    """Get information about a video without downloading it"""
    if platform == 'auto':
        platform = detect_platform(video_url)
    
    # Basic options for all platforms
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
            
            # Create embed URL based on platform
            embed_url = None
            if platform == 'youtube':
                if '/shorts/' in video_url:
                    video_id = video_url.split('/shorts/')[1].split('?')[0]
                    embed_url = f"https://www.youtube.com/embed/{video_id}"
                else:
                    video_id = video_url.split('v=')[1].split('&')[0] if 'v=' in video_url else None
                    if video_id:
                        embed_url = f"https://www.youtube.com/embed/{video_id}"
            elif platform == 'facebook':
                embed_url = f"https://www.facebook.com/plugins/video.php?href={video_url}"
            elif platform == 'tiktok':
                embed_url = video_url.replace('www.tiktok.com', 'www.tiktok.com/embed')
            
            # Extract formats for quality options
            formats = info.get('formats', [])
            best_formats = {}
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
            standard_resolutions = [2160, 1080, 720, 480, 360]
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
                
                # Add audio-only option for YouTube
                if platform == 'youtube':
                    qualities.append({'value': 'audio', 'label': 'Chỉ audio (MP3)'})
            
            result = {
                'thumbnail': info.get('thumbnail'),
                'title': info.get('title', f'{platform.capitalize()} Video'),
                'embed_url': embed_url,
                'original_url': video_url,
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'qualities': qualities,
                'ffmpeg_installed': is_ffmpeg_installed(),
                'platform': platform
            }
            
            return result
    except Exception as e:
        raise ValueError(f"Không thể lấy thông tin video: {str(e)}")

def download_video(video_url, platform='auto', quality='best', cookie_file=None):
    """Download a video with specified quality"""
    if platform == 'auto':
        platform = detect_platform(video_url)
    
    # Check if FFmpeg is installed
    ffmpeg_available = is_ffmpeg_installed()
    
    # Format selection based on quality and FFmpeg availability
    if quality == 'best':
        if ffmpeg_available:
            selected_format = 'bestvideo+bestaudio/best'
        else:
            # If FFmpeg not available, only download single format
            selected_format = 'best[ext=mp4]/best'
    elif quality == 'audio':
        if ffmpeg_available:
            selected_format = 'bestaudio/best'
        else:
            selected_format = 'worstaudio/worst'
    elif quality.isdigit():
        height = int(quality)
        if ffmpeg_available:
            selected_format = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
        else:
            selected_format = f'best[height<={height},ext=mp4]/best[height<={height}]/best'
    else:
        if ffmpeg_available:
            selected_format = 'bestvideo+bestaudio/best'
        else:
            selected_format = 'best[ext=mp4]/best'
    
    # Set options
    cache_path = get_cache_path(video_url, quality)
    
    ydl_opts = {
        'format': selected_format,
        'outtmpl': cache_path,
        'noplaylist': True,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
        'user_agent': DEFAULT_USER_AGENT,
        # Không cho phép lỗi ffmpeg dừng quá trình
        'ignoreerrors': True,
        # Thêm tùy chọn này để tránh yêu cầu ffmpeg khi không có sẵn
        'postprocessors': []
    }
    
    # Add audio conversion for audio-only - CHỈ KHI có FFmpeg
    if quality == 'audio' and ffmpeg_available:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    # Add optimizations if FFmpeg is available
    elif ffmpeg_available:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
        ydl_opts['merge_output_format'] = 'mp4'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        error_msg = str(e)
        if "ffmpeg is not installed" in error_msg:
            raise ValueError("Không thể tải xuống video: FFmpeg chưa được cài đặt. Vui lòng cài đặt FFmpeg hoặc chọn chất lượng có sẵn định dạng mp4.")
        raise ValueError(f"Không thể tải xuống video: {error_msg}")