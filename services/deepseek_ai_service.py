"""
DeepSeek AI Service module for accessing DeepSeek models.
"""
import os
import logging
import json
import requests
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DeepSeekAIService:
    """Service for interacting with DeepSeek AI API."""
    
    def __init__(self):
        """Initialize the DeepSeek AI service with API key from environment variables."""
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat" # Default model
        
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not found in environment variables")
            
    def get_chat_response(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get a response from the DeepSeek API.
        
        Args:
            messages: A list of message objects with role and content keys
                     Example: [{"role": "user", "content": "Hello, how are you?"}]
        
        Returns:
            The text response from the AI
            
        Raises:
            Exception: If there's an error communicating with the DeepSeek API
        """
        if not self.api_key:
            raise Exception("DEEPSEEK_API_KEY_MISSING")
            
        try:
            logger.debug(f"Sending request to DeepSeek with {len(messages)} messages")
            
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            # Make the API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            # Check for errors
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("error", {}).get("message", "Unknown error")
                logger.error(f"DeepSeek API error: {error_message}")
                
                if "quota" in error_message.lower() or response.status_code == 429:
                    raise Exception("API_QUOTA_EXCEEDED")
                elif "invalid api key" in error_message.lower():
                    raise Exception("API_KEY_INVALID")
                else:
                    raise Exception(f"DeepSeek API error: {error_message}")
                    
            # Parse the response
            result = response.json()
            
            # Extract the response text
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not ai_response:
                logger.warning("Received an empty response from DeepSeek")
                return "I'm sorry, I couldn't generate a response."
                
            return ai_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error when communicating with DeepSeek API: {str(e)}")
            raise Exception(f"Failed to connect to DeepSeek API: {str(e)}")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error getting response from DeepSeek: {error_message}")
            
            # Re-raise specific errors
            if error_message in ["API_QUOTA_EXCEEDED", "API_KEY_INVALID", "DEEPSEEK_API_KEY_MISSING"]:
                raise
            else:
                raise Exception(f"Failed to get AI response: {error_message}")
    
    def format_messages_for_api(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format chat history for the DeepSeek API.
        
        Args:
            chat_history: List of message objects from the session
            
        Returns:
            Formatted messages list for DeepSeek API
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
        
        # Add all messages from chat history - DeepSeek uses the same format as OpenAI
        for message in chat_history:
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
            
        return formatted_messages