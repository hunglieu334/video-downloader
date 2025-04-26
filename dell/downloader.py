import os
import yt_dlp
from flask import current_app as app
from app.utils import is_netscape_cookie_file

def get_ydl_opts(platform, quality, cookie_file=None):
    """Generate yt-dlp options based on platform and quality"""
    config = app.config
    selected_format = config['QUALITY_MAP'].get(quality, 'bestvideo+bestaudio/best')
    
    opts = {
        'outtmpl': f'{config["DOWNLOAD_FOLDER"]}/%(title)s.%(ext)s',
        'format': selected_format,
        'noplaylist': True,
        'quiet': False,
        'user-agent': config['DEFAULT_USER_AGENT'],
        'cookiefile': cookie_file if cookie_file and is_netscape_cookie_file(cookie_file) else None,
    }

    # Platform specific optimizations
    if platform == 'tiktok':
        opts['format'] = selected_format.replace('+bestaudio', '')
    
    return opts

def extract_video_info(video_url, platform, cookie_file=None):
    """Extract video information without downloading"""
    if not video_url:
        return {'error': 'URL is required'}, 400
        
    if os.path.exists(cookie_file) and not is_netscape_cookie_file(cookie_file):
        return {'error': 'Cookie file is invalid'}, 400
        
    try:
        # Basic configuration for quick info extraction
        ydl_opts = {
            'quiet': True,
            'user-agent': app.config['DEFAULT_USER_AGENT'],
            'cookiefile': cookie_file if cookie_file and is_netscape_cookie_file(cookie_file) else None,
            'format_sort': ['res'],
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            result = {
                'thumbnail': info.get('thumbnail'),
                'title': info.get('title'),
                'embed_url': None,
                'original_url': video_url
            }
            
            # Platform-specific embed URL handling
            if platform == 'tiktok':
                result['embed_url'] = video_url.replace('www.tiktok.com', 'www.tiktok.com/embed')
            elif platform == 'facebook':
                result['embed_url'] = f"https://www.facebook.com/plugins/video.php?href={video_url}"
                
        # Get available qualities
        ydl_opts_full = {
            'quiet': True,
            'user-agent': app.config['DEFAULT_USER_AGENT'],
            'cookiefile': cookie_file if cookie_file and is_netscape_cookie_file(cookie_file) else None,
            'listformats': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
            info_full = ydl.extract_info(video_url, download=False)
            formats = info_full.get('formats', [])
            qualities = []
            available_heights = set()
            
            for fmt in formats:
                height = fmt.get('height')
                if height and height not in available_heights:
                    available_heights.add(height)
                    if height in [2160, 1080, 720, 480, 360]:
                        qualities.append({
                            'value': str(height),
                            'label': f"{height}p"
                        })
                        
            if formats:
                qualities.insert(0, {'value': 'best', 'label': 'Tốt nhất (cao nhất có sẵn)'})
                qualities.sort(key=lambda x: int(x['value']) if x['value'] != 'best' else float('inf'), reverse=True)
                
            result['qualities'] = qualities
            
        return result, 200
    except Exception as e:
        return {'error': f'Error extracting video info: {str(e)}'}, 500

def download_video(video_url, platform, quality, cookie_file=None):
    """Download video and return file path"""
    try:
        ydl_opts = get_ydl_opts(platform, quality, cookie_file)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info), None
    except Exception as e:
        return None, f"Download error: {str(e)}"