from flask import Blueprint, jsonify, request
from flask_login import login_required
from src.utils.video_utils import get_video_info, download_video
import logging
import re

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

def validate_url(url):
    """Validate URL format and supported platforms."""
    if not url:
        return False, "URL không được để trống"
        
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
    if not url_pattern.match(url):
        return False, "URL không hợp lệ"
        
    # Check for supported platforms
    supported_domains = ['youtube.com', 'youtu.be', 'facebook.com', 'fb.watch', 'tiktok.com']
    if not any(domain in url.lower() for domain in supported_domains):
        return False, "URL không được hỗ trợ. Chỉ hỗ trợ YouTube, Facebook và TikTok"
        
    return True, None

@api.route('/api/preview', methods=['POST'])
@login_required
def preview_video():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400
            
        url = data.get('url', '').strip()
        is_valid, error_message = validate_url(url)
        
        if not is_valid:
            return jsonify({'error': error_message}), 400
            
        logger.debug(f"Processing preview request for URL: {url}")
        
        video_info = get_video_info(url)
        if not video_info:
            return jsonify({'error': 'Không thể lấy thông tin video. Vui lòng kiểm tra URL và thử lại.'}), 400
            
        return jsonify(video_info)
        
    except Exception as e:
        logger.exception("Error processing preview request")
        return jsonify({'error': 'Có lỗi xảy ra khi xử lý yêu cầu'}), 500

@api.route('/api/download', methods=['POST'])
@login_required
def download_video_route():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL không được để trống'}), 400
            
        url = data.get('url')
        format_id = data.get('format_id')
        
        logger.debug(f"Download request - URL: {url}, Format: {format_id}")
        
        result = download_video(url, format_id)
        if not result['success']:
            return jsonify({'error': result['message']}), 400
            
        return jsonify({
            'message': 'Video đã được tải xuống thành công',
            'path': result['path'],
            'title': result['title']
        })
        
    except Exception as e:
        logger.exception("Download error")
        return jsonify({'error': 'Lỗi khi tải video'}), 500