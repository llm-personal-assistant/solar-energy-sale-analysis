"""
Pydantic models for LLM API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ChatRole(str, Enum):
    """Chat message roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: ChatRole
    content: str


class LLMRequest(BaseModel):
    """Request model for LLM API calls"""
    text: str = Field(..., description="Input text to process")
    prompt: str = Field(..., description="System prompt or instruction")
    model: str = Field(default="gpt-4o", description="OpenAI model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens in response")
    temperature: float = Field(default=0.7, description="Temperature for response randomness (0.0-2.0)")
    messages: Optional[List[ChatMessage]] = Field(default=None, description="Custom message history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Analyze this email content for sentiment",
                "prompt": "You are an expert email analyst. Analyze the sentiment of the following text:",
                "model": "gpt-4o",
                "max_tokens": 150,
                "temperature": 0.3
            }
        }


class LLMResponse(BaseModel):
    """Response model for LLM API calls"""
    success: bool
    content: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    lead_id: Optional[str] = None
    lead_subject: Optional[str] = None
    lead_owner: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "content": "The email content shows a positive sentiment with enthusiastic language...",
                "model_used": "gpt-4o",
                "tokens_used": 45,
                "lead_id": "123",
                "lead_subject": "Hello, how are you?",
                "lead_sender": "John Doe",
                "lead_receiver": "Jane Doe"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat-based conversations"""
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    model: str = Field(default="gpt-4o", description="OpenAI model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens in response")
    temperature: float = Field(default=0.7, description="Temperature for response randomness (0.0-2.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "model": "gpt-4o",
                "max_tokens": 100,
                "temperature": 0.7
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat-based conversations"""
    success: bool
    message: Optional[ChatMessage] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": {
                    "role": "assistant",
                    "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
                },
                "model_used": "gpt-4o",
                "tokens_used": 25
            }
        }
