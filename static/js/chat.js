/**
 * Chat interface management
 * Handles the conversation UI and booking interactions
 */

class ChatManager {
    constructor(app) {
        this.app = app;
        this.isProcessing = false;
        this.conversationHistory = [];
        
        // Bind methods
        this.sendMessage = this.sendMessage.bind(this);
        this.handleKeyPress = this.handleKeyPress.bind(this);
        this.clearChat = this.clearChat.bind(this);
        
        // Initialize when ready
        this.initialize();
    }
    
    initialize() {
        this.setupEventListeners();
        this.showWelcomeMessage();
    }
    
    setupEventListeners() {
        // Send button
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            sendBtn.addEventListener('click', this.sendMessage);
        }
        
        // Message input
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('keypress', this.handleKeyPress);
            messageInput.addEventListener('input', this.handleInputChange.bind(this));
        }
        
        // Clear chat button
        const clearBtn = document.getElementById('clear-chat-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', this.clearChat);
        }
        
        // Quick action buttons
        this.setupQuickActions();
    }
    
    setupQuickActions() {
        const quickActions = document.querySelectorAll('.quick-action-btn');
        quickActions.forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this.handleQuickAction(action);
            });
        });
    }
    
    handleQuickAction(action) {
        const messageInput = document.getElementById('message-input');
        if (!messageInput) return;
        
        let message = '';
        
        switch (action) {
            case 'schedule':
                message = 'I need to schedule a meeting';
                break;
            case 'reschedule':
                message = 'I need to reschedule my meeting';
                break;
            case 'cancel':
                message = 'I need to cancel my meeting';
                break;
            case 'upcoming':
                message = 'Show me my upcoming meetings';
                break;
            default:
                return;
        }
        
        messageInput.value = message;
        messageInput.focus();
    }
    
    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    handleInputChange() {
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        
        if (messageInput && sendBtn) {
            const hasText = messageInput.value.trim().length > 0;
            sendBtn.disabled = !hasText || this.isProcessing;
        }
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        if (!messageInput || this.isProcessing) return;
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        try {
            this.isProcessing = true;
            this.setSendButtonState(true);
            
            // Add user message to chat
            this.addMessageToChat('user', message);
            
            // Clear input
            messageInput.value = '';
            this.handleInputChange();
            
            // Show typing indicator
            this.showTypingIndicator();
            
            // Send request to backend
            const response = await window.authManager.authenticatedFetch('/booking/process', {
                method: 'POST',
                body: JSON.stringify({ message: message })
            });
            
            this.hideTypingIndicator();
            
            if (response.ok) {
                const data = await response.json();
                
                // Add AI response to chat
                this.addMessageToChat('assistant', data.response, data.booking_result);
                
                // Handle special responses
                this.handleBookingResult(data.booking_result);
                
            } else {
                const errorData = await response.json();
                this.addMessageToChat('error', errorData.error || 'Failed to process your request');
            }
            
        } catch (error) {
            console.error('Send message error:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('error', 'An error occurred while processing your request. Please try again.');
        } finally {
            this.isProcessing = false;
            this.setSendButtonState(false);
            messageInput.focus();
        }
    }
    
    addMessageToChat(sender, message, bookingResult = null) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const messageId = 'msg-' + Date.now();
        const timestamp = new Date().toLocaleTimeString();
        
        let messageHTML = '';
        
        if (sender === 'user') {
            messageHTML = `
                <div id="${messageId}" class="message user-message">
                    <div class="message-content">
                        <div class="message-text">${this.app.escapeHtml(message)}</div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                    <div class="message-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
            `;
        } else if (sender === 'assistant') {
            messageHTML = `
                <div id="${messageId}" class="message assistant-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-text">${this.formatAssistantMessage(message)}</div>
                        ${this.createBookingResultHTML(bookingResult)}
                        <div class="message-time">${timestamp}</div>
                    </div>
                </div>
            `;
        } else if (sender === 'error') {
            messageHTML = `
                <div id="${messageId}" class="message error-message">
                    <div class="message-avatar">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-text text-danger">${this.app.escapeHtml(message)}</div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                </div>
            `;
        }
        
        chatContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
        
        // Store in conversation history
        this.conversationHistory.push({
            id: messageId,
            sender: sender,
            message: message,
            timestamp: timestamp,
            bookingResult: bookingResult
        });
    }
    
    formatAssistantMessage(message) {
        // Convert line breaks to HTML
        let formatted = this.app.escapeHtml(message);
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Make URLs clickable
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        
        return formatted;
    }
    
    createBookingResultHTML(bookingResult) {
        if (!bookingResult) return '';
        
        let resultHTML = '';
        
        if (bookingResult.success && bookingResult.event) {
            const event = bookingResult.event;
            resultHTML = `
                <div class="booking-result success mt-3">
                    <div class="alert alert-success">
                        <h6><i class="fas fa-calendar-check me-2"></i>Event Created Successfully</h6>
                        <div class="event-details">
                            <strong>${this.app.escapeHtml(event.summary || 'Untitled Event')}</strong><br>
                            <small class="text-muted">
                                ${this.formatEventTime(event)}
                            </small>
                        </div>
                        ${bookingResult.calendar_link ? `
                            <a href="${bookingResult.calendar_link}" target="_blank" class="btn btn-sm btn-outline-success mt-2">
                                <i class="fas fa-external-link-alt me-1"></i>Open in Google Calendar
                            </a>
                        ` : ''}
                    </div>
                </div>
            `;
        } else if (bookingResult.conflict) {
            resultHTML = `
                <div class="booking-result conflict mt-3">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-calendar-times me-2"></i>Schedule Conflict</h6>
                        <p class="mb-2">${this.app.escapeHtml(bookingResult.message)}</p>
                        ${bookingResult.alternative_time ? `
                            <button class="btn btn-sm btn-outline-primary" onclick="chatManager.suggestAlternative('${bookingResult.alternative_time}')">
                                <i class="fas fa-clock me-1"></i>Use suggested time
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        } else if (bookingResult.events) {
            resultHTML = this.createEventsListHTML(bookingResult.events);
        }
        
        return resultHTML;
    }
    
    createEventsListHTML(events) {
        if (!events || events.length === 0) {
            return `
                <div class="events-list mt-3">
                    <div class="alert alert-info">
                        <i class="fas fa-calendar me-2"></i>No events found
                    </div>
                </div>
            `;
        }
        
        let eventsHTML = `
            <div class="events-list mt-3">
                <h6><i class="fas fa-calendar me-2"></i>Upcoming Events</h6>
        `;
        
        events.slice(0, 5).forEach(event => {
            eventsHTML += `
                <div class="event-item">
                    <div class="event-title">${this.app.escapeHtml(event.summary || 'Untitled')}</div>
                    <div class="event-time text-muted">${this.formatEventTime(event)}</div>
                </div>
            `;
        });
        
        if (events.length > 5) {
            eventsHTML += `<div class="text-muted small">... and ${events.length - 5} more events</div>`;
        }
        
        eventsHTML += '</div>';
        return eventsHTML;
    }
    
    formatEventTime(event) {
        try {
            const start = event.start?.dateTime || event.start?.date;
            const end = event.end?.dateTime || event.end?.date;
            
            if (start) {
                const startDate = new Date(start);
                let formatted = this.app.formatDateTime(start);
                
                if (end) {
                    const endDate = new Date(end);
                    if (startDate.toDateString() === endDate.toDateString()) {
                        // Same day, just show end time
                        formatted += ' - ' + endDate.toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    } else {
                        // Different day, show full end datetime
                        formatted += ' - ' + this.app.formatDateTime(end);
                    }
                }
                
                return formatted;
            }
            
            return 'Time not specified';
        } catch (error) {
            console.error('Error formatting event time:', error);
            return 'Invalid time';
        }
    }
    
    handleBookingResult(bookingResult) {
        if (!bookingResult) return;
        
        // Handle specific booking results
        if (bookingResult.success) {
            // Success feedback is already shown in the chat
            console.log('Booking operation successful');
        } else if (bookingResult.conflict) {
            console.log('Schedule conflict detected');
        } else if (bookingResult.error) {
            console.error('Booking error:', bookingResult.error);
        }
    }
    
    suggestAlternative(alternativeTime) {
        const messageInput = document.getElementById('message-input');
        if (messageInput && alternativeTime) {
            const date = new Date(alternativeTime);
            const suggestion = `Yes, please schedule it for ${this.app.formatDateTime(alternativeTime)}`;
            messageInput.value = suggestion;
            messageInput.focus();
        }
    }
    
    showTypingIndicator() {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const typingHTML = `
            <div id="typing-indicator" class="message assistant-message typing">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        chatContainer.insertAdjacentHTML('beforeend', typingHTML);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    setSendButtonState(loading) {
        const sendBtn = document.getElementById('send-btn');
        const messageInput = document.getElementById('message-input');
        
        if (sendBtn) {
            if (loading) {
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
            } else {
                sendBtn.disabled = !messageInput?.value.trim();
                sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            }
        }
    }
    
    scrollToBottom() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    showWelcomeMessage() {
        if (this.app.isAuthenticated()) {
            this.addMessageToChat('assistant', 
                "Hello! I'm your AI booking assistant. I can help you schedule, reschedule, or cancel meetings in your Google Calendar. Just tell me what you need to do in natural language!"
            );
        }
    }
    
    async loadConversationHistory() {
        try {
            const response = await window.authManager.authenticatedFetch('/api/conversation_history');
            
            if (response.ok) {
                const data = await response.json();
                const history = data.history || [];
                
                // Clear current chat
                const chatContainer = document.getElementById('chat-messages');
                if (chatContainer) {
                    chatContainer.innerHTML = '';
                }
                
                // Reload conversation history
                history.forEach(entry => {
                    this.addMessageToChat('user', entry.user_message);
                    this.addMessageToChat('assistant', entry.ai_response);
                });
                
                // Show welcome message if no history
                if (history.length === 0) {
                    this.showWelcomeMessage();
                }
                
            }
        } catch (error) {
            console.error('Failed to load conversation history:', error);
            this.showWelcomeMessage();
        }
    }
    
    async clearChat() {
        try {
            const confirmClear = confirm('Are you sure you want to clear the conversation? This cannot be undone.');
            if (!confirmClear) return;
            
            const response = await window.authManager.authenticatedFetch('/booking/clear_conversation', {
                method: 'POST'
            });
            
            if (response.ok) {
                // Clear UI
                const chatContainer = document.getElementById('chat-messages');
                if (chatContainer) {
                    chatContainer.innerHTML = '';
                }
                
                // Clear local history
                this.conversationHistory = [];
                
                // Show welcome message
                this.showWelcomeMessage();
                
                this.app.showSuccess('Conversation cleared');
            } else {
                throw new Error('Failed to clear conversation');
            }
            
        } catch (error) {
            console.error('Clear chat error:', error);
            this.app.showError('Failed to clear conversation');
        }
    }
}

// Export for use in other modules
window.ChatManager = ChatManager;
