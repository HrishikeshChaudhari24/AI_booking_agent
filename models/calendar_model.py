import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class CalendarModel:
    """Model for Google Calendar operations"""
    
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize with user credentials"""
        self.credentials = Credentials.from_authorized_user_info(credentials)
        self.service = None
        self._build_service()
    
    def _build_service(self):
        """Build the Google Calendar service"""
        try:
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            logger.info("Calendar service built successfully")
        except Exception as e:
            logger.error(f"Failed to build calendar service: {e}")
            raise

    @staticmethod
    def _to_rfc3339(dt: datetime) -> str:
        """Return RFC3339 timestamp with timezone. Google Calendar API requires timezone
        information (e.g. "Z" or an offset). If the datetime is naive, assume UTC."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    def get_credentials_dict(self) -> Dict[str, Any]:
        """Get credentials as dictionary for session storage"""
        return {
            'token': self.credentials.token,
            'refresh_token': self.credentials.refresh_token,
            'token_uri': self.credentials.token_uri,
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret,
            'scopes': self.credentials.scopes
        }
    
    def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if the time slot is available"""
        try:
            if not self.service:
                return False
                
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=self._to_rfc3339(start_time),
                timeMax=self._to_rfc3339(end_time),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return len(events) == 0
            
        except HttpError as e:
            logger.error(f"Failed to check availability: {e}")
            return False
    
    def find_next_available_slot(self, preferred_start: datetime, duration_minutes: int = 60) -> Optional[datetime]:
        """Find the next available time slot"""
        try:
            # Check the next 7 days for availability
            current_time = preferred_start
            end_search = preferred_start + timedelta(days=7)
            
            while current_time < end_search:
                end_time = current_time + timedelta(minutes=duration_minutes)
                
                if self.check_availability(current_time, end_time):
                    return current_time
                
                # Move to next hour
                current_time += timedelta(hours=1)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find next available slot: {e}")
            return None
    
    def create_event(self, title: str, start_time: datetime, end_time: datetime, 
                    description: str = "", attendees: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Create a new calendar event"""
        try:
            if not self.service:
                return None
                
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            result = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Event created: {result.get('id')}")
            return result
            
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            return None
    
    def update_event(self, event_id: str, title: Optional[str] = None, start_time: Optional[datetime] = None, 
                    end_time: Optional[datetime] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update an existing event"""
        try:
            if not self.service:
                return None
                
            # Get the existing event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update fields if provided
            if title:
                event['summary'] = title
            if description is not None:
                event['description'] = description
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()
            
            updated_event = self.service.events().update(
                calendarId='primary', 
                eventId=event_id, 
                body=event
            ).execute()
            
            logger.info(f"Event updated: {event_id}")
            return updated_event
            
        except HttpError as e:
            logger.error(f"Failed to update event: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        try:
            if not self.service:
                return False
                
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            logger.info(f"Event deleted: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to delete event: {e}")
            return False
    
    def search_events(self, query: str, time_min: Optional[datetime] = None, time_max: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Search for events by query"""
        try:
            if not self.service:
                return []
                
            if not time_min:
                time_min = datetime.utcnow()
            if not time_max:
                time_max = datetime.utcnow() + timedelta(days=30)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=self._to_rfc3339(time_min),
                timeMax=self._to_rfc3339(time_max),
                q=query,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as e:
            logger.error(f"Failed to search events: {e}")
            return []
    
    def get_upcoming_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming events"""
        try:
            if not self.service:
                return []
                
            now = self._to_rfc3339(datetime.utcnow())
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as e:
            logger.error(f"Failed to get upcoming events: {e}")
            return []
