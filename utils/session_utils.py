"""
Utilities for managing chat session data.
"""
import logging
from typing import List, Dict, Any
from flask import session

logger = logging.getLogger(__name__)

# Session key for chat history
CHAT_HISTORY_KEY = 'chat_history'

def get_chat_history() -> List[Dict[str, Any]]:
    """
    Get the current chat history from the session.
    
    Returns:
        A list of message objects with 'role' and 'content' keys
    """
    # Initialize chat history if it doesn't exist
    if CHAT_HISTORY_KEY not in session:
        session[CHAT_HISTORY_KEY] = []
        
    return session[CHAT_HISTORY_KEY]

def add_message_to_history(role: str, content: str) -> None:
    """
    Add a message to the chat history in the session.
    
    Args:
        role: The role of the message sender ('user' or 'assistant')
        content: The message content
    """
    # Get current chat history
    chat_history = get_chat_history()
    
    # Add new message
    chat_history.append({
        'role': role,
        'content': content
    })
    
    # Update session
    session[CHAT_HISTORY_KEY] = chat_history
    session.modified = True
    
    logger.debug(f"Added {role} message to chat history. Total messages: {len(chat_history)}")

def clear_chat_history() -> None:
    """Clear all messages from the chat history."""
    session[CHAT_HISTORY_KEY] = []
    session.modified = True
    logger.debug("Chat history cleared")
