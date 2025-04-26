import yt_dlp
import os
import re
import hashlib
from src.config.constants import QUALITY_MAP, DEFAULT_USER_AGENT
from src.server.utils.validators import is_ffmpeg_installed
from src.server.utils.fileManager import get_cache_path

DEBUG = os.environ.get('YOUTUBE_DEBUG', '0') == '1'

# Các format ID quan trọng của YouTube
YOUTUBE_FORMAT_IDS = {
    '720p_mp4': '22',     # 720p MP4 (video+audio)
    '480p_mp4': '18',     # 480p MP4 (video+audio)
    '360p_mp4': '134',    # 360p MP4 (chỉ video)
    'audio': '140',       # M4A audio
}

def get_youtube_info(video_url, cookie_file=None):
    """Get information about a YouTube video"""
    if not validate_youtube_url(video_url):
        raise ValueError("Invalid YouTube URL")
    
    # Kiểm tra nếu là YouTube Shorts
    is_shorts = is_youtube_shorts(video_url)
    
    # Basic options for fetching info
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'user_agent': DEFAULT_USER_AGENT,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
    }
    
    # Thêm tùy chọn đặc biệt cho shorts để cố gắng lấy chất lượng cao nhất
    if is_shorts:
        ydl_opts.update({
            'prefer_insecure': True,
            'geo_bypass': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            }
        })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Tạo YouTube embed URL
            video_id = info.get('id')
            if is_shorts:
                embed_url = f"https://www.youtube.com/shorts/{video_id}"
            else:
                embed_url = f"https://www.youtube.com/embed/{video_id}" if video_id else None
            
            # Extract available formats
            formats = info.get('formats', [])
            
            # Lọc các format hữu ích và sắp xếp theo chất lượng
            video_formats = []
            for fmt in formats:
                # Bỏ qua các format không có video hoặc chỉ là audio
                if fmt.get('vcodec') == 'none' or fmt.get('acodec') == 'none':
                    continue
                    
                # Thu thập thông tin format
                format_info = {
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'height': fmt.get('height'),
                    'width': fmt.get('width'),
                    'fps': fmt.get('fps'),
                    'tbr': fmt.get('tbr', 0),  # Tổng bitrate
                    'filesize': fmt.get('filesize'),
                    'format_note': fmt.get('format_note', ''),
                    'vcodec': fmt.get('vcodec'),
                    'acodec': fmt.get('acodec')
                }
                
                if format_info['height'] and format_info['width']:
                    video_formats.append(format_info)
            
            # Sắp xếp theo độ phân giải và bitrate
            video_formats = sorted(
                video_formats, 
                key=lambda x: (x.get('height', 0), x.get('tbr', 0)), 
                reverse=True
            )
            
            # Nhóm các format theo độ phân giải
            resolution_groups = {}
            for fmt in video_formats:
                height = fmt.get('height')
                if height:
                    if height not in resolution_groups:
                        resolution_groups[height] = []
                    resolution_groups[height].append(fmt)
            
            # Chỉ lấy format tốt nhất cho mỗi độ phân giải (bitrate cao nhất)
            best_formats = {}
            for height, formats_group in resolution_groups.items():
                best_formats[height] = max(formats_group, key=lambda x: x.get('tbr', 0))
            
            # Generate quality options
            qualities = []
            
            # Nhóm các độ phân giải tiêu chuẩn để hiển thị
            standard_resolutions = [2160, 1440, 1080, 720, 480, 360]
            
            # Thêm tùy chọn chất lượng cao nhất và định dạng gốc
            qualities.append({'value': 'best', 'label': 'Tốt nhất (cao nhất có sẵn)'})
            qualities.append({'value': 'original', 'label': 'Định dạng gốc (không chuyển đổi)'})
            
            # Thêm phân loại theo độ phân giải
            for height in sorted(best_formats.keys(), reverse=True):
                fmt = best_formats[height]
                bitrate = fmt.get('tbr', 0)
                extension = fmt.get('ext', 'mp4')
                fps = fmt.get('fps', '')
                fps_str = f"{fps}fps " if fps else ""
                
                bitrate_str = f" ({int(bitrate)}kbps)" if bitrate else ""
                
                # Thêm chi tiết định dạng cho các độ phân giải phổ biến
                if height in standard_resolutions:
                    label = f"{height}p {fps_str}[{extension}]{bitrate_str}"
                    qualities.append({
                        'value': str(height),
                        'label': label,
                        'format_id': fmt.get('format_id')
                    })
            
            # Thêm tùy chọn chỉ tải audio
            qualities.append({'value': 'audio', 'label': 'Chỉ âm thanh (MP3)'})
            
            # Thu thập thêm thông tin video
            result = {
                'thumbnail': info.get('thumbnail'),
                'title': info.get('title', 'YouTube Video'),
                'embed_url': embed_url,
                'original_url': video_url,
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count'),
                'upload_date': info.get('upload_date'),
                'qualities': qualities,
                'ffmpeg_installed': is_ffmpeg_installed(),
                'format_detail': best_formats,  # Lưu chi tiết format để sử dụng sau
                'is_shorts': is_shorts,
                'available_resolutions': sorted(list(best_formats.keys()), reverse=True)
            }
            
            return result
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'private video' in error_msg:
            raise ValueError("Video này đã được đặt ở chế độ riêng tư")
        elif 'copyright' in error_msg:
            raise ValueError("Video không khả dụng do vấn đề bản quyền")
        else:
            raise ValueError(f"Không thể xử lý video YouTube: {e}")

