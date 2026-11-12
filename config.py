import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartcity-connect-super-secure-key-2026')
    
    # Instance folder path
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    # Database URI using Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'smartcity.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # SMS / OTP Verification
    SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'development')
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
    OTP_EXPIRY_MINUTES = 10
    
    # Reverse Geocoding Provider: 'nominatim' (Free OSM) or 'google'
    GEOCODING_PROVIDER = os.environ.get('GEOCODING_PROVIDER', 'nominatim')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    
    # Pre-configured Authority Account (Protected Setup)
    DEFAULT_AUTHORITY_USERNAME = os.environ.get('DEFAULT_AUTHORITY_USERNAME', 'officer_admin')
    DEFAULT_AUTHORITY_PASSWORD = os.environ.get('DEFAULT_AUTHORITY_PASSWORD', 'AuthorityPass@2026')
    DEFAULT_AUTHORITY_ROLE = os.environ.get('DEFAULT_AUTHORITY_ROLE', 'Senior Municipal Officer')

    # Default Map Coordinates (Bengaluru Smart City)
    DEFAULT_MAP_LAT = 12.9716
    DEFAULT_MAP_LNG = 77.5946
    DEFAULT_MAP_ZOOM = 12
