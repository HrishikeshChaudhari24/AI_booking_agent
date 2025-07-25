"""
User database models for the AI Booking Agent application
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

def create_user_models(db):
    """Create user models with the given database instance"""
    
    class User(UserMixin, db.Model):
        """User model for storing user authentication and profile data"""
        __tablename__ = 'users'
        
        id = db.Column(db.String(100), primary_key=True)  # Google user ID
        email = db.Column(db.String(255), unique=True, nullable=False)
        name = db.Column(db.String(255), nullable=True)
        picture_url = db.Column(db.String(500), nullable=True)
        
        # OAuth tokens
        access_token = db.Column(db.Text, nullable=True)
        refresh_token = db.Column(db.Text, nullable=True)
        token_expires_at = db.Column(db.DateTime, nullable=True)
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        last_login = db.Column(db.DateTime, nullable=True)
        
        def __repr__(self):
            return f'<User {self.email}>'
        
        def get_id(self):
            return str(self.id)

    class Conversation(db.Model):
        """Model for storing conversation history with the AI assistant"""
        __tablename__ = 'conversations'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
        session_id = db.Column(db.String(255), nullable=False)
        
        # Conversation data
        messages = db.Column(db.Text, nullable=False)  # JSON string of message history
        context = db.Column(db.Text, nullable=True)    # JSON string of conversation context
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<Conversation {self.id} for user {self.user_id}>'

    class CalendarEvent(db.Model):
        """Model for tracking calendar events created by the AI assistant"""
        __tablename__ = 'calendar_events'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
        google_event_id = db.Column(db.String(255), nullable=False)
        
        # Event details
        title = db.Column(db.String(500), nullable=False)
        description = db.Column(db.Text, nullable=True)
        start_time = db.Column(db.DateTime, nullable=False)
        end_time = db.Column(db.DateTime, nullable=False)
        location = db.Column(db.String(500), nullable=True)
        attendees = db.Column(db.Text, nullable=True)  # JSON string of attendee emails
        
        # AI assistant metadata
        intent_confidence = db.Column(db.String(50), nullable=True)  # high, medium, low
        created_by_ai = db.Column(db.Boolean, default=True)
        modification_type = db.Column(db.String(50), nullable=True)  # create, update, delete
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<CalendarEvent {self.title} for user {self.user_id}>'

    class UserSession(db.Model):
        """Model for managing user sessions and conversation state"""
        __tablename__ = 'user_sessions'
        
        id = db.Column(db.Integer, primary_key=True)
        session_id = db.Column(db.String(255), unique=True, nullable=False)
        user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=True)
        
        # Session data
        data = db.Column(db.Text, nullable=True)  # JSON string of session data
        conversation_context = db.Column(db.Text, nullable=True)  # Current conversation context
        
        # Session metadata
        ip_address = db.Column(db.String(45), nullable=True)
        user_agent = db.Column(db.String(500), nullable=True)
        is_authenticated = db.Column(db.Boolean, default=False)
        
        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        expires_at = db.Column(db.DateTime, nullable=True)
        
        def __repr__(self):
            return f'<UserSession {self.session_id}>'

    return {
        'User': User,
        'Conversation': Conversation,
        'CalendarEvent': CalendarEvent,
        'UserSession': UserSession
    }