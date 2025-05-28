import os
from pathlib import Path

# Application settings
APP_NAME = "P2P File Sharing"
APP_VERSION = "1.0.0"

# Network settings
DEFAULT_PORT = 5000
MULTICAST_GROUP = "224.3.29.71"
BUFFER_SIZE = 8192

# File settings
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
ALLOWED_EXTENSIONS = {
    # Documents
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'bmp',
    # Audio
    'mp3', 'wav', 'ogg',
    # Video
    'mp4', 'avi', 'mkv',
    # Archives
    'zip', 'rar', '7z',
    # Code
    'py', 'java', 'cpp', 'c', 'h', 'js', 'html', 'css',
    # Other
    'json', 'xml', 'csv'
}

# Database settings
DB_DIR = Path.home() / '.p2p_fileshare'
DB_FILE = DB_DIR / 'p2p_fileshare.db'

# Create database directory if it doesn't exist
DB_DIR.mkdir(exist_ok=True)

# UI settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
UPDATE_INTERVAL = 5000  # milliseconds 