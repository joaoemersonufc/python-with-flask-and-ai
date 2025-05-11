document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const messagesContainer = document.getElementById('messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const clearButton = document.getElementById('clear-chat');
    
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
            
            if (!response.ok) {
                throw new Error('Failed to get response');
            }
            
            const data = await response.json();
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add AI response to chat
            addMessageToChat('ai', data.response);
            
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
                    </div>
                `;
            } else {
                console.error('Failed to clear chat history');
            }
        } catch (error) {
            console.error('Error clearing chat history:', error);
        }
    });
    
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
    
    // Initial scroll to bottom to show most recent messages
    scrollToBottom();
});
