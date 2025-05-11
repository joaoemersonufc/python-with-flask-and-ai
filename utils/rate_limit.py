"""
Utilities for managing rate limiting and message quotas.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from flask import session

# Constants for rate limiting
MESSAGE_LIMIT_KEY = 'message_limit'
FREE_TIER_LIMIT = 5  # Number of messages allowed in free tier
RESET_PERIOD_HOURS = 3  # Reset period in hours

def get_usage_info() -> Dict:
    """
    Get the current usage information from the session.
    
    Returns:
        A dictionary containing message count and reset time
    """
    # Initialize limit info if it doesn't exist
    if MESSAGE_LIMIT_KEY not in session:
        reset_time = datetime.now() + timedelta(hours=RESET_PERIOD_HOURS)
        session[MESSAGE_LIMIT_KEY] = {
            'count': 0,
            'reset_time': reset_time.timestamp()
        }
        session.modified = True
        
    return session[MESSAGE_LIMIT_KEY]

def increment_message_count() -> None:
    """
    Increment the message count in the session.
    """
    usage_info = get_usage_info()
    usage_info['count'] += 1
    session[MESSAGE_LIMIT_KEY] = usage_info
    session.modified = True

def check_rate_limit() -> Tuple[bool, Optional[Dict]]:
    """
    Check if the user has exceeded their message limit.
    
    Returns:
        A tuple containing:
        - Boolean indicating if the limit is exceeded
        - If limited, a dict with 'remaining_time' (seconds) to reset
          and 'reset_time' (formatted string)
    """
    usage_info = get_usage_info()
    
    # Check if reset time has passed
    reset_timestamp = usage_info['reset_time']
    current_time = datetime.now().timestamp()
    
    # If reset time has passed, reset the counter
    if current_time > reset_timestamp:
        reset_time = datetime.now() + timedelta(hours=RESET_PERIOD_HOURS)
        usage_info = {
            'count': 0,
            'reset_time': reset_time.timestamp()
        }
        session[MESSAGE_LIMIT_KEY] = usage_info
        session.modified = True
    
    # Check if user has exceeded the limit
    if usage_info['count'] >= FREE_TIER_LIMIT:
        # Calculate remaining time
        reset_time_dt = datetime.fromtimestamp(usage_info['reset_time'])
        remaining_seconds = int((reset_time_dt - datetime.now()).total_seconds())
        remaining_time = max(0, remaining_seconds)
        
        # Format reset time for display
        formatted_reset_time = reset_time_dt.strftime("%H:%M:%S")
        
        return (True, {
            'remaining_time': remaining_time,
            'reset_time': formatted_reset_time,
            'limit': FREE_TIER_LIMIT
        })
    
    return (False, None)

def get_remaining_messages() -> int:
    """
    Get the number of remaining messages in the current period.
    
    Returns:
        Number of messages remaining
    """
    usage_info = get_usage_info()
    return max(0, FREE_TIER_LIMIT - usage_info['count'])

def reset_usage() -> None:
    """Reset the usage counter and timer. Used primarily for testing."""
    reset_time = datetime.now() + timedelta(hours=RESET_PERIOD_HOURS)
    session[MESSAGE_LIMIT_KEY] = {
        'count': 0,
        'reset_time': reset_time.timestamp()
    }
    session.modified = True