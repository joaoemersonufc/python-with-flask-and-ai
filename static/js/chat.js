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
            
            // Check for rate limit error
            if (response.status === 429 && data.error === 'rate_limit_exceeded') {
                handleRateLimit(data.limit_info);
                return;
            }
            
            if (!response.ok) {
                throw new Error('Failed to get response');
            }
            
            // Add AI response to chat
            addMessageToChat('ai', data.response);
            
            // Update remaining messages counter
            if (data.remaining_messages !== undefined) {
                updateRemainingMessages(data.remaining_messages);
            }
            
            // Scroll to bottom
            scrollToBottom();
            
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            
            // Show error message
            addMessageToChat('ai', 'Sorry, I encountered an error. Please try again later.');
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
    
    // Check rate limit on page load
    checkRateLimit();
    
    // Initial scroll to bottom to show most recent messages
    scrollToBottom();
});
