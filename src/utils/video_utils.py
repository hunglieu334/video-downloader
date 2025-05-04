import yt_dlp
import os
import logging
from src.config.app import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_video_info(url):
    try:
        # Cấu hình tùy chọn cho yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo+bestaudio/best',
            # Tắt extract_flat để lấy đầy đủ thông tin
            'extract_flat': False,
            'no_color': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # Thêm các tùy chọn mới
            'extract_thumbnails': True,
            'youtube_include_dash_manifest': False,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        }
        
        logger.debug(f"Đang lấy thông tin video từ URL: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    logger.error("Không thể lấy thông tin video")
                    return None
                
                # Lọc formats hợp lệ
                valid_formats = []
                for f in info.get('formats', []):
                    if not f.get('format_id'):
                        continue
                    
                    # Chỉ lấy các format video
                    if f.get('vcodec') == 'none':
                        continue
                        
                    format_info = {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution', 'unknown'),
                        'filesize': f.get('filesize', 0),
                        'format': f.get('format', ''),
                        'quality': f.get('quality', 0)
                    }
                    valid_formats.append(format_info)
                
                # Sắp xếp format theo chất lượng
                valid_formats.sort(key=lambda x: x['quality'], reverse=True)
                
                # Lấy thumbnail tốt nhất
                thumbnails = info.get('thumbnails', [])
                best_thumbnail = None
                if thumbnails:
                    # Sắp xếp theo kích thước
                    thumbnails.sort(key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
                    best_thumbnail = thumbnails[0].get('url')
                
                return {
                    'title': info.get('title', 'Video không tiêu đề'),
                    'duration': info.get('duration', 0),
                    'thumbnail': best_thumbnail or info.get('thumbnail', ''),
                    'formats': valid_formats,
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0)
                }
            except yt_dlp.utils.ExtractorError as e:
                logger.error(f"Lỗi trích xuất thông tin video: {str(e)}")
                error_msg = 'Không thể tải video này. '
                if 'facebook' in url.lower():
                    error_msg += 'Đối với Facebook, hãy đảm bảo video ở chế độ công khai.'
                elif 'youtube' in url.lower():
                    error_msg += 'Đối với YouTube, hãy đảm bảo video không bị giới hạn độ tuổi.'
                return {'error': error_msg}
                
    except Exception as e:
        logger.exception(f"Lỗi khi lấy thông tin video: {str(e)}")
        return None

def download_video(url, format_id=None):
    try:
        downloads_dir = os.path.join(Config.INSTANCE_PATH, 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        ydl_opts = {
            'format': format_id if format_id else 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return {'success': False, 'message': 'Không thể tải video'}
                
                filename = ydl.prepare_filename(info)
                return {
                    'success': True,
                    'path': filename,
                    'title': info.get('title', 'Video không tiêu đề')
                }
            except Exception as e:
                logger.exception(f"Lỗi tải xuống: {str(e)}")
                return {
                    'success': False, 
                    'message': 'Không thể tải video này. Vui lòng kiểm tra URL hoặc thử lại sau.'
                }
                
    except Exception as e:
        logger.exception(f"Lỗi cấu hình tải xuống: {str(e)}")
        return {'success': False, 'message': str(e)}