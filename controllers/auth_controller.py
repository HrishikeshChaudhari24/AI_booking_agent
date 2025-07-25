import os
import json
import logging
from flask import Blueprint, request, redirect, session, jsonify, render_template, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from config import Config

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def get_google_oauth_flow():
    """Create Google OAuth flow"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [Config.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=Config.CALENDAR_SCOPES
    )
    flow.redirect_uri = Config.GOOGLE_REDIRECT_URI
    return flow

@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login"""
    try:
        # Check if credentials are configured
        if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
            return render_template('setup_required.html')
        
        flow = get_google_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        session['oauth_state'] = state
        return redirect(authorization_url)
        
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        return render_template('oauth_error.html', error=str(e))

@auth_bp.route('/callback')
def oauth_callback():
    """Handle OAuth callback"""
    try:
        # Verify state parameter
        if 'oauth_state' not in session:
            return jsonify({'error': 'Invalid OAuth state'}), 400
            
        state = session.pop('oauth_state')
        if request.args.get('state') != state:
            return jsonify({'error': 'State mismatch'}), 400
        
        # Get authorization code
        authorization_code = request.args.get('code')
        if not authorization_code:
            return jsonify({'error': 'Authorization code not found'}), 400
        
        # Exchange code for tokens
        flow = get_google_oauth_flow()
        flow.fetch_token(authorization_response=request.url)
        
        # Store credentials in session
        credentials = flow.credentials
        session['google_credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': getattr(credentials, 'token_uri', 'https://oauth2.googleapis.com/token'),
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        session['authenticated'] = True
        logger.info("User authenticated successfully")
        
        return render_template('auth_callback.html')
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/status')
def auth_status():
    """Check authentication status"""
    try:
        authenticated = session.get('authenticated', False)
        
        if authenticated and 'google_credentials' in session:
            # Verify credentials are still valid
            creds_data = session['google_credentials']
            credentials = Credentials.from_authorized_user_info(creds_data)
            
            if credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                    # Update session with new token
                    session['google_credentials']['token'] = credentials.token
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    session.clear()
                    return jsonify({'authenticated': False})
            
            return jsonify({
                'authenticated': True,
                'user_info': {
                    'has_calendar_access': True
                }
            })
        else:
            return jsonify({'authenticated': False})
            
    except Exception as e:
        logger.error(f"Auth status check error: {e}")
        return jsonify({'authenticated': False})

@auth_bp.route('/refresh_token', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    try:
        if 'google_credentials' not in session:
            return jsonify({'error': 'No credentials found'}), 401
        
        creds_data = session['google_credentials']
        credentials = Credentials.from_authorized_user_info(creds_data)
        
        if credentials.refresh_token:
            credentials.refresh(Request())
            session['google_credentials']['token'] = credentials.token
            return jsonify({'success': True, 'message': 'Token refreshed'})
        else:
            return jsonify({'error': 'No refresh token available'}), 401
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500