def download_youtube_video(video_url, quality='best', cookie_file=None, format_id=None):
    """Download a YouTube video with specified quality"""
    if not validate_youtube_url(video_url):
        raise ValueError("Invalid YouTube URL")
    
    # Kiểm tra FFmpeg
    ffmpeg_available = is_ffmpeg_installed()
    
    # Kiểm tra nếu là YouTube Shorts
    is_shorts = is_youtube_shorts(video_url)
    
    # Nếu là shorts và người dùng chọn chất lượng cao nhất hoặc 720p
    if is_shorts and (quality == 'best' or quality == '720'):
        # Format đặc biệt cho shorts để ưu tiên 720p
        selected_format = '22/18/136+140/bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    elif format_id:
        # Nếu có format_id cụ thể
        selected_format = format_id + "+bestaudio/best"
    elif quality == 'best':
        selected_format = 'bestvideo+bestaudio/best'
    elif quality == 'original':
        # Chọn định dạng tốt nhất nhưng giữ nguyên định dạng gốc
        selected_format = 'bestvideo+bestaudio/best'
    elif quality == 'audio':
        selected_format = 'bestaudio/best'
    elif quality.isdigit():
        height = int(quality)
        # Nếu là 720p, thêm format 22 (YouTube 720p MP4) vào đầu danh sách
        if height == 720:
            selected_format = '22/18/bestvideo[height<=720]+bestaudio/best[height<=720]/best'
        else:
            selected_format = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
    else:
        selected_format = 'bestvideo+bestaudio/best'
    
    # Thiết lập đường dẫn cache
    cache_path = get_cache_path(video_url, quality if not format_id else f"{quality}_{format_id}")
    
    # Tùy chọn nâng cao cho YouTube
    ydl_opts = {
        'format': selected_format,
        'outtmpl': cache_path if quality != 'original' else os.path.splitext(cache_path)[0] + '.%(ext)s',
        'noplaylist': True,
        'user_agent': DEFAULT_USER_AGENT,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
        'quiet': not DEBUG,
        # Thêm các tùy chọn để cố gắng lấy chất lượng cao cho shorts
        'prefer_insecure': True,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],  # Sử dụng cả client Android và web để tối đa hoá khả năng lấy chất lượng cao
            }
        }
    }
    
    # Thêm xử lý hậu kỳ nếu có FFmpeg và không phải là định dạng gốc
    if ffmpeg_available:
        if quality == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality != 'original':  # Không chuyển đổi nếu là định dạng gốc
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            ydl_opts['merge_output_format'] = 'mp4'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if DEBUG:
                print(f"Downloading with format: {selected_format}")
            info = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        error_msg = str(e)
        if "ffmpeg is not installed" in error_msg:
            raise ValueError("FFmpeg chưa được cài đặt. Để tải xuống video chất lượng cao, vui lòng cài đặt FFmpeg.")
        raise ValueError(f"Không thể tải xuống video: {error_msg}")

