from flask import jsonify, request, send_file, after_this_request, current_app
from flask_login import login_required, current_user
import os
import time
import traceback

from src.server.services.download import get_video_info, download_video, detect_platform
from src.server.utils.validators import is_valid_url, is_netscape_cookie_file
from src.server.utils.fileManager import get_cache_path, clean_expired_cache
from src.server.models import DownloadHistory, db
from src.config.app import Config
from src.config.constants import ERROR_MESSAGES, SUPPORTED_PLATFORMS

def register_api_routes(app):
    """Register API routes with the Flask application"""
    
    @app.route('/api/preview', methods=['POST'])
    @login_required
    def preview_video():
        """Preview video information before downloading"""
        video_url = request.form.get('url', '').strip()
        platform = request.form.get('platform', 'auto')
        
        # Validate URL
        if not video_url:
            return jsonify({'error': ERROR_MESSAGES['url_required']}), 400
            
        if not is_valid_url(video_url):
            return jsonify({'error': ERROR_MESSAGES['invalid_url']}), 400
            
        # Check cookie file format if it exists
        if os.path.exists(Config.COOKIE_FILE) and not is_netscape_cookie_file(Config.COOKIE_FILE):
            return jsonify({'error': ERROR_MESSAGES['cookie_format']}), 400
            
        # Auto-detect platform if not specified or set to auto
        if platform == 'auto':
            platform = detect_platform(video_url)
            if platform == 'unknown':
                return jsonify({'error': ERROR_MESSAGES['unsupported_platform']}), 400
        
        # Check if platform is supported
        if platform not in SUPPORTED_PLATFORMS:
            return jsonify({'error': ERROR_MESSAGES['unsupported_platform']}), 400
        
        try:
            # Get video information
            info = get_video_info(video_url, platform, Config.COOKIE_FILE)
            
            # Include the detected platform in the response
            info['platform'] = platform
            
            return jsonify(info), 200
        except Exception as e:
            app.logger.error(f"Preview error for {video_url}: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                'error': str(e) if str(e) else 'Failed to get video information'
            }), 500
    
    @app.route('/api/download', methods=['POST'])
    @login_required
    def download_video_route():
        """Download video endpoint"""
        video_url = request.form.get('url', '').strip()
        platform = request.form.get('platform', 'auto')
        quality = request.form.get('quality', 'best')
        video_title = request.form.get('title', 'video')
        
        # Validate URL
        if not video_url:
            return jsonify({'error': ERROR_MESSAGES['url_required']}), 400
            
        if not is_valid_url(video_url):
            return jsonify({'error': ERROR_MESSAGES['invalid_url']}), 400
            
        # Detect platform if necessary
        if platform == 'auto':
            platform = detect_platform(video_url)
            
        # Check if platform is supported
        if platform not in SUPPORTED_PLATFORMS:
            return jsonify({'error': ERROR_MESSAGES['unsupported_platform']}), 400
        
        # Clean expired cache before download
        clean_expired_cache()
        
        try:
            # Try to download the video
            start_time = time.time()
            file_path = download_video(video_url, platform, quality, Config.COOKIE_FILE)
            download_time = time.time() - start_time
            
            # Log download history
            history = DownloadHistory(
                user_id=current_user.id,
                url=video_url,
                platform=platform,
                quality=quality,
                title=video_title,
                success=True
            )
            
            # Update user download count
            current_user.increment_download_count()
            
            db.session.add(history)
            db.session.commit()
            
            app.logger.info(f"Download successful: {video_url} ({quality}) in {download_time:.2f}s")
            
            # Guess safe filename from video title
            filename = "".join(c if c.isalnum() or c in ['-', '_', '.'] else '_' for c in video_title)
            filename = f"{filename}.mp4"
            
            return send_file(
                file_path, 
                as_attachment=True,
                download_name=filename,
                mimetype='video/mp4'
            )
            
        except Exception as e:
            # Log failed download
            history = DownloadHistory(
                user_id=current_user.id,
                url=video_url,
                platform=platform,
                quality=quality,
                title=video_title,
                success=False
            )
            
            db.session.add(history)
            db.session.commit()
            
            app.logger.error(f"Download error for {video_url}: {str(e)}")
            app.logger.error(traceback.format_exc())
            
            return jsonify({
                'error': str(e) if str(e) else ERROR_MESSAGES['download_failed']
            }), 500
            
    @app.route('/api/check-cookies', methods=['POST'])
    @login_required
    def check_cookies():
        """Validate uploaded cookie file"""
        if 'cookie_file' not in request.files:
            return jsonify({'valid': False, 'message': 'No file provided'}), 400
            
        file = request.files['cookie_file']
        
        if file.filename == '':
            return jsonify({'valid': False, 'message': 'No file selected'}), 400
            
        try:
            # Save to temporary location to validate
            temp_path = os.path.join(Config.CACHE_FOLDER, 'temp_cookies.txt')
            file.save(temp_path)
            
            # Validate format
            if is_netscape_cookie_file(temp_path):
                # If valid, move to the proper location
                file.seek(0)
                os.makedirs(os.path.dirname(Config.COOKIE_FILE), exist_ok=True)
                file.save(Config.COOKIE_FILE)
                return jsonify({'valid': True, 'message': 'Cookie file uploaded successfully'}), 200
            else:
                return jsonify({'valid': False, 'message': ERROR_MESSAGES['cookie_format']}), 400
                
        except Exception as e:
            app.logger.error(f"Cookie upload error: {str(e)}")
            return jsonify({'valid': False, 'message': str(e)}), 500
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)