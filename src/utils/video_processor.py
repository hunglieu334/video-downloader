import yt_dlp

def get_video_info(url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'formats': [
                    {
                        'format_id': f.get('format_id', ''),
                        'ext': f.get('ext', ''),
                        'filesize': f.get('filesize', 0),
                        'format': f.get('format', '')
                    }
                    for f in info.get('formats', [])
                ]
            }
    except Exception as e:
        print(f"Error extracting video info: {str(e)}")
        return None

def download_video(url, output_path, format_id=None):
    try:
        ydl_opts = {
            'format': format_id if format_id else 'best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return False