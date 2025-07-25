import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, session, jsonify
from models.calendar_model import CalendarModel
from models.ai_model import AIModel
from models.booking_model import BookingModel
from services.session_service import SessionService

logger = logging.getLogger(__name__)

booking_bp = Blueprint('booking', __name__)

def get_calendar_model() -> CalendarModel:
    """Get calendar model instance for current user"""
    if 'google_credentials' not in session:
        raise ValueError("User not authenticated")
    
    return CalendarModel(session['google_credentials'])

def get_ai_model() -> AIModel:
    """Get AI model instance"""
    return AIModel()

def get_booking_model() -> BookingModel:
    """Get booking model instance"""
    try:
        return BookingModel()
    except ValueError as e:
        logger.error(f"Failed to initialize booking model: {e}")
        raise

@booking_bp.route('/process', methods=['POST'])
def process_booking_request():
    """Process natural language booking request"""
    try:
        # Check authentication
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get models
        ai_model = get_ai_model()
        calendar_model = get_calendar_model()
        booking_model = get_booking_model()
        
        # Get conversation context
        context = SessionService.get_conversation_context(session.get('session_id', ''))
        
        # Extract intent using AI
        intent = ai_model.extract_booking_intent(user_message, context)
        logger.info(f"Extracted intent: {intent.dict()}")
        
        booking_result = None
        
        # Get user email for booking system
        user_email = session.get('user_email', 'anonymous@example.com')
        
        # Process based on intent
        if intent.action == 'create':
            booking_result = handle_create_event(calendar_model, booking_model, intent, user_email)
        elif intent.action == 'reschedule':
            booking_result = handle_reschedule_event(calendar_model, intent)
        elif intent.action == 'cancel':
            booking_result = handle_cancel_event(calendar_model, intent)
        elif intent.action == 'query':
            booking_result = handle_query_events(calendar_model, booking_model, intent, user_email)
        else:
            booking_result = {'error': 'Unknown action requested'}
        
        # Generate AI response
        ai_response = ai_model.generate_response(
            user_message, 
            booking_result, 
            context
        )
        
        # Store conversation context
        SessionService.store_conversation_context(
            session.get('session_id', ''), 
            user_message, 
            ai_response,
            intent.dict()
        )
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'intent': intent.dict(),
            'booking_result': booking_result
        })
        
    except ValueError as e:
        logger.error(f"Booking request error: {e}")
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Booking request error: {e}")
        return jsonify({'error': 'Failed to process booking request'}), 500

def handle_create_event(calendar_model: CalendarModel, booking_model: BookingModel, intent, user_email: str) -> dict:
    """Handle event creation"""
    try:
        if not intent.title:
            return {'error': 'Event title is required'}
        
        if not intent.date or not intent.time:
            return {'error': 'Date and time are required for creating events'}
        
        # Parse datetime
        ai_model = get_ai_model()
        start_datetime = ai_model.parse_datetime(intent.date, intent.time)
        if not start_datetime:
            return {'error': 'Invalid date or time format'}
        
        end_datetime = start_datetime + timedelta(minutes=intent.duration or 60)
        
        # Check availability in shared booking system first
        if not booking_model.check_time_slot_availability(start_datetime, end_datetime):
            # Get conflicting bookings from shared system
            conflicts = booking_model.get_conflicting_bookings(start_datetime, end_datetime)
            alternative = booking_model.find_next_available_slot(start_datetime, intent.duration or 60)
            
            conflict_details = []
            for conflict in conflicts:
                conflict_details.append(f"- {conflict.get('title', 'Appointment')} from {conflict.get('start_time')} to {conflict.get('end_time')}")
            
            conflict_message = "\n".join(conflict_details) if conflict_details else "Time slot is already booked by another user."
            
            return {
                'conflict': True,
                'message': f"Time slot not available. Conflicting bookings:\n{conflict_message}",
                'alternative_time': alternative.isoformat() if alternative else None,
                'conflicts': conflicts
            }
        
        # Also check user's personal Google Calendar
        if not calendar_model.check_availability(start_datetime, end_datetime):
            # Find alternative slots
            alternative = calendar_model.find_next_available_slot(start_datetime, intent.duration or 60)
            conflicts = []
            if calendar_model.service:
                conflicts = calendar_model.service.events().list(
                    calendarId='primary',
                    timeMin=start_datetime.isoformat(),
                    timeMax=end_datetime.isoformat(),
                    singleEvents=True
                ).execute().get('items', [])
            
            suggestion = ai_model.suggest_alternatives(start_datetime, conflicts)
            
            return {
                'conflict': True,
                'message': f"Time slot is not available. {suggestion}",
                'alternative_time': alternative.isoformat() if alternative else None,
                'conflicts': conflicts
            }
        
        # Create event in Google Calendar
        event = calendar_model.create_event(
            title=intent.title,
            start_time=start_datetime,
            end_time=end_datetime,
            description=intent.description or "",
            attendees=intent.attendees or []
        )
        
        if event:
            # Also create booking in shared system
            booking = booking_model.create_booking(
                user_email=user_email,
                title=intent.title,
                start_time=start_datetime,
                end_time=end_datetime,
                description=intent.description or "",
                google_event_id=event.get('id')
            )
            
            if booking:
                return {
                    'success': True,
                    'event': event,
                    'booking': booking,
                    'message': f"Appointment '{intent.title}' booked successfully for {intent.duration or 60} minutes",
                    'calendar_link': f"https://calendar.google.com/calendar/event?eid={event.get('id', '')}"
                }
            else:
                # If shared booking fails, try to clean up the Google Calendar event
                try:
                    event_id = event.get('id')
                    if event_id:
                        calendar_model.delete_event(event_id)
                except:
                    pass
                return {'error': 'Failed to secure booking in shared system'}
        else:
            return {'error': 'Failed to create calendar event'}
            
    except Exception as e:
        logger.error(f"Create event error: {e}")
        return {'error': 'Failed to create event'}

