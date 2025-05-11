"""
Utilities for managing chat session and database data.
"""
import logging
from typing import List, Dict, Any
from flask import session
from flask_login import current_user
from models import db, Message, User

logger = logging.getLogger(__name__)

# Session key for chat history for non-authenticated users
CHAT_HISTORY_KEY = 'chat_history'

def get_chat_history() -> List[Dict[str, Any]]:
    """
    Get the current chat history from the database if user is authenticated,
    or from the session if not.
    
    Returns:
        A list of message objects with 'role' and 'content' keys
    """
    # If user is authenticated, get messages from database
    if current_user.is_authenticated:
        messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.created_at).all()
        return [{'role': msg.role, 'content': msg.content} for msg in messages]
    
    # Otherwise, get from session
    if CHAT_HISTORY_KEY not in session:
        session[CHAT_HISTORY_KEY] = []
        
    return session[CHAT_HISTORY_KEY]

def add_message_to_history(role: str, content: str) -> None:
    """
    Add a message to the chat history in the database if user is authenticated,
    or to the session if not.
    
    Args:
        role: The role of the message sender ('user' or 'assistant')
        content: The message content
    """
    # If user is authenticated, add to database
    if current_user.is_authenticated:
        message = Message()
        message.user_id = current_user.id
        message.role = role
        message.content = content
        db.session.add(message)
        db.session.commit()
        logger.debug(f"Added {role} message to database for user {current_user.username}")
        return
    
    # Otherwise, add to session
    chat_history = get_chat_history()
    chat_history.append({
        'role': role,
        'content': content
    })
    
    # Update session
    session[CHAT_HISTORY_KEY] = chat_history
    session.modified = True
    
    logger.debug(f"Added {role} message to session chat history. Total messages: {len(chat_history)}")

def clear_chat_history() -> None:
    """
    Clear all messages from the chat history in the database if user is authenticated,
    or from the session if not.
    """
    if current_user.is_authenticated:
        Message.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        logger.debug(f"Cleared chat history for user {current_user.username} from database")
        return
    
    # Clear session chat history
    session[CHAT_HISTORY_KEY] = []
    session.modified = True
    logger.debug("Session chat history cleared")
