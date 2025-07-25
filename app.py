import os
import logging
import redis
from flask import Flask
from flask_session import Session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Redis client
redis_client = None

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object('config.Config')
    app.secret_key = os.environ.get("SESSION_SECRET")
    
    # Proxy fix for production deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure session with Redis fallback
    global redis_client
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    try:
        redis_client = redis.from_url(redis_url, decode_responses=False)
        redis_client.ping()
        print("✓ Redis connection successful - using Redis sessions")
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_client
    except (redis.ConnectionError, OSError):
        print("✗ Redis connection failed - using filesystem sessions")
        redis_client = None
        app.config['SESSION_TYPE'] = 'filesystem'
    
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'ai_booking:'
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    Session(app)
    

    
    # Configure CORS
    CORS(app, 
         origins=['https://ai-booking-agent-tfd7.onrender.com', 'https://*.replit.dev'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Register blueprints
    from controllers.auth_controller import auth_bp
    from controllers.booking_controller import booking_bp
    from controllers.api_controller import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(booking_bp, url_prefix='/booking')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Main route
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    @app.route('/setup')
    def setup():
        from flask import render_template
        return render_template('upload_credentials.html')
    
    # Initialize data storage
    with app.app_context():
        # Import models
        from models import calendar_model, ai_model
        
        # Store Redis client in app config instead of as attribute
        app.config['REDIS_CLIENT'] = redis_client
        
        if redis_client:
            from redis_models import create_redis_managers
            app.config['DATA_MANAGERS'] = create_redis_managers(redis_client)
            print("✓ Redis data managers initialized successfully")
        else:
            # Fallback to in-memory storage for development
            app.config['DATA_MANAGERS'] = None
            print("⚠ Using fallback storage - install Redis for full functionality")
    
    return app

# Create the app instance
app = create_app()
