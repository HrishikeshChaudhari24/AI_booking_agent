"""
Redis-based session service for the AI Booking Agent application
"""
import uuid
import logging
from datetime import datetime
from flask import request, current_app
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class RedisSessionService:
    """Manages user sessions using Redis data managers"""
    
    def __init__(self):
        self.session_manager = None
        self.user_manager = None
        self.conversation_manager = None
    
    def _get_managers(self):
        """Get Redis data managers from current app"""
        if not self.session_manager:
            managers = current_app.data_managers
            self.session_manager = managers['session_manager']
            self.user_manager = managers['user_manager']
            self.conversation_manager = managers['conversation_manager']
    
    def _get_session_id_from_request(self) -> Optional[str]:
        """Extract session ID from request headers or cookies"""
        # Try to get from custom header first
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            return session_id
        
        # Try to get from cookie
        session_id = request.cookies.get('ai_booking_session')
        return session_id
    
    def create_session(self, user_id: str = None) -> str:
        """Create a new session and return session ID"""
        self._get_managers()
        
        session_id = str(uuid.uuid4())
        self.session_manager.create_session(session_id, user_id)
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session_id(self) -> str:
        """Get current session ID or create new one"""
        session_id = self._get_session_id_from_request()
        if not session_id:
            return self.create_session()
        
        # Verify session exists
        self._get_managers()
        if not self.session_manager.get_session(session_id):
            return self.create_session()
        
        return session_id
    
    def get_session_data(self, session_id: str = None) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if not session_id:
            session_id = self.get_session_id()
        
        self._get_managers()
        return self.session_manager.get_session(session_id)
    
    def update_session_data(self, session_id: str, **kwargs):
        """Update session data"""
        self._get_managers()
        return self.session_manager.update_session(session_id, **kwargs)
    
    def set_user_authenticated(self, session_id: str, user_id: str, user_info: Dict[str, Any]):
        """Mark user as authenticated and store user info"""
        self._get_managers()
        
        # Update session
        self.session_manager.update_session(
            session_id,
            user_id=user_id,
            is_authenticated=True,
            data=user_info
        )
        
        # Create or update user record
        self.user_manager.create_user(
            user_id=user_id,
            email=user_info.get('email'),
            name=user_info.get('name'),
            picture_url=user_info.get('picture')
        )
        
        logger.info(f"User {user_id} authenticated in session {session_id}")
    
    def get_user_id(self, session_id: str = None) -> Optional[str]:
        """Get authenticated user ID"""
        session_data = self.get_session_data(session_id)
        return session_data.get('user_id') if session_data else None
    
    def get_user_info(self, session_id: str = None) -> Optional[Dict[str, Any]]:
        """Get authenticated user info"""
        session_data = self.get_session_data(session_id)
        return session_data.get('data', {}) if session_data else None
    
    def is_authenticated(self, session_id: str = None) -> bool:
        """Check if user is authenticated"""
        session_data = self.get_session_data(session_id)
        return session_data.get('is_authenticated', False) if session_data else False
    
    def logout(self, session_id: str):
        """Clear user authentication data"""
        self._get_managers()
        self.session_manager.update_session(
            session_id,
            user_id=None,
            is_authenticated=False,
            data={}
        )
        
        logger.info(f"User logged out from session {session_id}")
    
    def delete_session(self, session_id: str):
        """Delete session"""
        self._get_managers()
        self.session_manager.delete_session(session_id)
        logger.info(f"Session {session_id} deleted")
    
    def store_conversation_context(self, session_id: str, user_message: str, 
                                  ai_response: str, intent: Optional[Dict[str, Any]] = None):
        """Store conversation context using Redis conversation manager"""
        self._get_managers()
        
        # Get or create conversation for this session
        user_id = self.get_user_id(session_id)
        if not user_id:
            logger.warning(f"No user_id found for session {session_id}")
            return
        
        # Try to find existing conversation for this session
        conversations = self.conversation_manager.get_user_conversations(user_id)
        current_conversation = None
        
        for conv in conversations:
            if conv.get('session_id') == session_id:
                current_conversation = conv
                break
        
        if not current_conversation:
            # Create new conversation
            conversation_id = self.conversation_manager.create_conversation(user_id, session_id)
        else:
            conversation_id = current_conversation['id']
        
        # Add messages
        self.conversation_manager.add_message(conversation_id, 'user', user_message)
        self.conversation_manager.add_message(conversation_id, 'assistant', ai_response, intent)
        
        logger.debug(f"Stored conversation for session {session_id}")
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        self._get_managers()
        
        user_id = self.get_user_id(session_id)
        if not user_id:
            return []
        
        conversations = self.conversation_manager.get_user_conversations(user_id)
        
        for conv in conversations:
            if conv.get('session_id') == session_id:
                messages = conv.get('messages', [])
                return messages[-limit:] if messages else []
        
        return []