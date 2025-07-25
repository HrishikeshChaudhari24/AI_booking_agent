import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
import json

logger = logging.getLogger(__name__)

class BookingModel:
    """Model for shared booking operations using Supabase"""
    
    def __init__(self):
        """Initialize Supabase client"""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase: Client = create_client(url, key)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure booking tables exist"""
        try:
            # Create bookings table if it doesn't exist
            # Note: In production, this should be done via Supabase migrations
            # For now, we'll assume the table exists or create it via SQL
            pass
        except Exception as e:
            logger.warning(f"Could not ensure tables: {e}")
    
    def check_time_slot_availability(self, start_time: datetime, end_time: datetime, 
                                   exclude_booking_id: Optional[str] = None) -> bool:
        """Check if a time slot is available across all users"""
        try:
            # Convert to UTC if timezone aware
            if start_time.tzinfo is not None:
                start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
            if end_time.tzinfo is not None:
                end_time = end_time.astimezone(timezone.utc).replace(tzinfo=None)
            
            # Query for overlapping bookings
            query = self.supabase.table('bookings').select('*').eq('status', 'confirmed')
            
            # Check for time overlap
            query = query.or_(
                f"and(start_time.lte.{start_time.isoformat()},end_time.gt.{start_time.isoformat()})"
                f",and(start_time.lt.{end_time.isoformat()},end_time.gte.{end_time.isoformat()})"
                f",and(start_time.gte.{start_time.isoformat()},end_time.lte.{end_time.isoformat()})"
            )
            
            # Exclude specific booking if provided (for updates)
            if exclude_booking_id:
                query = query.neq('id', exclude_booking_id)
            
            result = query.execute()
            
            # If no overlapping bookings found, slot is available
            return len(result.data) == 0
            
        except Exception as e:
            logger.error(f"Failed to check time slot availability: {e}")
            return False
    
    def create_booking(self, user_email: str, title: str, start_time: datetime, 
                      end_time: datetime, description: str = "", 
                      google_event_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new booking"""
        try:
            # Convert to UTC if timezone aware
            if start_time.tzinfo is not None:
                start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
            if end_time.tzinfo is not None:
                end_time = end_time.astimezone(timezone.utc).replace(tzinfo=None)
            
            # Check availability first
            if not self.check_time_slot_availability(start_time, end_time):
                return None
            
            # Calculate duration in minutes
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            booking_data = {
                'user_email': user_email,
                'title': title,
                'description': description,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration_minutes,
                'status': 'confirmed',
                'google_event_id': google_event_id,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('bookings').insert(booking_data).execute()
            
            if result.data:
                logger.info(f"Booking created successfully: {result.data[0]['id']}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create booking: {e}")
            return None
    
    def update_booking(self, booking_id: str, user_email: str, **updates) -> Optional[Dict[str, Any]]:
        """Update an existing booking"""
        try:
            # Check if booking belongs to user
            existing = self.supabase.table('bookings').select('*').eq('id', booking_id).eq('user_email', user_email).execute()
            
            if not existing.data:
                logger.error(f"Booking not found or doesn't belong to user: {booking_id}")
                return None
            
            # If updating time, check availability
            if 'start_time' in updates and 'end_time' in updates:
                start_time = updates['start_time']
                end_time = updates['end_time']
                
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                if not self.check_time_slot_availability(start_time, end_time, booking_id):
                    return None
                
                # Convert to string for database
                updates['start_time'] = start_time.isoformat()
                updates['end_time'] = end_time.isoformat()
                updates['duration_minutes'] = int((end_time - start_time).total_seconds() / 60)
            
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.supabase.table('bookings').update(updates).eq('id', booking_id).execute()
            
            if result.data:
                logger.info(f"Booking updated successfully: {booking_id}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update booking: {e}")
            return None
    
    def cancel_booking(self, booking_id: str, user_email: str) -> bool:
        """Cancel a booking"""
        try:
            result = self.supabase.table('bookings').update({
                'status': 'cancelled',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', booking_id).eq('user_email', user_email).execute()
            
            if result.data:
                logger.info(f"Booking cancelled successfully: {booking_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel booking: {e}")
            return False
    
    def get_user_bookings(self, user_email: str, include_cancelled: bool = False) -> List[Dict[str, Any]]:
        """Get all bookings for a user"""
        try:
            query = self.supabase.table('bookings').select('*').eq('user_email', user_email)
            
            if not include_cancelled:
                query = query.neq('status', 'cancelled')
            
            query = query.order('start_time')
            result = query.execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get user bookings: {e}")
            return []
    
    def get_upcoming_bookings(self, user_email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming bookings for a user"""
        try:
            now = datetime.utcnow().isoformat()
            
            result = self.supabase.table('bookings').select('*').eq('user_email', user_email)\
                .eq('status', 'confirmed').gte('start_time', now)\
                .order('start_time').limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get upcoming bookings: {e}")
            return []
    
    def search_bookings(self, user_email: str, query: str) -> List[Dict[str, Any]]:
        """Search bookings by title or description"""
        try:
            result = self.supabase.table('bookings').select('*').eq('user_email', user_email)\
                .eq('status', 'confirmed')\
                .or_(f"title.ilike.%{query}%,description.ilike.%{query}%")\
                .order('start_time').execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to search bookings: {e}")
            return []
    
    def get_conflicting_bookings(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get all bookings that conflict with the given time range"""
        try:
            # Convert to UTC if timezone aware
            if start_time.tzinfo is not None:
                start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
            if end_time.tzinfo is not None:
                end_time = end_time.astimezone(timezone.utc).replace(tzinfo=None)
            
            # Query for overlapping bookings
            result = self.supabase.table('bookings').select('*').eq('status', 'confirmed')\
                .or_(
                    f"and(start_time.lte.{start_time.isoformat()},end_time.gt.{start_time.isoformat()})"
                    f",and(start_time.lt.{end_time.isoformat()},end_time.gte.{end_time.isoformat()})"
                    f",and(start_time.gte.{start_time.isoformat()},end_time.lte.{end_time.isoformat()})"
                ).order('start_time').execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get conflicting bookings: {e}")
            return []
    
    def find_next_available_slot(self, preferred_start: datetime, duration_minutes: int = 60, 
                               search_days: int = 7) -> Optional[datetime]:
        """Find the next available time slot"""
        try:
            current_time = preferred_start
            end_search = preferred_start + timedelta(days=search_days)
            
            while current_time < end_search:
                end_time = current_time + timedelta(minutes=duration_minutes)
                
                if self.check_time_slot_availability(current_time, end_time):
                    return current_time
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find next available slot: {e}")
            return None