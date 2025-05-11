"""
Local AI Service module that simulates AI responses when the API is unavailable.
"""
import logging
import random
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class LocalAIService:
    """Service for simulating AI responses when the OpenAI API is unavailable."""
    
    def __init__(self):
        """Initialize the local AI service."""
        self.responses = {
            "greeting": [
                "Hello! I'm a local AI assistant. The OpenAI service is currently unavailable, so I'm providing limited responses.",
                "Hi there! I'm operating in local mode because the OpenAI API is unavailable right now.",
                "Greetings! I'm a basic assistant running locally because the OpenAI service is down or quota exceeded."
            ],
            "question": [
                "I'm running in local mode due to API limitations. I can only provide basic responses at the moment.",
                "Since I'm running locally, I can't access the full AI capabilities. Please try again later when the API is available.",
                "I'm a basic local assistant with limited capabilities. The OpenAI API service is currently unavailable."
            ],
            "unknown": [
                "I'm sorry, I'm running in local mode with limited capabilities because the OpenAI API is unavailable.",
                "The OpenAI API is currently unavailable, so I can only offer basic responses.",
                "I'm operating in fallback mode due to API limitations. Please try again later for better assistance."
            ]
        }
        
    def get_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Get a simulated response for when the OpenAI API is unavailable.
        
        Args:
            messages: A list of message objects with role and content keys
        
        Returns:
            A simulated text response
        """
        if not messages:
            return random.choice(self.responses["unknown"])
        
        # Get the last user message
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            return random.choice(self.responses["unknown"])
            
        last_message = user_messages[-1]["content"].lower()
        
        # Check if it's a greeting
        if any(greeting in last_message for greeting in ["hello", "hi", "hey", "greetings", "olá", "oi"]):
            return random.choice(self.responses["greeting"])
            
        # Check if it's a question
        if any(question in last_message for question in ["?", "what", "why", "how", "when", "who", "where", "can you", "could you"]):
            return random.choice(self.responses["question"])
            
        # Default response
        return random.choice(self.responses["unknown"])
    
    def format_messages_for_api(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format chat history for processing.
        
        Args:
            chat_history: List of message objects from the session
            
        Returns:
            Formatted messages list 
        """
        # Simply return the messages in the format we expect
        formatted_messages = []
        for message in chat_history:
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
            
        return formatted_messages