def handle_reschedule_event(calendar_model: CalendarModel, intent) -> dict:
    """Handle event rescheduling"""
    try:
        if not intent.event_id and not intent.title:
            return {'error': 'Event ID or title is required for rescheduling'}
        
        # Find event if only title provided
        if not intent.event_id and intent.title:
            events = calendar_model.search_events(intent.title)
            if not events:
                return {'error': f"No event found with title '{intent.title}'"}
            intent.event_id = events[0]['id']
        
        if not intent.date or not intent.time:
            return {'error': 'New date and time are required for rescheduling'}
        
        # Parse new datetime
        ai_model = get_ai_model()
        new_start = ai_model.parse_datetime(intent.date, intent.time)
        if not new_start:
            return {'error': 'Invalid date or time format'}
        
        new_end = new_start + timedelta(minutes=intent.duration or 60)
        
        # Check availability for new time
        if not calendar_model.check_availability(new_start, new_end):
            alternative = calendar_model.find_next_available_slot(new_start, intent.duration or 60)
            return {
                'conflict': True,
                'message': 'New time slot is not available',
                'alternative_time': alternative.isoformat() if alternative else None
            }
        
        # Update event
        updated_event = calendar_model.update_event(
            event_id=intent.event_id,
            title=intent.title,
            start_time=new_start,
            end_time=new_end,
            description=intent.description
        )
        
        if updated_event:
            return {
                'success': True,
                'event': updated_event,
                'message': f"Event rescheduled successfully to {intent.date} at {intent.time}"
            }
        else:
            return {'error': 'Failed to reschedule event'}
            
    except Exception as e:
        logger.error(f"Reschedule event error: {e}")
        return {'error': 'Failed to reschedule event'}

def handle_cancel_event(calendar_model: CalendarModel, intent) -> dict:
    """Handle event cancellation"""
    try:
        if not intent.event_id and not intent.title:
            return {'error': 'Event ID or title is required for cancellation'}
        
        # Find event if only title provided
        if not intent.event_id and intent.title:
            events = calendar_model.search_events(intent.title)
            if not events:
                return {'error': f"No event found with title '{intent.title}'"}
            intent.event_id = events[0]['id']
        
        # Delete event
        success = calendar_model.delete_event(intent.event_id)
        
        if success:
            return {
                'success': True,
                'message': f"Event cancelled successfully"
            }
        else:
            return {'error': 'Failed to cancel event'}
            
    except Exception as e:
        logger.error(f"Cancel event error: {e}")
        return {'error': 'Failed to cancel event'}

def handle_query_events(calendar_model: CalendarModel, booking_model: BookingModel, intent, user_email: str) -> dict:
    """Handle event queries"""
    try:
        # Get events from both sources
        if intent.title:
            # Search for specific events in shared bookings
            shared_bookings = booking_model.search_bookings(user_email, intent.title)
            # Also search in Google Calendar
            calendar_events = calendar_model.search_events(intent.title)
        else:
            # Get upcoming events from shared bookings
            shared_bookings = booking_model.get_upcoming_bookings(user_email, 10)
            # Also get from Google Calendar
            calendar_events = calendar_model.get_upcoming_events(10)
        
        # Combine and format events
        all_events = []
        
        # Add shared bookings
        for booking in shared_bookings:
            all_events.append({
                'id': booking.get('id'),
                'summary': booking.get('title'),
                'description': booking.get('description', ''),
                'start': {'dateTime': booking.get('start_time')},
                'end': {'dateTime': booking.get('end_time')},
                'source': 'shared_booking',
                'duration_minutes': booking.get('duration_minutes', 60)
            })
        
        # Add Google Calendar events (avoid duplicates)
        google_event_ids = [b.get('google_event_id') for b in shared_bookings if b.get('google_event_id')]
        for event in calendar_events:
            if event.get('id') not in google_event_ids:
                all_events.append({
                    **event,
                    'source': 'google_calendar'
                })
        
        # Sort by start time
        all_events.sort(key=lambda x: x.get('start', {}).get('dateTime', ''))
        
        return {
            'success': True,
            'events': all_events,
            'message': f"Found {len(all_events)} appointments"
        }
        
    except Exception as e:
        logger.error(f"Query events error: {e}")
        return {'error': 'Failed to query events'}

@booking_bp.route('/events')
def get_events():
    """Get upcoming events"""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        
        calendar_model = get_calendar_model()
        events = calendar_model.get_upcoming_events(20)
        
        return jsonify({
            'success': True,
            'events': events
        })
        
    except Exception as e:
        logger.error(f"Get events error: {e}")
        return jsonify({'error': 'Failed to get events'}), 500

@booking_bp.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    try:
        ai_model = get_ai_model()
        ai_model.clear_memory()
        
        SessionService.clear_conversation_context(session.get('session_id', ''))
        
        return jsonify({
            'success': True,
            'message': 'Conversation cleared'
        })
        
    except Exception as e:
        logger.error(f"Clear conversation error: {e}")
        return jsonify({'error': 'Failed to clear conversation'}), 500
