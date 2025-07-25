# AI Booking Agent

## Overview

The AI Booking Agent is a production-ready Flask-based web application that provides an intelligent calendar management system. It combines natural language processing with Google Calendar integration to allow users to manage their calendar events through conversational AI. The application uses Google's Gemini AI model via LangChain for intent extraction and conversation management, with Redis for data storage, providing users with a seamless booking experience through natural language interactions.

## Recent Changes (January 25, 2025)

✓ **Migrated from PostgreSQL to Redis for data storage** - Complete architectural change to use Redis for sessions, user data, conversations, and calendar events
✓ **Added Redis data managers** - Created comprehensive Redis-based storage with automatic expiration and efficient key management
✓ **Updated session management** - Replaced Flask-Session with Redis-based session service for better scalability
✓ **Created local setup documentation** - Added detailed LOCAL_SETUP.md with step-by-step instructions for running locally

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with blueprint-based modular design
- **Architecture Pattern**: MVC (Model-View-Controller) with clean separation of concerns
- **Data Storage**: Redis with structured data managers for users, sessions, conversations, and calendar events
- **Session Management**: Custom Redis-based session service with automatic expiration
- **CORS Configuration**: Cross-origin support for development and production deployment
- **Proxy Support**: ProxyFix middleware for production deployment compatibility

### Frontend Architecture
- **Technology**: Pure vanilla JavaScript with modern ES6+ features
- **UI Framework**: Bootstrap 5 with dark theme for responsive design
- **HTTP Client**: Fetch API for modern asynchronous communication
- **Modular Design**: Separate JavaScript modules for auth, chat, and app coordination

### AI Integration
- **Primary LLM**: Google Gemini AI for natural language understanding
- **Orchestration**: LangChain for conversation flow and memory management
- **Intent Extraction**: Structured intent parsing with confidence scoring
- **Conversation Memory**: Persistent conversation context across sessions

## Key Components

### Controllers
- **AuthController** (`auth_controller.py`): Manages Google OAuth2 authentication flow
- **BookingController** (`booking_controller.py`): Processes booking requests and coordinates AI with calendar operations
- **APIController** (`api_controller.py`): Provides health checks and session management endpoints

### Models
- **AIModel** (`ai_model.py`): Handles Gemini AI integration and intent extraction
- **CalendarModel** (`calendar_model.py`): Manages Google Calendar API operations and event management

### Services
- **RedisSessionService** (`redis_session_service.py`): Manages user sessions using Redis data managers
- **Redis Data Managers** (`redis_models.py`): Comprehensive Redis storage for users, sessions, conversations, and calendar events

### Frontend Modules
- **App.js**: Main application coordination and initialization
- **Auth.js**: OAuth authentication flow management
- **Chat.js**: Chat interface and conversation handling

## Data Flow

1. **Authentication Flow**: User initiates OAuth → Google authentication → Callback processing → Session creation
2. **Conversation Flow**: User input → Intent extraction via Gemini → Calendar API operations → Response generation
3. **Booking Process**: Natural language request → AI parsing → Conflict checking → Event creation/modification → Confirmation

## External Dependencies

### APIs and Services
- **Google Calendar API**: For calendar event management and conflict detection
- **Google OAuth2**: For secure user authentication and authorization
- **Gemini AI API**: For natural language processing and intent extraction

### Authentication Scopes
- Calendar read access for availability checking
- Calendar events management for booking operations
- Offline access for persistent authentication

### Data Storage Architecture
- **Redis-based storage** with structured key namespacing (`ai_booking:type:identifier`)
- **Automatic expiration**: Sessions (24h), conversations (7 days), calendar events (90 days), users (30 days)
- **Conversation context persistence** across browser sessions with message history
- **OAuth credential management** with secure token refresh handling
- **User profile storage** with Google account integration

## Deployment Strategy

### Environment Configuration
- Environment variables for all sensitive credentials (API keys, OAuth secrets)
- Configurable redirect URIs for different deployment environments
- Secure session configuration with HttpOnly and SameSite cookies

### Production Readiness Features
- ProxyFix middleware for reverse proxy deployment
- CORS configuration supporting multiple origins including Replit
- Comprehensive error handling and logging throughout the application
- Health check endpoint for monitoring

### Security Considerations
- Server-side session storage to prevent client-side token exposure
- Secure cookie configuration with appropriate security flags
- OAuth state parameter validation to prevent CSRF attacks
- Credential refresh handling for long-lived sessions

The application is designed to be deployed on platforms like Replit while maintaining production-grade security and scalability standards.