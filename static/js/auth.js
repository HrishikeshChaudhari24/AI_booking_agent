/**
 * Authentication management
 * Handles Google OAuth login/logout and token management
 */

class AuthManager {
    constructor(app) {
        this.app = app;
        this.isLoggingIn = false;
        
        // Bind methods
        this.login = this.login.bind(this);
        this.logout = this.logout.bind(this);
        this.handleAuthCallback = this.handleAuthCallback.bind(this);
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // If DOM is already loaded, set up immediately
        if (document.readyState === 'loading') {
            // DOM hasn't finished loading yet
            document.addEventListener('DOMContentLoaded', () => {
                this.bindLoginButton();
            });
        } else {
            // DOM is already loaded
            this.bindLoginButton();
        }
    }
    
    bindLoginButton() {
        const loginBtn = document.getElementById('login-btn');
        if (loginBtn && !loginBtn.hasAttribute('data-auth-bound')) {
            loginBtn.addEventListener('click', this.login);
            loginBtn.setAttribute('data-auth-bound', 'true');
            console.log('Login button event listener attached');
        }
    }
    
    async login() {
        if (this.isLoggingIn) {
            console.log('Login already in progress');
            return;
        }
        
        try {
            this.isLoggingIn = true;
            this.setLoginButtonState(true);
            
            console.log('Initiating Google OAuth login...');
            
            // Redirect to OAuth endpoint
            window.location.href = '/auth/login';
            
        } catch (error) {
            console.error('Login error:', error);
            this.app.showError('Failed to initiate login. Please try again.');
            this.setLoginButtonState(false);
            this.isLoggingIn = false;
        }
    }
    
    async logout() {
        try {
            const confirmLogout = confirm('Are you sure you want to logout?');
            if (!confirmLogout) return;
            
            console.log('Logging out...');
            
            const response = await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Logout successful:', data.message);
                
                // Update app state
                this.app.handleAuthStatus({ authenticated: false });
                
                // Clear any cached data
                if (window.chatManager) {
                    window.chatManager.clearChat();
                }
                
                this.app.showSuccess('Logged out successfully');
                
            } else {
                throw new Error('Logout request failed');
            }
            
        } catch (error) {
            console.error('Logout error:', error);
            this.app.showError('Failed to logout. Please try again.');
        }
    }
    
    async refreshToken() {
        try {
            console.log('Refreshing access token...');
            
            const response = await fetch('/auth/refresh_token', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Token refreshed successfully');
                return true;
            } else {
                console.error('Token refresh failed');
                return false;
            }
            
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }
    
    handleAuthCallback() {
        // This method handles the OAuth callback
        // The callback is handled server-side, but we can use this
        // to handle any client-side logic after successful auth
        
        console.log('Handling auth callback...');
        
        // Check if we're on the callback page
        if (window.location.pathname === '/auth/callback') {
            // Show success message and redirect to main app
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }
    }
    
    setLoginButtonState(loading) {
        const loginBtn = document.getElementById('login-btn');
        if (!loginBtn) return;
        
        if (loading) {
            loginBtn.disabled = true;
            loginBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Connecting to Google...
            `;
        } else {
            loginBtn.disabled = false;
            loginBtn.innerHTML = `
                <i class="fab fa-google me-2"></i>
                Connect Google Calendar
            `;
        }
    }
    
    // Handle authentication errors from API calls
    handleAuthError(response) {
        if (response.status === 401) {
            console.log('Authentication required, redirecting to login...');
            this.app.handleAuthStatus({ authenticated: false });
            this.app.showError('Your session has expired. Please login again.');
            return true;
        }
        return false;
    }
    
    // Utility method to make authenticated API calls
    async authenticatedFetch(url, options = {}) {
        try {
            // Set default options
            const defaultOptions = {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            };
            
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            // Handle authentication errors
            if (response.status === 401) {
                // Try to refresh token
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Retry the original request
                    return await fetch(url, { ...defaultOptions, ...options });
                } else {
                    // Refresh failed, need to re-authenticate
                    this.handleAuthError(response);
                    throw new Error('Authentication required');
                }
            }
            
            return response;
            
        } catch (error) {
            console.error('Authenticated fetch error:', error);
            throw error;
        }
    }
    
    // Test connection to Google Calendar
    async testConnection() {
        try {
            console.log('Testing Google Calendar connection...');
            
            const response = await this.authenticatedFetch('/api/test_calendar', {
                method: 'POST'
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Calendar connection test successful:', data);
                this.app.showSuccess(`Calendar connected! Found ${data.events_count} upcoming events.`);
                return true;
            } else {
                throw new Error('Calendar connection test failed');
            }
            
        } catch (error) {
            console.error('Calendar connection test error:', error);
            this.app.showError('Failed to connect to Google Calendar. Please check your permissions.');
            return false;
        }
    }
    
    // Initialize auth-related event listeners
    initializeEventListeners() {
        // Test connection button
        const testBtn = document.getElementById('test-connection-btn');
        if (testBtn) {
            testBtn.addEventListener('click', () => this.testConnection());
        }
    }
}

// Export for use in other modules
window.AuthManager = AuthManager;
window.AuthManager = AuthManager;
