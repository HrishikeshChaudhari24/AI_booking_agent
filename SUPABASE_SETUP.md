# Supabase Setup for Shared Booking System

## Quick Setup

1. **Go to your Supabase project dashboard**
2. **Open the SQL Editor** (left sidebar)
3. **Copy and paste the SQL from `sql/create_tables.sql`** and run it
4. **Done!** Your shared booking system is ready

## What This Creates

The setup creates a `bookings` table that prevents double-booking across all users:

### Features
- ✅ **Shared time slot management** - No two users can book the same time
- ✅ **Variable duration support** - Users can book for 30 minutes, 2 hours, etc.
- ✅ **Conflict detection** - Shows who has booked conflicting times
- ✅ **Google Calendar sync** - Links to user's personal calendar events
- ✅ **User isolation** - Users only see their own bookings for privacy

### How It Works

1. **User books appointment**: "I want to book for today 7pm for 2 hours"
2. **System checks**: Supabase database for any existing bookings from 7pm-9pm
3. **If available**: Creates booking in both Supabase and user's Google Calendar
4. **If conflict**: Shows the conflicting booking and suggests alternatives
5. **Subsequent users**: Cannot book overlapping times until the slot is free

## Example Usage

```
User A: "Book meeting for today 3pm"
✅ Books 3:00-4:00 PM successfully

User B: "Book appointment for today 3:30pm" 
❌ Conflict detected: "Time slot not available. Conflicting bookings:
- Meeting from 2025-07-25 15:00:00 to 2025-07-25 16:00:00"

User B: "Book appointment for today 4pm"
✅ Books 4:00-5:00 PM successfully (no conflict)
```

## Database Schema

```sql
bookings (
  id UUID PRIMARY KEY,
  user_email VARCHAR(255),     -- Who booked it
  title VARCHAR(500),          -- "Meeting", "Appointment", etc.
  start_time TIMESTAMP,        -- When it starts
  end_time TIMESTAMP,          -- When it ends  
  duration_minutes INTEGER,    -- How long (for easy queries)
  status VARCHAR(50),          -- 'confirmed', 'cancelled'
  google_event_id VARCHAR(255) -- Link to Google Calendar event
)
```

## Security & Privacy

- **Row Level Security (RLS)** enabled
- Users can only see/edit their own bookings
- Conflict checking works without exposing other users' details
- All times stored in UTC for consistency

Your shared booking system is now ready! Users can book appointments without conflicts, and the system will automatically prevent double-booking.