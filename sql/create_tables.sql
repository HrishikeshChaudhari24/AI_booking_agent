-- Create bookings table in Supabase
-- Run this in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS bookings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled', 'pending')),
    google_event_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bookings_user_email ON bookings(user_email);
CREATE INDEX IF NOT EXISTS idx_bookings_start_time ON bookings(start_time);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_time_range ON bookings(start_time, end_time);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_bookings_updated_at 
    BEFORE UPDATE ON bookings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

-- Create policy so users can only see their own bookings
-- Note: For shared booking system, you might want to adjust this
CREATE POLICY "Users can view their own bookings" ON bookings
    FOR SELECT USING (auth.email() = user_email);

CREATE POLICY "Users can insert their own bookings" ON bookings
    FOR INSERT WITH CHECK (auth.email() = user_email);

CREATE POLICY "Users can update their own bookings" ON bookings
    FOR UPDATE USING (auth.email() = user_email);

CREATE POLICY "Users can delete their own bookings" ON bookings
    FOR DELETE USING (auth.email() = user_email);

-- For the shared booking conflict checking, create a public view
-- that allows checking time conflicts without exposing user details
CREATE OR REPLACE VIEW booking_time_slots AS
SELECT 
    id,
    start_time,
    end_time,
    duration_minutes,
    status
FROM bookings
WHERE status = 'confirmed';

-- Allow public access to the view for conflict checking
GRANT SELECT ON booking_time_slots TO anon, authenticated;