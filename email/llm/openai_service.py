"""
OpenAI API service for LLM functionality
"""

import os
from openai import OpenAI
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import logging

from .models import LLMRequest, LLMResponse, ChatRequest, ChatResponse, ChatMessage, ChatRole

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIService:
    """Service class for OpenAI API interactions"""
    
    def __init__(self):
        """Initialize OpenAI service with API key"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Default model settings
        self.default_model = "gpt-4o"
        self.default_max_tokens = 10000
        self.default_temperature = 0.0
    
    def process_text_with_prompt(self, request: LLMRequest) -> LLMResponse:
        """
        Process text with a given prompt using OpenAI API
        
        Args:
            request: LLMRequest containing text, prompt, and parameters
            
        Returns:
            LLMResponse with the generated content or error
        """
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt if provided
            if request.prompt:
                messages.append({
                    "role": "system",
                    "content": request.prompt
                })
            
            # Add user text
            messages.append({
                "role": "user",
                "content": request.text
            })
            
            # Use custom messages if provided
            if request.messages:
                messages = [msg.dict() for msg in request.messages]
            
            # Prepare API parameters
            api_params = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature
            }
            
            # # Add max_tokens if specified
            # if request.max_tokens:
            #     api_params["max_tokens"] = request.max_tokens
            
            # Make API call
            logger.info(f"Making OpenAI API call with model: {request.model}")
            response = self.client.chat.completions.create(**api_params)
            
            # Extract response content
            content = response.choices[0].message.content
            model_used = response.model
            tokens_used = response.usage.total_tokens if response.usage else None
            
            logger.info(f"OpenAI API call successful. Tokens used: {tokens_used}")
            
            return LLMResponse(
                success=True,
                content=content,
                model_used=model_used,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            return LLMResponse(
                success=False,
                error=str(e)
            )
    
    
    def simple_completion(self, text: str, prompt: str = None, model: str = None) -> str:
        """
        Simple method for quick text completion
        
        Args:
            text: Input text to process
            prompt: Optional system prompt
            model: Optional model to use (defaults to gpt-4o)
            
        Returns:
            Generated text or error message
        """
        try:
            request = LLMRequest(
                text=text,
                prompt=prompt or "You are a helpful assistant.",
                model=model or self.default_model
            )
            
            response = self.process_text_with_prompt(request)
            
            if response.success:
                return response.content
            else:
                return f"Error: {response.error}"
                
        except Exception as e:
            logger.error(f"Simple completion failed: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models
        
        Returns:
            List of available model names
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data if model.id.startswith('gpt')]
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return ["gpt-4o", "gpt-4"]  # Fallback to common models
    
    def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key by making a simple test call
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            test_request = LLMRequest(
                text="Hello",
                prompt="Respond with 'API key is valid'",
                model="gpt-4o",
                max_tokens=10
            )
            
            response = self.process_text_with_prompt(test_request)
            return response.success
            
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False


# Global instance
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """Get global OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


if __name__ == "__main__":
    # Test the service
    service = OpenAIService()
    
    # Test simple completion
    result = service.simple_completion(
        text="What is the capital of France?",
        prompt="You are a geography expert. Answer concisely."
    )
    print(f"Simple completion result: {result}")
    
    # Test API key validation
    is_valid = service.validate_api_key()
    print(f"API key valid: {is_valid}")
