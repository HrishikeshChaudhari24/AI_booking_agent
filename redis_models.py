"""
Redis-based data models for the AI Booking Agent application
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis


class RedisDataManager:
    """Redis data manager for handling all data operations"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate Redis key with prefix"""
        return f"ai_booking:{prefix}:{identifier}"
    
    def _serialize_data(self, data: Dict[str, Any]) -> str:
        """Serialize data to JSON string"""
        # Convert datetime objects to ISO format strings
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, default=datetime_converter)
    
    def _deserialize_data(self, data_str: str) -> Dict[str, Any]:
        """Deserialize JSON string to data"""
        if not data_str:
            return {}
        
        data = json.loads(data_str)
        
        # Convert ISO format strings back to datetime objects
        for key, value in data.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass  # Keep as string if not a valid datetime
        
        return data


class UserManager(RedisDataManager):
    """Manage user data in Redis"""
    
    def create_user(self, user_id: str, email: str, name: str = None, 
                   picture_url: str = None) -> Dict[str, Any]:
        """Create or update user"""
        user_data = {
            'id': user_id,
            'email': email,
            'name': name,
            'picture_url': picture_url,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_login': datetime.utcnow()
        }
        
        key = self._generate_key('user', user_id)
        self.redis.setex(key, timedelta(days=30), self._serialize_data(user_data))
        return user_data
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        key = self._generate_key('user', user_id)
        data = self.redis.get(key)
        return self._deserialize_data(data) if data else None
    
    def update_user_tokens(self, user_id: str, access_token: str, 
                          refresh_token: str = None, expires_at: datetime = None):
        """Update user OAuth tokens"""
        user_data = self.get_user(user_id)
        if not user_data:
            return None
        
        user_data.update({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expires_at': expires_at,
            'updated_at': datetime.utcnow()
        })
        
        key = self._generate_key('user', user_id)
        self.redis.setex(key, timedelta(days=30), self._serialize_data(user_data))
        return user_data
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (requires scanning, use sparingly)"""
        pattern = self._generate_key('user', '*')
        for key in self.redis.scan_iter(match=pattern):
            user_data = self._deserialize_data(self.redis.get(key))
            if user_data.get('email') == email:
                return user_data
        return None


class SessionManager(RedisDataManager):
    """Manage user sessions in Redis"""
    
    def create_session(self, session_id: str = None, user_id: str = None) -> str:
        """Create new session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_authenticated': bool(user_id),
            'data': {}
        }
        
        key = self._generate_key('session', session_id)
        # Sessions expire after 24 hours of inactivity
        self.redis.setex(key, timedelta(hours=24), self._serialize_data(session_data))
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        key = self._generate_key('session', session_id)
        data = self.redis.get(key)
        return self._deserialize_data(data) if data else None
    
    def update_session(self, session_id: str, **kwargs):
        """Update session data"""
        session_data = self.get_session(session_id)
        if not session_data:
            return None
        
        session_data.update(kwargs)
        session_data['updated_at'] = datetime.utcnow()
        
        key = self._generate_key('session', session_id)
        self.redis.setex(key, timedelta(hours=24), self._serialize_data(session_data))
        return session_data
    
    def delete_session(self, session_id: str):
        """Delete session"""
        key = self._generate_key('session', session_id)
        self.redis.delete(key)


