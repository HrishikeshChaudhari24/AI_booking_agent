import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    
    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Auto-detect redirect URI based on environment
    REPLIT_URL = os.environ.get('REPLIT_DEV_DOMAIN')
    if REPLIT_URL:
        GOOGLE_REDIRECT_URI = f'https://{REPLIT_URL}/auth/callback'
    else:
        GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://ai-booking-agent-tfd7.onrender.com/auth/callback')
          # GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://ai-booking-agent-tfd7.onrender.com/auth/callback')
    
    # Gemini API configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Calendar API scopes
    CALENDAR_SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    # Session configuration
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    
    # Security settings
    COOKIE_SECURE = True
    COOKIE_HTTPONLY = True
    COOKIE_SAMESITE = 'Lax'
