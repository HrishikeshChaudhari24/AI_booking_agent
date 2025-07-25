# AI Booking Agent - Local Setup Instructions

## Overview
This guide will help you run the AI Booking Agent application locally on your machine. The application now uses Redis for data storage instead of PostgreSQL.

## Prerequisites

### Required Software
1. **Python 3.11 or higher**
   - Download from: https://www.python.org/downloads/

2. **Redis Server**
   - **macOS**: `brew install redis`
   - **Ubuntu/Debian**: `sudo apt-get install redis-server`
   - **Windows**: Download from https://redis.io/download
   - **Docker**: `docker run -d -p 6379:6379 redis:alpine`

3. **Git**
   - Download from: https://git-scm.com/downloads

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd ai-booking-agent
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Redis Server
```bash
# Start Redis server (choose one method)

# Method 1: Direct command
redis-server

# Method 2: Background service
# macOS with Homebrew:
brew services start redis

# Ubuntu/Debian:
sudo systemctl start redis-server

# Method 3: Docker
docker run -d -p 6379:6379 --name redis-ai-booking redis:alpine
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your values:
```env
# Required: Session security
SESSION_SECRET=your-super-secret-session-key-here

# Required: Google OAuth credentials  
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Required: Gemini AI API key
GEMINI_API_KEY=your-gemini-api-key

# Optional: Redis configuration (defaults to local)
REDIS_URL=redis://localhost:6379/0

# Optional: Flask environment
FLASK_ENV=development
FLASK_DEBUG=true
```

### 5. Set Up Google Calendar API

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Calendar API

#### Step 2: Create OAuth 2.0 Credentials
1. Go to "Credentials" in the Google Cloud Console
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URI: `http://localhost:5000/auth/callback`
5. Download the credentials JSON file

#### Step 3: Get Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key for Gemini
3. Add it to your `.env` file

### 6. Run the Application
```bash
# Make sure Redis is running first
redis-cli ping  # Should return "PONG"

# Start the Flask application
python main.py

# Or use gunicorn for production-like testing
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

The application will be available at: http://localhost:5000

## Verification Steps

### 1. Check Redis Connection
```bash
# Test Redis is working
redis-cli ping  # Should return "PONG"

# Check if app data is being stored
redis-cli keys "ai_booking:*"
```

### 2. Test Application Features
1. **Home Page**: Visit http://localhost:5000
2. **Google Auth**: Click "Connect Google Calendar"
3. **AI Chat**: Try sending a message like "Schedule a meeting tomorrow at 2 PM"

## Common Issues & Solutions

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it:
redis-server

# Check Redis logs:
tail -f /var/log/redis/redis-server.log  # Linux
tail -f /usr/local/var/log/redis.log     # macOS
```

### Python Dependencies
```bash
# If packages are missing:
pip install --upgrade pip
pip install -r requirements.txt

# For specific Redis packages:
pip install redis flask-redis
```

### Google OAuth Issues
- Ensure redirect URI matches exactly: `http://localhost:5000/auth/callback`
- Check that Google Calendar API is enabled
- Verify client ID and secret are correct
- Make sure credentials.json is in the project root

### Port Conflicts
If port 5000 is in use:
```bash
# Find what's using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Run on different port
python main.py --port 5001
```

## Development Commands

### View Redis Data
```bash
# Connect to Redis CLI
redis-cli

# View all AI Booking keys
KEYS ai_booking:*

# View specific user data
GET ai_booking:user:your-user-id

# View session data
GET ai_booking:session:session-id

# Clear all data (careful!)
FLUSHDB
```

### Application Logs
The application logs to console. For production:
```bash
# Redirect logs to file
python main.py > app.log 2>&1

# Or use gunicorn with logging
gunicorn --bind 0.0.0.0:5000 --log-file app.log --log-level debug main:app
```

## Data Storage Structure

The application stores data in Redis with these key patterns:
- `ai_booking:user:{user_id}` - User profiles and OAuth tokens
- `ai_booking:session:{session_id}` - User sessions
- `ai_booking:conversation:{conversation_id}` - Chat history
- `ai_booking:calendar_event:{event_id}` - Calendar events created by AI

## Next Steps

Once running locally:
1. Test the Google Calendar integration
2. Try various natural language booking requests
3. Check Redis data storage using the CLI commands above
4. Customize the AI responses and booking logic as needed

## Support

If you encounter issues:
1. Check the console logs for error messages
2. Verify all environment variables are set correctly
3. Ensure Redis is running and accessible
4. Test Google OAuth setup in a private browser window