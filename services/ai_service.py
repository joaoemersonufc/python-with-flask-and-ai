"""
AI Service module that handles interactions with OpenAI API.
"""
import os
import logging
from typing import Dict, List, Any, cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key from environment variables."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            
        self.client = OpenAI(api_key=api_key)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
    def get_chat_response(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get a response from the OpenAI chat API.
        
        Args:
            messages: A list of message objects with role and content keys
                     Example: [{"role": "user", "content": "Hello, how are you?"}]
        
        Returns:
            The text response from the AI
            
        Raises:
            Exception: If there's an error communicating with the OpenAI API
        """
        try:
            logger.debug(f"Sending request to OpenAI with {len(messages)} messages")
            
            # Create API request
            # Cast the messages to the correct type for OpenAI
            openai_messages = cast(List[ChatCompletionMessageParam], messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=0.7,
                max_tokens=800,
            )
            
            # Extract and return the AI's response
            ai_response = response.choices[0].message.content
            if ai_response:
                logger.debug(f"Received response from OpenAI: {ai_response[:50]}...")
            else:
                logger.warning("Received an empty response from OpenAI.")
            
            # Check if the AI response is None before returning
            if ai_response is None:
                logger.warning("AI response is None. Returning an empty string.")
                return ""
            
            return ai_response
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error getting response from OpenAI: {error_message}")
            
            # Check for specific error types
            if "insufficient_quota" in error_message or "429" in error_message:
                raise Exception("API_QUOTA_EXCEEDED")
            elif "rate_limit" in error_message:
                raise Exception("API_RATE_LIMITED")
            elif "invalid_api_key" in error_message or "authentication" in error_message.lower():
                raise Exception("API_KEY_INVALID")
            else:
                raise Exception(f"Failed to get AI response: {error_message}")

    def format_messages_for_api(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format chat history for the OpenAI API.
        
        Args:
            chat_history: List of message objects from the session
            
        Returns:
            Formatted messages list for OpenAI API
        """
        # Add system message at the beginning
        formatted_messages = [
            {
                "role": "system", 
                "content": (
                    "You are an AI assistant that is helpful, creative, clever, and very friendly. "
                    "Provide thoughtful and concise responses to the user's questions or comments. "
                    "If you don't know something, be honest about it rather than making up information."
                )
            }
        ]
        
        # Add all messages from chat history
        for message in chat_history:
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
            
        return formatted_messages
