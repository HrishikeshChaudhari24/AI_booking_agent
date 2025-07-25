import logging
from flask import Blueprint, request, session, jsonify
from services.redis_session_service import RedisSessionService

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Booking Agent'
    })

@api_bp.route('/session', methods=['GET'])
def get_session_info():
    """Get session information"""
    try:
        return jsonify({
            'session_id': session.get('session_id'),
            'authenticated': session.get('authenticated', False),
            'has_credentials': 'google_credentials' in session
        })
        
    except Exception as e:
        logger.error(f"Session info error: {e}")
        return jsonify({'error': 'Failed to get session info'}), 500

@api_bp.route('/session', methods=['POST'])
def create_session():
    """Create new session"""
    try:
        session_service = RedisSessionService()
        session_id = session_service.create_session()
        session['session_id'] = session_id
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Create session error: {e}")
        return jsonify({'error': 'Failed to create session'}), 500

@api_bp.route('/conversation_history')
def get_conversation_history():
    """Get conversation history for current session"""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        
        session_id = session.get('session_id', '')
        session_service = RedisSessionService()
        history = session_service.get_conversation_history(session_id)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Get conversation history error: {e}")
        return jsonify({'error': 'Failed to get conversation history'}), 500

@api_bp.route('/test_ai', methods=['POST'])
def test_ai():
    """Test AI model connectivity"""
    try:
        from models.ai_model import AIModel
        
        data = request.get_json()
        test_message = data.get('message', 'Hello, can you help me schedule a meeting?')
        
        ai_model = AIModel()
        intent = ai_model.extract_booking_intent(test_message)
        response = ai_model.generate_response(test_message)
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'extracted_intent': intent.dict(),
            'ai_response': response
        })
        
    except Exception as e:
        logger.error(f"AI test error: {e}")
        return jsonify({'error': f'AI test failed: {str(e)}'}), 500

@api_bp.route('/test_calendar', methods=['POST'])
def test_calendar():
    """Test calendar connectivity"""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        
        from models.calendar_model import CalendarModel
        
        calendar_model = CalendarModel(session['google_credentials'])
        events = calendar_model.get_upcoming_events(5)
        
        return jsonify({
            'success': True,
            'events_count': len(events),
            'sample_events': events[:3]  # Return first 3 events as sample
        })
        
    except Exception as e:
        logger.error(f"Calendar test error: {e}")
        return jsonify({'error': f'Calendar test failed: {str(e)}'}), 500

@api_bp.errorhandler(404)
def api_not_found(error):
    """Handle API 404 errors"""
    return jsonify({'error': 'API endpoint not found'}), 404

@api_bp.errorhandler(500)
def api_server_error(error):
    """Handle API server errors"""
    logger.error(f"API server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
