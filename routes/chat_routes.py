"""
Routes for the chat functionality of the application.
"""
import logging
from flask import (
    Blueprint, render_template, request, jsonify, 
    session, redirect, url_for
)

from services.ai_service import AIService
from utils.session_utils import get_chat_history, add_message_to_history, clear_chat_history

logger = logging.getLogger(__name__)

# Create a blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize AI service
ai_service = AIService()

@chat_bp.route('/')
def index():
    """Render the main chat page."""
    # Get chat history from session
    chat_history = get_chat_history()
    
    return render_template('index.html', chat_history=chat_history)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat messages and return AI responses.
    
    Expects JSON with format: {'message': 'user message here'}
    Returns JSON with format: {'response': 'AI response here'}
    """
    try:
        # Get user message from request
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Invalid request. Message is required.'}), 400
            
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty.'}), 400
            
        # Get chat history from session
        chat_history = get_chat_history()
        
        # Add user message to chat history
        add_message_to_history('user', user_message)
        
        # Update chat history after adding user message
        chat_history = get_chat_history()
        
        # Format messages for OpenAI API
        formatted_messages = ai_service.format_messages_for_api(chat_history)
        
        # Get response from AI service
        ai_response = ai_service.get_chat_response(formatted_messages)
        
        # Add AI response to chat history
        add_message_to_history('assistant', ai_response)
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request.'}), 500

@chat_bp.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear the chat history from the session."""
    try:
        clear_chat_history()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        return jsonify({'error': 'Failed to clear chat history.'}), 500
