import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
from google import genai
from google.genai import types
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)

class BookingIntent(BaseModel):
    """Structured booking intent from AI"""
    action: str  # 'create', 'reschedule', 'cancel', 'query'
    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[int] = 60  # minutes
    description: Optional[str] = None
    attendees: Optional[List[str]] = None
    event_id: Optional[str] = None
    confidence: float = 0.0

class AIModel:
    """Model for AI operations using Gemini and LangChain"""
    
    def __init__(self):
        """Initialize the AI model"""
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.memory = ConversationBufferMemory(return_messages=True)
        
    def extract_booking_intent(self, user_message: str, context: str = "") -> BookingIntent:
        """Extract booking intent from user message using Gemini"""
        try:
            system_prompt = """
            You are an AI booking assistant. Analyze the user's message and extract booking information.
            
            Determine the action: 'create', 'reschedule', 'cancel', or 'query'
            Extract details like title, date, time, duration, description, and attendees.
            
            For dates:
            - "today" should remain as "today" 
            - "tomorrow" should be converted to next day in YYYY-MM-DD format
            - Specific dates should be in YYYY-MM-DD format
            
            For times:
            - Keep original format (7pm, 7:00 PM, 19:00) - DO NOT convert to 24-hour
            - Preserve AM/PM indicators when present
            - If no AM/PM specified for times 1-12, assume user's intended time
            
            For queries about "appointments", "meetings", "events" - use action "query"
            
            If information is missing or unclear, set confidence lower.
            
            Return JSON matching this structure:
            {
                "action": "create|reschedule|cancel|query",
                "title": "event title or inferred title",
                "date": "today|YYYY-MM-DD or null",
                "time": "original format (7pm, 2:30 PM, etc.) or null", 
                "duration": 60,
                "description": "event description or null",
                "attendees": ["email1@example.com"] or null,
                "event_id": "event_id for reschedule/cancel or null",
                "confidence": 0.8
            }
            """
            
            user_prompt = f"""
            Context: {context}
            User message: {user_message}
            
            Current date: {datetime.now().strftime('%Y-%m-%d')}
            Current time: {datetime.now().strftime('%H:%M')}
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=BookingIntent,
                ),
            )
            
            if response.text:
                data = json.loads(response.text)
                return BookingIntent(**data)
            else:
                raise ValueError("Empty response from AI model")
                
        except Exception as e:
            logger.error(f"Failed to extract booking intent: {e}")
            # Return default intent on error
            return BookingIntent(
                action="query",
                title="",
                confidence=0.0
            )
    
    def generate_response(self, user_message: str, booking_result: Optional[Dict[str, Any]] = None, 
                         context: str = "") -> str:
        """Generate natural language response"""
        try:
            # Get conversation history
            history = self.memory.chat_memory.messages
            conversation_context = ""
            
            for msg in history[-4:]:  # Last 4 messages for context
                if isinstance(msg, HumanMessage):
                    conversation_context += f"User: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    conversation_context += f"Assistant: {msg.content}\n"
            
            system_prompt = """
            You are a friendly and professional AI booking assistant. 
            
            Respond naturally to the user's booking request. 
            If booking was successful, provide confirmation details.
            If there were conflicts, suggest alternatives.
            If information is missing, ask clarifying questions.
            
            Keep responses concise but informative.
            Always be helpful and professional.
            """
            
            user_prompt = f"""
            Conversation history:
            {conversation_context}
            
            Current user message: {user_message}
            
            Booking result: {json.dumps(booking_result) if booking_result else 'No booking operation performed'}
            
            Additional context: {context}
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            
            ai_response = response.text or "I'm sorry, I couldn't process your request right now."
            
            # Store in memory
            self.memory.chat_memory.add_user_message(user_message)
            self.memory.chat_memory.add_ai_message(ai_response)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."
    
    def suggest_alternatives(self, preferred_datetime: datetime, conflicts: List[Dict[str, Any]]) -> str:
        """Suggest alternative times when there are conflicts"""
        try:
            conflict_info = ""
            for conflict in conflicts:
                start = conflict.get('start', {}).get('dateTime', '')
                summary = conflict.get('summary', 'Busy')
                conflict_info += f"- {summary} at {start}\n"
            
            prompt = f"""
            The user wanted to schedule something for {preferred_datetime.strftime('%Y-%m-%d at %H:%M')}, 
            but there are conflicts:
            
            {conflict_info}
            
            Suggest 2-3 alternative times that would work better. 
            Be specific about dates and times.
            Consider typical business hours and reasonable scheduling.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            return response.text or "I can suggest alternative times if you'd like."
            
        except Exception as e:
            logger.error(f"Failed to suggest alternatives: {e}")
            return "Let me help you find an alternative time that works better."
    
    def parse_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse date and time strings into datetime object with proper timezone handling"""
        try:
            if not date_str or not time_str:
                return None
                
            # Handle "today" keyword
            if date_str.lower() == 'today':
                date_obj = datetime.now().date()
            else:
                # Parse date
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Parse time - handle both 12hr and 24hr formats
            time_str = time_str.strip().lower()
            
            # Convert 12-hour format to 24-hour
            if 'pm' in time_str:
                time_str = time_str.replace('pm', '').strip()
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':'))
                else:
                    hour, minute = int(time_str), 0
                if hour != 12:
                    hour += 12
                time_obj = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M').time()
            elif 'am' in time_str:
                time_str = time_str.replace('am', '').strip()
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':'))
                else:
                    hour, minute = int(time_str), 0
                if hour == 12:
                    hour = 0
                time_obj = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M').time()
            else:
                # Handle formats like "7pm", "19", "19:00"
                if time_str.endswith('pm'):
                    time_str = time_str[:-2].strip()
                    if ':' in time_str:
                        hour, minute = map(int, time_str.split(':'))
                    else:
                        hour, minute = int(time_str), 0
                    if hour != 12:
                        hour += 12
                    time_obj = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M').time()
                elif time_str.endswith('am'):
                    time_str = time_str[:-2].strip()
                    if ':' in time_str:
                        hour, minute = map(int, time_str.split(':'))
                    else:
                        hour, minute = int(time_str), 0
                    if hour == 12:
                        hour = 0
                    time_obj = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M').time()
                else:
                    # Assume 24-hour format or plain number
                    if ':' in time_str:
                        time_obj = datetime.strptime(time_str, '%H:%M').time()
                    else:
                        # Single number - could be hour (assume PM if 1-12, otherwise 24hr)
                        hour = int(time_str)
                        if 1 <= hour <= 12:
                            # Assume PM for afternoon hours if no AM/PM specified
                            hour = hour + 12 if hour != 12 else hour
                        time_obj = datetime.strptime(f"{hour:02d}:00", '%H:%M').time()
            
            # Combine date and time
            dt = datetime.combine(date_obj, time_obj)
            
            # Ensure UTC timezone for Google Calendar API
            from datetime import timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            return dt
            
        except Exception as e:
            logger.error(f"Failed to parse datetime: {e}")
            return None
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        try:
            history = self.memory.chat_memory.messages
            if not history:
                return ""
                
            conversation_text = ""
            for msg in history:
                if isinstance(msg, HumanMessage):
                    conversation_text += f"User: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    conversation_text += f"Assistant: {msg.content}\n"
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Summarize this conversation briefly:\n\n{conversation_text}"
            )
            
            return response.text or ""
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return ""
