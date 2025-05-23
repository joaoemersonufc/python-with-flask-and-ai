document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const messagesContainer = document.getElementById('messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const clearButton = document.getElementById('clear-chat');
    const remainingMessagesElement = document.getElementById('remaining-messages');
    
    // Rate limit modal elements
    const rateLimitModal = new bootstrap.Modal(document.getElementById('rate-limit-modal'), {
        backdrop: 'static',
        keyboard: false
    });
    const countdownTimer = document.getElementById('countdown-timer');
    const messageLimit = document.getElementById('message-limit');
    
    // Rate limit variables
    let countdownInterval;
    let rateLimitResetTime;
    
    // Auto-resize textarea as user types
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Submit form when Enter is pressed (unless Shift is held)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Handle chat form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const userMessage = userInput.value.trim();
        if (!userMessage) return;
        
        // Clear input and reset height
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Add user message to chat
        addMessageToChat('user', userMessage);
        
        // Scroll to bottom
        scrollToBottom();
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send message to server
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userMessage })
            });
            
            // Get the response data
            const data = await response.json();
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Check for specific errors
            if (response.status === 429 && data.error === 'rate_limit_exceeded') {
                // User rate limit error
                handleRateLimit(data.limit_info);
                return;
            } else if (data.error === 'openai_quota_exceeded') {
                // API quota exceeded error
                showErrorMessage('OpenAI API quota exceeded. Switching to an alternative AI model.');
                return;
            } else if (data.error === 'openai_rate_limited') {
                // API rate limited error
                showErrorMessage('OpenAI API is currently rate limited. Please try again in a few minutes.');
                return;
            } else if (data.error === 'openai_key_invalid') {
                // API key invalid error
                showErrorMessage('OpenAI API key is invalid. Switching to an alternative AI model.');
                return;
            } else if (!response.ok) {
                throw new Error('Failed to get response');
            }
            
            // Add AI response to chat
            addMessageToChat('ai', data.response);
            
            // Update remaining messages counter
            if (data.remaining_messages !== undefined) {
                updateRemainingMessages(data.remaining_messages);
            }
            
            // Check if AI model info is available and update UI
            if (data.ai_info) {
                updateAIModelInfo(data.ai_info);
            }
            
            // Scroll to bottom
            scrollToBottom();
            
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            
            // Show error message
            showErrorMessage('Sorry, I encountered an error. Please try again later.');
            scrollToBottom();
        }
        
        // Helper function to show error message in chat
        function showErrorMessage(message) {
            // Add system message to chat
            const messageWrapper = document.createElement('div');
            messageWrapper.className = 'message-wrapper system-message';
            
            messageWrapper.innerHTML = `
                <div class="message error-message">
                    <div class="message-header">
                        <strong><i class="fas fa-exclamation-circle"></i> System</strong>
                    </div>
                    <div class="message-content">${escapeHtml(message)}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageWrapper);
            scrollToBottom();
        }
    });
    
    // Clear chat history
    clearButton.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/chat/clear', { method: 'POST' });
            
            if (response.ok) {
                // Clear messages container
                messagesContainer.innerHTML = `
                    <div class="empty-state text-center py-5">
                        <i class="fas fa-robot fa-4x mb-3 text-secondary"></i>
                        <h4>Start a conversation</h4>
                        <p class="text-secondary">Ask me anything, and I'll do my best to help you.</p>
                        <p class="mt-3">
                            <small class="text-info">Free tier: ${remainingMessagesElement.textContent} messages every 3 hours</small>
                        </p>
                    </div>
                `;
                
                // Check if rate limit has been reset
                checkRateLimit();
            } else {
                console.error('Failed to clear chat history');
            }
        } catch (error) {
            console.error('Error clearing chat history:', error);
        }
    });
    
    // Rate limit handling functions
    function handleRateLimit(limitInfo) {
        // Set the limit info in the modal
        rateLimitResetTime = new Date().getTime() + (limitInfo.remaining_time * 1000);
        messageLimit.textContent = limitInfo.limit;
        
        // Update the countdown immediately
        updateCountdown();
        
        // Start countdown interval
        clearInterval(countdownInterval);
        countdownInterval = setInterval(updateCountdown, 1000);
        
        // Show the modal
        rateLimitModal.show();
    }
    
    function updateCountdown() {
        const now = new Date().getTime();
        const timeLeft = rateLimitResetTime - now;
        
        if (timeLeft <= 0) {
            // Time's up, clear interval and refresh rate limit info
            clearInterval(countdownInterval);
            countdownTimer.textContent = "00:00:00";
            
            // Check for updated rate limit after a short delay
            setTimeout(checkRateLimit, 1000);
            return;
        }
        
        // Calculate hours, minutes, seconds
        const hours = Math.floor(timeLeft / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
        
        // Display the countdown
        countdownTimer.textContent = 
            (hours < 10 ? "0" + hours : hours) + ":" +
            (minutes < 10 ? "0" + minutes : minutes) + ":" +
            (seconds < 10 ? "0" + seconds : seconds);
    }
    
    function checkRateLimit() {
        fetch('/api/usage')
            .then(response => response.json())
            .then(data => {
                // Update remaining messages counter
                if (data.remaining_messages !== undefined) {
                    updateRemainingMessages(data.remaining_messages);
                }
                
                // If no longer rate limited, hide modal
                if (!data.is_limited && document.getElementById('rate-limit-modal').classList.contains('show')) {
                    rateLimitModal.hide();
                }
                
                // If still rate limited, update the modal
                if (data.is_limited && data.limit_info) {
                    handleRateLimit(data.limit_info);
                }
            })
            .catch(error => console.error('Error checking rate limit:', error));
    }
    
    function updateRemainingMessages(count) {
        remainingMessagesElement.textContent = count;
    }
    
    // Helper function to add a message to the chat
    function addMessageToChat(role, content) {
        // Remove empty state if present
        const emptyState = messagesContainer.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper ${role === 'user' ? 'user-message' : 'ai-message'}`;
        
        messageWrapper.innerHTML = `
            <div class="message">
                <div class="message-header">
                    <strong>${role === 'user' ? 'You' : 'AI Assistant'}</strong>
                </div>
                <div class="message-content">${escapeHtml(content)}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageWrapper);
    }
    
    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;")
            .replace(/\n/g, "<br>");
    }
    
    // Helper functions for typing indicator
    function showTypingIndicator() {
        typingIndicator.classList.remove('d-none');
    }
    
    function hideTypingIndicator() {
        typingIndicator.classList.add('d-none');
    }
    
    // Scroll to bottom of messages container
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Function to update the UI based on AI model info
    function updateAIModelInfo(aiInfo) {
        // Update page title with AI model name
        const titleElement = document.querySelector('.card-header h3');
        if (titleElement) {
            titleElement.innerHTML = `<i class="fas fa-comment-dots me-2"></i>Chat with ${aiInfo.name}`;
        }
        
        // Remove any existing alerts
        const existingAlerts = document.querySelectorAll('.model-alert');
        existingAlerts.forEach(alert => alert.remove());
        
        // Add the appropriate alert based on the AI mode
        const alertDiv = document.createElement('div');
        alertDiv.setAttribute('role', 'alert');
        alertDiv.className = 'model-alert m-2 mb-0 alert';
        
        if (aiInfo.is_local) {
            // Local mode alert
            alertDiv.className += ' alert-warning';
            alertDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Running in Local Mode:</strong> External AI APIs are currently unavailable. Responses will be limited.
            `;
        } else if (aiInfo.mode === 'deepseek') {
            // DeepSeek mode alert
            alertDiv.className += ' alert-info';
            alertDiv.innerHTML = `
                <i class="fas fa-robot me-2"></i>
                <strong>Using DeepSeek AI:</strong> Powered by DeepSeek's free-tier AI model.
            `;
        } else if (aiInfo.mode === 'openai') {
            // OpenAI mode alert
            alertDiv.className += ' alert-primary';
            alertDiv.innerHTML = `
                <i class="fas fa-brain me-2"></i>
                <strong>Using OpenAI:</strong> Powered by OpenAI's models.
            `;
        }
        
        // Insert after card header
        const cardHeader = document.querySelector('.card-header');
        if (cardHeader) {
            // Only add if we have a valid AI mode and the alert doesn't already exist
            if (!document.querySelector(`.model-alert.alert-${aiInfo.mode}`)) {
                cardHeader.parentNode.insertBefore(alertDiv, cardHeader.nextSibling);
            }
        }
    }
    
    // Check rate limit on page load
    checkRateLimit();
    
    // Initial scroll to bottom to show most recent messages
    scrollToBottom();
});
