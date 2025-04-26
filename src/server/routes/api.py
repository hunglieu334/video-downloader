from flask import jsonify, request, send_file, abort
from flask_login import login_required, current_user
import os
import traceback

from src.server.services.download import get_video_info, download_video, detect_platform
from src.server.utils.validators import is_valid_url
from src.server.utils.fileManager import get_cache_path, clean_expired_cache
from src.config.app import Config

def register_api_routes(app):
    @app.route('/api/preview', methods=['POST'])
    @login_required
    def preview_video():
        """API endpoint for video preview"""
        try:
            data = request.get_json() or {}
            video_url = data.get('url') or request.form.get('url')
            platform = data.get('platform') or request.form.get('platform', 'auto')
            
            if not video_url or not is_valid_url(video_url):
                return jsonify({"error": "Vui lòng cung cấp URL hợp lệ"}), 400
                
            # Auto-detect platform if set to 'auto'
            if platform == 'auto':
                platform = detect_platform(video_url)
                
            # Get video information
            video_info = get_video_info(video_url, platform, Config.COOKIE_FILE)
            
            return jsonify({
                "success": True,
                "data": video_info
            })
                
        except Exception as e:
            app.logger.error(f"Preview error: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"error": f"Lỗi khi xử lý video: {str(e)}"}), 500
    
    @app.route('/api/download', methods=['POST'])
    @login_required
    def download_video_endpoint():
        """API endpoint for video download"""
        try:
            video_url = request.form.get('url')
            platform = request.form.get('platform', 'auto')
            quality = request.form.get('quality', 'best')
            format_id = request.form.get('format_id')  # Thêm tham số format_id
            
            # Log thông tin tải xuống
            app.logger.info(f"Download request - URL: {video_url}, Platform: {platform}, Quality: {quality}, Format ID: {format_id}")
            
            if not video_url or not is_valid_url(video_url):
                return jsonify({"error": "Vui lòng cung cấp URL hợp lệ"}), 400
                
            # Dọn dẹp cache
            clean_expired_cache()
            
            # Tự động nhận diện nền tảng nếu cần
            if platform == 'auto':
                platform = detect_platform(video_url)
                
            # Tải xuống video với format_id nếu được cung cấp
            if platform == 'youtube' and format_id:
                from src.server.services.youtube import download_youtube_video
                file_path = download_youtube_video(video_url, quality, Config.COOKIE_FILE, format_id)
            else:
                # Sử dụng hàm download thông thường cho các trường hợp khác
                file_path = download_video(video_url, platform, quality, Config.COOKIE_FILE)
            
            if not os.path.exists(file_path):
                return jsonify({"error": "Không thể tải xuống video"}), 500
            
            # Tạo tên file để download
            filename = os.path.basename(file_path)
            
            # Trả về file để download
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            app.logger.error(f"Download error: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({"error": f"Lỗi khi tải xuống video: {str(e)}"}), 500