class ConversationManager(RedisDataManager):
    """Manage conversation history in Redis"""
    
    def create_conversation(self, user_id: str, session_id: str) -> str:
        """Create new conversation"""
        conversation_id = str(uuid.uuid4())
        
        conversation_data = {
            'id': conversation_id,
            'user_id': user_id,
            'session_id': session_id,
            'messages': [],
            'context': {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        key = self._generate_key('conversation', conversation_id)
        # Conversations expire after 7 days
        self.redis.setex(key, timedelta(days=7), self._serialize_data(conversation_data))
        
        # Also maintain a user conversation index
        user_conversations_key = self._generate_key('user_conversations', user_id)
        self.redis.sadd(user_conversations_key, conversation_id)
        self.redis.expire(user_conversations_key, timedelta(days=7))
        
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        key = self._generate_key('conversation', conversation_id)
        data = self.redis.get(key)
        return self._deserialize_data(data) if data else None
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Dict[str, Any] = None):
        """Add message to conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        conversation['messages'].append(message)
        conversation['updated_at'] = datetime.utcnow()
        
        key = self._generate_key('conversation', conversation_id)
        self.redis.setex(key, timedelta(days=7), self._serialize_data(conversation))
        return conversation
    
    def update_context(self, conversation_id: str, context: Dict[str, Any]):
        """Update conversation context"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        conversation['context'].update(context)
        conversation['updated_at'] = datetime.utcnow()
        
        key = self._generate_key('conversation', conversation_id)
        self.redis.setex(key, timedelta(days=7), self._serialize_data(conversation))
        return conversation
    
    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        user_conversations_key = self._generate_key('user_conversations', user_id)
        conversation_ids = self.redis.smembers(user_conversations_key)
        
        conversations = []
        for conv_id in conversation_ids:
            conversation = self.get_conversation(conv_id.decode('utf-8'))
            if conversation:
                conversations.append(conversation)
        
        return sorted(conversations, key=lambda x: x['updated_at'], reverse=True)


class CalendarEventManager(RedisDataManager):
    """Manage calendar events in Redis"""
    
    def create_event(self, user_id: str, google_event_id: str, title: str,
                    start_time: datetime, end_time: datetime, **kwargs) -> str:
        """Create calendar event record"""
        event_id = str(uuid.uuid4())
        
        event_data = {
            'id': event_id,
            'user_id': user_id,
            'google_event_id': google_event_id,
            'title': title,
            'description': kwargs.get('description'),
            'start_time': start_time,
            'end_time': end_time,
            'location': kwargs.get('location'),
            'attendees': kwargs.get('attendees', []),
            'intent_confidence': kwargs.get('intent_confidence'),
            'created_by_ai': kwargs.get('created_by_ai', True),
            'modification_type': kwargs.get('modification_type', 'create'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        key = self._generate_key('calendar_event', event_id)
        # Calendar events expire after 90 days
        self.redis.setex(key, timedelta(days=90), self._serialize_data(event_data))
        
        # Maintain user events index
        user_events_key = self._generate_key('user_events', user_id)
        self.redis.sadd(user_events_key, event_id)
        self.redis.expire(user_events_key, timedelta(days=90))
        
        return event_id
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get calendar event by ID"""
        key = self._generate_key('calendar_event', event_id)
        data = self.redis.get(key)
        return self._deserialize_data(data) if data else None
    
    def get_user_events(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all calendar events for a user"""
        user_events_key = self._generate_key('user_events', user_id)
        event_ids = self.redis.smembers(user_events_key)
        
        events = []
        for event_id in event_ids:
            event = self.get_event(event_id.decode('utf-8'))
            if event:
                events.append(event)
        
        return sorted(events, key=lambda x: x['start_time'], reverse=True)
    
    def update_event(self, event_id: str, **kwargs):
        """Update calendar event"""
        event_data = self.get_event(event_id)
        if not event_data:
            return None
        
        event_data.update(kwargs)
        event_data['updated_at'] = datetime.utcnow()
        
        key = self._generate_key('calendar_event', event_id)
        self.redis.setex(key, timedelta(days=90), self._serialize_data(event_data))
        return event_data


def create_redis_managers(redis_client: redis.Redis) -> Dict[str, Any]:
    """Create all Redis data managers"""
    return {
        'user_manager': UserManager(redis_client),
        'session_manager': SessionManager(redis_client),
        'conversation_manager': ConversationManager(redis_client),
        'calendar_event_manager': CalendarEventManager(redis_client)
    }