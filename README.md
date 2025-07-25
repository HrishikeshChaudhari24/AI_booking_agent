# AI Booking Agent

A production-ready AI-powered booking assistant that integrates with Google Calendar using natural language processing. Built with Flask, LangChain, and Gemini AI.

## Features

- **Natural Language Interface**: Chat with the AI in plain English to manage your calendar
- **Google Calendar Integration**: Secure OAuth2 connection to your Google Calendar
- **Smart Scheduling**: Automatic conflict detection with alternative time suggestions
- **AI-Powered**: Uses Gemini LLM via LangChain for intent extraction and conversation management
- **Real-time Chat**: Interactive chat interface with typing indicators and rich responses
- **Secure Sessions**: Cookie-based authentication with server-side session storage
- **MVC Architecture**: Clean separation of concerns with organized codebase

## Tech Stack

### Backend
- **Flask**: Web framework with RESTful API endpoints
- **LangChain**: AI orchestration and conversation memory
- **Gemini AI**: Natural language processing and intent extraction
- **Google Calendar API**: Event management and calendar operations
- **Flask-Session**: Secure server-side session management
- **Flask-CORS**: Cross-origin request handling

### Frontend
- **Vanilla JavaScript**: Pure JS for maximum compatibility
- **Bootstrap 5**: Responsive UI with dark theme
- **Font Awesome**: Icons and visual elements
- **Fetch API**: Modern HTTP client for API communication

## Setup Instructions

### 1. Environment Setup

1. Clone or download the project files
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. Generate a session secret:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

### 2. Google OAuth Setup

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Calendar API

2. **Create OAuth Credentials**:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: "Web application"
   - Add authorized redirect URI: `https://your-replit-url.replit.dev/auth/callback`
   - Download the `credentials.json` file

3. **Extract Credentials**:
   ```bash
   python setup_credentials.py
   ```

### 3. Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to Replit Secrets as `GEMINI_API_KEY`

### 4. Environment Variables

Add these to Replit Secrets:
```
SESSION_SECRET=your-generated-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GEMINI_API_KEY=your-gemini-api-key
```

## Running the Application

1. **Start the server**:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reload main:app
   ```

2. **Access the application**:
   - Open your Replit URL in a browser
   - Click "Connect Google Calendar" to authenticate
   - Start chatting with the AI assistant

## Usage Examples

### Scheduling Events
- "Schedule a team meeting tomorrow at 2 PM"
- "Book a client call for Friday afternoon"
- "Set up a project review next Tuesday at 10 AM with john@company.com"

### Managing Events
- "Reschedule my meeting to 3 PM"
- "Cancel the team standup tomorrow"
- "Show me my meetings for next week"
- "What's on my calendar today?"

## Deployment Guide

### Prerequisites
1. Create a Google Cloud project and OAuth 2.0 credentials.
2. Obtain a Gemini API key.
3. Provision a Redis instance (or use Render/Heroku add-on).
4. Set the environment variables listed in `.env.example`.

### One-click Deploy on Render
```bash
# From your repository root (already pushed to GitHub)
# Render will automatically detect the build
```
1. Create a new **Web Service** from this repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app -b 0.0.0.0:$PORT`
4. Add a Redis add-on.
5. Add env vars.

### Docker / Cloud Run
```bash
docker build -t ai-booking:latest .

docker run -p 8080:8080 --env-file .env ai-booking:latest
```

### Heroku/Railway
```
heroku create ai-booking-agent
heroku addons:create heroku-redis:hobby-dev
heroku config:set $(cat .env | xargs)

git push heroku main
```
   