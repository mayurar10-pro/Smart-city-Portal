import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartcity-connect-super-secret-key-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'smartcity.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max image size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Default Admin Credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Default Map Coordinates (Bangalore Smart City center)
    DEFAULT_MAP_LAT = 12.9716
    DEFAULT_MAP_LNG = 77.5946
    DEFAULT_MAP_ZOOM = 12
