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

-- Create policies for shared booking system
-- Allow anon users to manage bookings for the shared system

-- Allow anyone to view bookings (needed for conflict checking)
CREATE POLICY "Allow read access for conflict checking" ON bookings
    FOR SELECT USING (true);

-- Allow anyone to insert bookings
CREATE POLICY "Allow insert for shared booking" ON bookings
    FOR INSERT WITH CHECK (true);

-- Allow anyone to update bookings
CREATE POLICY "Allow update for shared booking" ON bookings
    FOR UPDATE USING (true);

-- Allow anyone to delete bookings  
CREATE POLICY "Allow delete for shared booking" ON bookings
    FOR DELETE USING (true);

-- Grant necessary permissions to anon and authenticated users
GRANT ALL ON bookings TO anon, authenticated;
GRANT USAGE ON SEQUENCE bookings_id_seq TO anon, authenticated;