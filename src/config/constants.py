# User agents
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Quality mapping for video formats
QUALITY_MAP = {
    'best': 'bestvideo+bestaudio/best',
    '2160': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]/best',
    '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
    '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
    '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
    '360': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best',
    'audio': 'bestaudio/best'
}

# Platform identifiers
PLATFORMS = {
    'youtube': {
        'domains': ['youtube.com', 'youtu.be', 'm.youtube.com'],
        'name': 'YouTube'
    },
    'facebook': {
        'domains': ['facebook.com', 'fb.com', 'fb.watch', 'm.facebook.com'],
        'name': 'Facebook'
    },
    'tiktok': {
        'domains': ['tiktok.com', 'vm.tiktok.com', 'm.tiktok.com'],
        'name': 'TikTok'
    }
}