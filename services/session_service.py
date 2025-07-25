import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing user sessions and conversation context"""
    
    SESSION_DIR = 'flask_session'
    CONVERSATION_DIR = 'conversations'
    
    @classmethod
    def _ensure_directories(cls):
        """Ensure session directories exist"""
        Path(cls.SESSION_DIR).mkdir(exist_ok=True)
        Path(cls.CONVERSATION_DIR).mkdir(exist_ok=True)
    
    @classmethod
    def create_session(cls) -> str:
        """Create a new session ID"""
        cls._ensure_directories()
        session_id = str(uuid.uuid4())
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    @classmethod
    def store_conversation_context(cls, session_id: str, user_message: str, 
                                  ai_response: str, intent: Optional[Dict[str, Any]] = None):
        """Store conversation context for a session"""
        try:
            cls._ensure_directories()
            
            context_file = Path(cls.CONVERSATION_DIR) / f"{session_id}.json"
            
            # Load existing context or create new
            if context_file.exists():
                with open(context_file, 'r') as f:
                    context = json.load(f)
            else:
                context = {
                    'session_id': session_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'messages': []
                }
            
            # Add new message pair
            message_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_message': user_message,
                'ai_response': ai_response,
                'intent': intent or {}
            }
            
            context['messages'].append(message_entry)
            context['updated_at'] = datetime.utcnow().isoformat()
            
            # Keep only last 50 messages to prevent excessive growth
            if len(context['messages']) > 50:
                context['messages'] = context['messages'][-50:]
            
            # Save context
            with open(context_file, 'w') as f:
                json.dump(context, f, indent=2)
            
            logger.debug(f"Stored conversation context for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation context: {e}")
    
    @classmethod
    def get_conversation_context(cls, session_id: str) -> str:
        """Get conversation context as formatted string"""
        try:
            cls._ensure_directories()
            
            context_file = Path(cls.CONVERSATION_DIR) / f"{session_id}.json"
            
            if not context_file.exists():
                return ""
            
            with open(context_file, 'r') as f:
                context = json.load(f)
            
            # Format recent messages for context
            messages = context.get('messages', [])[-10:]  # Last 10 messages
            context_str = ""
            
            for msg in messages:
                context_str += f"User: {msg['user_message']}\n"
                context_str += f"Assistant: {msg['ai_response']}\n\n"
            
            return context_str.strip()
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return ""
    
    @classmethod
    def get_conversation_history(cls, session_id: str) -> List[Dict[str, Any]]:
        """Get full conversation history for a session"""
        try:
            cls._ensure_directories()
            
            context_file = Path(cls.CONVERSATION_DIR) / f"{session_id}.json"
            
            if not context_file.exists():
                return []
            
            with open(context_file, 'r') as f:
                context = json.load(f)
            
            return context.get('messages', [])
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    @classmethod
    def clear_conversation_context(cls, session_id: str):
        """Clear conversation context for a session"""
        try:
            cls._ensure_directories()
            
            context_file = Path(cls.CONVERSATION_DIR) / f"{session_id}.json"
            
            if context_file.exists():
                context_file.unlink()
                logger.info(f"Cleared conversation context for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear conversation context: {e}")
    
    @classmethod
    def cleanup_old_sessions(cls, days_old: int = 7):
        """Clean up old session files"""
        try:
            cls._ensure_directories()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Clean conversation files
            for context_file in Path(cls.CONVERSATION_DIR).glob("*.json"):
                if context_file.stat().st_mtime < cutoff_date.timestamp():
                    context_file.unlink()
                    logger.info(f"Cleaned up old conversation file: {context_file}")
            
            # Clean Flask session files
            for session_file in Path(cls.SESSION_DIR).glob("*"):
                if session_file.stat().st_mtime < cutoff_date.timestamp():
                    session_file.unlink()
                    logger.info(f"Cleaned up old session file: {session_file}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
    
    @classmethod
    def get_session_stats(cls) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            cls._ensure_directories()
            
            conversation_files = list(Path(cls.CONVERSATION_DIR).glob("*.json"))
            session_files = list(Path(cls.SESSION_DIR).glob("*"))
            
            stats = {
                'active_conversations': len(conversation_files),
                'active_sessions': len(session_files),
                'last_cleanup': datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
