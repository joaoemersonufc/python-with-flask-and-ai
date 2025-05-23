"""
Routes for the chat functionality of the application.
"""
import logging
from flask import (
    Blueprint, render_template, request, jsonify
)

from services.ai_service import AIService
from services.local_ai_service import LocalAIService
from services.deepseek_ai_service import DeepSeekAIService
from utils.session_utils import get_chat_history, add_message_to_history, clear_chat_history
from utils.db_rate_limit import check_rate_limit, increment_message_count, get_remaining_messages

logger = logging.getLogger(__name__)

# Create a blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize AI services
ai_service = AIService()         # OpenAI service
deepseek_ai_service = DeepSeekAIService()  # DeepSeek AI service
local_ai_service = LocalAIService()        # Local fallback service

# AI service mode flags
AI_MODE_OPENAI = 'openai'
AI_MODE_DEEPSEEK = 'deepseek'
AI_MODE_LOCAL = 'local'

# Current AI service mode - start with DeepSeek as primary
current_ai_mode = AI_MODE_DEEPSEEK

def get_ai_model_name():
    """Get the name of the current AI model being used."""
    if current_ai_mode == AI_MODE_OPENAI:
        return "OpenAI GPT-4o"
    elif current_ai_mode == AI_MODE_DEEPSEEK:
        return "DeepSeek AI"
    else:
        return "Local AI (Fallback)"

@chat_bp.route('/')
def index():
    """Render the main chat page."""
    # Get chat history from session
    chat_history = get_chat_history()
    
    # Get remaining messages for the user
    remaining_messages = get_remaining_messages()
    
    # Get the current AI model information
    ai_info = {
        'mode': current_ai_mode,
        'name': get_ai_model_name(),
        'is_local': current_ai_mode == AI_MODE_LOCAL
    }
    
    return render_template('index.html', 
                          chat_history=chat_history, 
                          remaining_messages=remaining_messages,
                          ai_info=ai_info)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat messages and return AI responses.
    
    Expects JSON with format: {'message': 'user message here'}
    Returns JSON with format: {'response': 'AI response here'}
    
    Rate limited for free tier usage.
    """
    global current_ai_mode
    
    try:
        # Check rate limit before processing
        is_limited, limit_info = check_rate_limit()
        if is_limited:
            return jsonify({
                'error': 'rate_limit_exceeded',
                'limit_info': limit_info
            }), 429
        
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
        
        # Format messages for API (all services use the same format)
        formatted_messages = ai_service.format_messages_for_api(chat_history)
        
        # Get response from the appropriate AI service based on current mode
        global current_ai_mode
        try:
            if current_ai_mode == AI_MODE_DEEPSEEK:
                # Try DeepSeek AI first
                logger.info("Using DeepSeek AI service")
                ai_response = deepseek_ai_service.get_chat_response(formatted_messages)
            elif current_ai_mode == AI_MODE_OPENAI:
                # Use OpenAI as backup
                logger.info("Using OpenAI service")
                ai_response = ai_service.get_chat_response(formatted_messages)
            else:
                # Use local AI service as last resort
                logger.info("Using local AI service")
                ai_response = local_ai_service.get_chat_response(formatted_messages)
        except Exception as e:
            error_message = str(e)
            
            if error_message in ["API_QUOTA_EXCEEDED", "API_KEY_INVALID", "DEEPSEEK_API_KEY_MISSING"]:
                logger.warning(f"Error with AI service: {error_message}")
                
                # If DeepSeek fails, try OpenAI
                if current_ai_mode == AI_MODE_DEEPSEEK:
                    try:
                        logger.info("DeepSeek error, falling back to OpenAI")
                        current_ai_mode = AI_MODE_OPENAI
                        ai_response = ai_service.get_chat_response(formatted_messages)
                    except Exception as openai_error:
                        # If OpenAI also fails, use local fallback
                        logger.warning(f"OpenAI also failed: {str(openai_error)}, using local fallback")
                        current_ai_mode = AI_MODE_LOCAL
                        ai_response = local_ai_service.get_chat_response(formatted_messages)
                # If OpenAI fails, use local fallback
                elif current_ai_mode == AI_MODE_OPENAI:
                    logger.info("OpenAI error, falling back to local service")
                    current_ai_mode = AI_MODE_LOCAL
                    ai_response = local_ai_service.get_chat_response(formatted_messages)
                else:
                    # Re-raise if we're already in local mode and still getting errors
                    raise
            else:
                # Re-raise other exceptions to be handled by the outer try-except
                raise
        
        # Add AI response to chat history
        add_message_to_history('assistant', ai_response)
        
        # Increment message count for rate limiting
        increment_message_count()
        
        # Get remaining messages for the response
        remaining_messages = get_remaining_messages()
        
        # Get AI model info for the response
        ai_info = {
            'mode': current_ai_mode,
            'name': get_ai_model_name(),
            'is_local': current_ai_mode == AI_MODE_LOCAL
        }
        
        return jsonify({
            'response': ai_response,
            'remaining_messages': remaining_messages,
            'ai_info': ai_info
        })
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in chat endpoint: {error_message}")
        
        # Handle specific error types
        if error_message == "API_QUOTA_EXCEEDED":
            # API quota exceeded error
            return jsonify({
                'error': 'openai_quota_exceeded',
                'message': 'The API quota has been exceeded. Switching to an alternative AI model.'
            }), 503
        elif error_message == "API_RATE_LIMITED":
            # API rate limited error
            return jsonify({
                'error': 'openai_rate_limited',
                'message': 'The API is currently rate limited. Please try again in a few minutes.'
            }), 429
        elif error_message == "API_KEY_INVALID":
            # API key invalid error
            return jsonify({
                'error': 'openai_key_invalid',
                'message': 'The API key is invalid or has expired. Switching to an alternative AI model.'
            }), 401
        elif error_message == "DEEPSEEK_API_KEY_MISSING":
            # DeepSeek API key missing
            logger.error("DeepSeek API key is missing - update current_ai_mode")
            current_ai_mode = AI_MODE_OPENAI
            return jsonify({
                'error': 'deepseek_key_missing',
                'message': 'The DeepSeek API key is missing. Switching to OpenAI.'
            }), 401
        else:
            # Generic error
            return jsonify({
                'error': 'server_error',
                'message': 'An error occurred processing your request. Please try again later.'
            }), 500

@chat_bp.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear the chat history from the session."""
    try:
        clear_chat_history()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        return jsonify({'error': 'Failed to clear chat history.'}), 500

@chat_bp.route('/api/usage', methods=['GET'])
def get_usage():
    """Get the current usage info and limits."""
    try:
        is_limited, limit_info = check_rate_limit()
        remaining = get_remaining_messages()
        
        return jsonify({
            'is_limited': is_limited,
            'remaining_messages': remaining,
            'limit_info': limit_info if is_limited else None
        })
    except Exception as e:
        logger.error(f"Error getting usage info: {str(e)}")
        return jsonify({'error': 'Failed to get usage information.'}), 500
