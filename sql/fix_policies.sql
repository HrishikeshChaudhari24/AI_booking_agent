-- Fix Supabase RLS policies for shared booking system
-- Run this in your Supabase SQL Editor to fix the booking issues

-- First, drop any existing restrictive policies
DROP POLICY IF EXISTS "Users can view their own bookings" ON bookings;
DROP POLICY IF EXISTS "Users can insert their own bookings" ON bookings;
DROP POLICY IF EXISTS "Users can update their own bookings" ON bookings;
DROP POLICY IF EXISTS "Users can delete their own bookings" ON bookings;

-- Create new open policies for shared booking system
CREATE POLICY "Allow read access for conflict checking" ON bookings
    FOR SELECT USING (true);

CREATE POLICY "Allow insert for shared booking" ON bookings
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow update for shared booking" ON bookings
    FOR UPDATE USING (true);

CREATE POLICY "Allow delete for shared booking" ON bookings
    FOR DELETE USING (true);

-- Grant necessary permissions
GRANT ALL ON bookings TO anon, authenticated;

-- If you get an error about sequence, also run:
-- GRANT USAGE ON SEQUENCE bookings_id_seq TO anon, authenticated;