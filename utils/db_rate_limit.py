"""
Utilities for managing rate limiting and message quotas using the database.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from flask import session
from flask_login import current_user
from models import db, RateLimit, User

# Constants for rate limiting
FREE_TIER_LIMIT = 5  # Number of messages allowed in free tier
RESET_PERIOD_HOURS = 3  # Reset period in hours

# Session key for rate limiting for non-authenticated users
SESSION_LIMIT_KEY = 'message_limit'

def get_usage_info() -> Dict:
    """
    Get the current usage information from the database if user is authenticated,
    or from the session if not.
    
    Returns:
        A dictionary containing message count and reset time
    """
    # If user is authenticated, get from database
    if current_user.is_authenticated:
        rate_limit = RateLimit.query.filter_by(user_id=current_user.id).first()
        
        # If no rate limit record exists, create one
        if not rate_limit:
            reset_time = datetime.now() + timedelta(hours=RESET_PERIOD_HOURS)
            rate_limit = RateLimit()
            rate_limit.user_id = current_user.id
            rate_limit.count = 0
            rate_limit.reset_time = reset_time
            db.session.add(rate_limit)
            db.session.commit()
        
        return {
            'count': rate_limit.count,
            'reset_time': rate_limit.reset_time.timestamp()
        }
    
    # Otherwise, get from session
    if SESSION_LIMIT_KEY not in session:
        reset_time = datetime.now() + timedelta(hours=RESET_PERIOD_HOURS)
        session[SESSION_LIMIT_KEY] = {
            'count': 0,
            'reset_time': reset_time.timestamp()
        }
        session.modified = True
        
    return session[SESSION_LIMIT_KEY]

def increment_message_count() -> None:
    """
    Increment the message count in the database if user is authenticated,
    or in the session if not.
    """
    # If user is authenticated, update in database
    if current_user.is_authenticated:
        rate_limit = RateLimit.query.filter_by(user_id=current_user.id).first()
        
        # If no rate limit record exists, create one with count=1
        if not rate_limit:
            reset_time = datetime.now() + timedelta(hours=RESET_PERIOD_HOURS)
            rate_limit = RateLimit()
            rate_limit.user_id = current_user.id
            rate_limit.count = 1
            rate_limit.reset_time = reset_time
            db.session.add(rate_limit)
        else:
            rate_limit.count += 1
            
        db.session.commit()
        return
    
    # Otherwise, update in session
    usage_info = get_usage_info()
    usage_info['count'] += 1
    session[SESSION_LIMIT_KEY] = usage_info
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
        
        # Reset in database or session based on authentication status
        if current_user.is_authenticated:
            rate_limit = RateLimit.query.filter_by(user_id=current_user.id).first()
            if rate_limit:
                rate_limit.count = 0
                rate_limit.reset_time = reset_time
                db.session.commit()
            else:
                # Should not happen, but handle it just in case
                rate_limit = RateLimit()
                rate_limit.user_id = current_user.id
                rate_limit.count = 0
                rate_limit.reset_time = reset_time
                db.session.add(rate_limit)
                db.session.commit()
        else:
            # Reset in session
            usage_info = {
                'count': 0,
                'reset_time': reset_time.timestamp()
            }
            session[SESSION_LIMIT_KEY] = usage_info
            session.modified = True
    
    # Get fresh usage info after possible reset
    usage_info = get_usage_info()
    
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
    """
    Reset the usage counter and timer. Used primarily for testing.
    """
    reset_time = datetime.now() + timedelta(hours=RESET_PERIOD_HOURS)
    
    if current_user.is_authenticated:
        rate_limit = RateLimit.query.filter_by(user_id=current_user.id).first()
        if rate_limit:
            rate_limit.count = 0
            rate_limit.reset_time = reset_time
            db.session.commit()
        else:
            rate_limit = RateLimit()
            rate_limit.user_id = current_user.id
            rate_limit.count = 0
            rate_limit.reset_time = reset_time
            db.session.add(rate_limit)
            db.session.commit()
    else:
        session[SESSION_LIMIT_KEY] = {
            'count': 0,
            'reset_time': reset_time.timestamp()
        }
        session.modified = True