def get_youtube_download_options(quality, cookie_file=None):
    """Generate optimized yt-dlp options for YouTube videos"""
    ffmpeg_available = is_ffmpeg_installed()
    
    # YouTube-specific format selection
    if quality == 'best':
        selected_format = 'bestvideo+bestaudio/best'
    elif quality == 'original':
        # Chọn định dạng tốt nhất nhưng giữ nguyên định dạng gốc
        selected_format = 'bestvideo+bestaudio/best'
    elif quality.isdigit():
        height = int(quality)
        if ffmpeg_available:
            selected_format = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
        else:
            selected_format = f'best[height<={height}]/best'
    else:
        selected_format = QUALITY_MAP.get(quality, 'bestvideo+bestaudio/best')
    
    # YouTube-specific options
    opts = {
        'format': selected_format,
        'noplaylist': True,
        'user_agent': DEFAULT_USER_AGENT,
        'cookiefile': cookie_file if cookie_file and os.path.exists(cookie_file) else None,
    }
    
    # Add optimizations if FFmpeg is available and quality is NOT original
    if ffmpeg_available and quality != 'audio' and quality != 'original':
        opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
        opts['merge_output_format'] = 'mp4'
    
    return opts

def extract_youtube_id(url):
    """Extract YouTube video ID from a URL"""
    if not url:
        return None
        
    # Handle youtu.be URLs
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]
        
    # Handle youtube.com URLs
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if match:
        return match.group(1)
    
    return None

def validate_youtube_url(url):
    """Validate if URL is a YouTube video URL"""
    if not url:
        return False
        
    # YouTube domains
    yt_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
    
    # Check domain
    domain_match = any(domain in url.lower() for domain in yt_domains)
    
    # Check for video ID pattern
    has_video_id = bool(extract_youtube_id(url))
    
    return domain_match and has_video_id

def get_cache_path(url, quality, is_shorts=False):
    """Generate a unique cache path for a video URL and quality"""
    # Thêm thông tin shorts vào hash để phân biệt
    url_hash = hashlib.md5(f"{url}_{quality}_shorts_{is_shorts}".encode()).hexdigest()
    
    # Phần còn lại của hàm...
    # Nếu là định dạng original, trả về không có phần mở rộng cụ thể
    if quality == 'original':
        return os.path.join(Config.CACHE_FOLDER, f"{url_hash}")
    # Đối với audio, sử dụng .mp3
    elif quality == 'audio':
        return os.path.join(Config.CACHE_FOLDER, f"{url_hash}.mp3")
    # Còn lại sử dụng .mp4
    else:
        return os.path.join(Config.CACHE_FOLDER, f"{url_hash}.mp4")

def get_best_shorts_format(formats):
    """Tìm format tốt nhất cho YouTube Shorts"""
    best_format = None
    best_height = 0
    
    # Ưu tiên format 22 (720p MP4)
    for fmt in formats:
        if fmt.get('format_id') == '22':
            return fmt
    
    # Tìm format có chiều cao cao nhất
    for fmt in formats:
        height = fmt.get('height', 0)
        if height > best_height and fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
            best_height = height
            best_format = fmt
    
    # Nếu không tìm thấy format tích hợp, tìm video tốt nhất
    if not best_format:
        best_video = None
        best_video_height = 0
        
        for fmt in formats:
            height = fmt.get('height', 0)
            if height > best_video_height and fmt.get('vcodec') != 'none':
                best_video_height = height
                best_video = fmt
        
        if best_video:
            return best_video
    
    return best_format