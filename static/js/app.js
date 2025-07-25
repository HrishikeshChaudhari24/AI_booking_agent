/**
 * Main application JavaScript
 * Handles initialization and coordination between modules
 */

class AIBookingApp {
    constructor() {
        this.isInitialized = false;
        this.sessionId = null;
        this.authenticated = false;
        
        // Bind methods
        this.init = this.init.bind(this);
        this.handleAuthStatus = this.handleAuthStatus.bind(this);
        this.showError = this.showError.bind(this);
        this.showSuccess = this.showSuccess.bind(this);
    }
    
    async init() {
        try {
            console.log('Initializing AI Booking App...');
            
            // Show loading state
            this.showLoadingState();
            
            // Create session if needed
            await this.createSession();
            
            // Check authentication status
            await this.checkAuthStatus();
            
            // Initialize modules
            this.initializeAuth();
            this.initializeChat();
            
            // Setup global error handling
            this.setupErrorHandling();
            
            this.isInitialized = true;
            console.log('AI Booking App initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to initialize the application. Please refresh the page.');
        } finally {
            this.hideLoadingState();
        }
    }
    
    async createSession() {
        try {
            const response = await fetch('/api/session', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                console.log('Session created:', this.sessionId);
            }
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    }
    
    async checkAuthStatus() {
        try {
            const response = await fetch('/auth/status', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handleAuthStatus(data);
            } else {
                this.handleAuthStatus({ authenticated: false });
            }
        } catch (error) {
            console.error('Failed to check auth status:', error);
            this.handleAuthStatus({ authenticated: false });
        }
    }
    
    handleAuthStatus(authData) {
        this.authenticated = authData.authenticated;
        
        // Update UI based on auth status
        const loginSection = document.getElementById('login-section');
        const chatSection = document.getElementById('chat-section');
        const authStatus = document.getElementById('auth-status');
        
        if (this.authenticated) {
            loginSection.style.display = 'none';
            chatSection.style.display = 'block';
            authStatus.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    Connected to Google Calendar
                    <button class="btn btn-sm btn-outline-danger ms-3" onclick="authManager.logout()">
                        Logout
                    </button>
                </div>
            `;
            
            // Load conversation history
            if (window.chatManager) {
                window.chatManager.loadConversationHistory();
            }
        } else {
            loginSection.style.display = 'block';
            chatSection.style.display = 'none';
            authStatus.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Please connect your Google Calendar to start booking
                </div>
            `;
        }
    }
    
    initializeAuth() {
        // Initialize auth manager
        if (typeof AuthManager !== 'undefined') {
            window.authManager = new AuthManager(this);
        }
    }
    
    initializeChat() {
        // Initialize chat manager
        if (typeof ChatManager !== 'undefined') {
            window.chatManager = new ChatManager(this);
        }
    }
    
    setupErrorHandling() {
        // Global error handler for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showError('An unexpected error occurred. Please try again.');
        });
        
        // Global error handler for JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('JavaScript error:', event.error);
            this.showError('An error occurred. Please refresh the page if the problem persists.');
        });
    }
    
    showLoadingState() {
        const loadingElement = document.getElementById('loading-state');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
    }
    
    hideLoadingState() {
        const loadingElement = document.getElementById('loading-state');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    showError(message, duration = 5000) {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;
        
        const alertId = 'alert-' + Date.now();
        const alertHTML = `
            <div id="${alertId}" class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertsContainer.insertAdjacentHTML('beforeend', alertHTML);
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                const alertElement = document.getElementById(alertId);
                if (alertElement) {
                    const bsAlert = new bootstrap.Alert(alertElement);
                    bsAlert.close();
                }
            }, duration);
        }
    }
    
    showSuccess(message, duration = 3000) {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;
        
        const alertId = 'alert-' + Date.now();
        const alertHTML = `
            <div id="${alertId}" class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="fas fa-check-circle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertsContainer.insertAdjacentHTML('beforeend', alertHTML);
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                const alertElement = document.getElementById(alertId);
                if (alertElement) {
                    const bsAlert = new bootstrap.Alert(alertElement);
                    bsAlert.close();
                }
            }, duration);
        }
    }
    
    // Utility methods
    formatDateTime(dateTimeString) {
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleString('en-US', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateTimeString;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public API methods
    refreshAuthStatus() {
        return this.checkAuthStatus();
    }
    
    getSessionId() {
        return this.sessionId;
    }
    
    isAuthenticated() {
        return this.authenticated;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AIBookingApp();
    window.app.init();
});

// Export for use in other modules
window.AIBookingApp = AIBookingApp;
