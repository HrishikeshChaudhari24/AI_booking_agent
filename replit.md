# AI Booking Agent

## Overview

The AI Booking Agent is a production-ready Flask-based web application that provides an intelligent calendar management system. It combines natural language processing with Google Calendar integration to allow users to manage their calendar events through conversational AI. The application uses Google's Gemini AI model via LangChain for intent extraction and conversation management, with Redis for data storage, providing users with a seamless booking experience through natural language interactions.

## Recent Changes (July 25, 2025)

✓ **Migrated to Replit environment** - Successfully adapted from Replit Agent to standard Replit deployment
✓ **Added Supabase shared booking system** - Prevents double-booking across all users with variable duration support
✓ **Fixed time zone parsing issues** - Proper handling of user input like "7pm today" converts correctly to 19:00
✓ **Enhanced conflict detection** - Shows conflicting bookings and suggests alternative time slots
✓ **Integrated dual storage** - Uses both Supabase (shared bookings) and Google Calendar (personal events)
✓ **Added user email tracking** - Proper user identification for multi-user booking system
✓ **Created setup documentation** - SUPABASE_SETUP.md with simple SQL setup instructions

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
- **Supabase PostgreSQL** for shared booking management with conflict prevention
- **Google Calendar API** for personal calendar integration and event synchronization
- **Session storage** via filesystem (Redis fallback) for user authentication
- **Row Level Security (RLS)** ensures users only access their own bookings
- **Dual storage sync** - bookings stored in both Supabase and Google Calendar
- **OAuth credential management** with secure token refresh handling
- **User email tracking** for multi-user booking identification

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