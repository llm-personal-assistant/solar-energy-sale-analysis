"""
FastAPI routes for LLM functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from .models import LLMRequest, LLMResponse
from .openai_service import OpenAIService, get_openai_service

# Import authentication dependencies
try:
    from ..auth.auth_routes import get_current_user_from_token
    from ..auth.models import UserResponse
    from ..email_service.email_service import EmailService
except ImportError:
    # Handle relative import issues
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from auth.auth_routes import get_current_user_from_token
    from auth.models import UserResponse
    from email_service.email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

email_service = EmailService()
# Create router
llm_router = APIRouter(prefix="/llm", tags=["LLM"])


@llm_router.get("/analysis/{lead_id}", response_model=LLMResponse)
async def process_text_with_prompt(
    lead_id: str,
    current_user: UserResponse = Depends(get_current_user_from_token),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Process text with a given prompt using OpenAI API
    
    **Authentication Required**: Bearer token must be provided in Authorization header
    
  
    """
    try:
        emails = await email_service.get_emails(
            user_id=current_user.id,
            lead_id=lead_id,
            limit=100
        )
        if len(emails) == 0:
            raise HTTPException(status_code=400, detail=f"No emails found for lead: {lead_id}")
        
        lead_text = ""
        for email in emails:
            if lead_text == "":
                lead_text = f"Subject: {email['subject']}\nSender: {email['sender']}\nReceiver: {email['receiver']}\nBody: {email['body']}\n\n"
            else:
                lead_text +=  f"Subject: {email['subject']}\nSender: {email['sender']}\nReceiver: {email['receiver']}\nBody: {email['body']}\n\n"

        lead_text = lead_text.strip()
        prompt = "Analyze the sentiment of the following email. Respond with: Positive, Negative, or Neutral, followed by a brief explanation."

        print(f"lead_text: {lead_text}")
        request = LLMRequest(
                text=lead_text,
                prompt=prompt,
                model="gpt-4o",
                max_tokens=10000,
                temperature=0.0
            )
        logger.info(f"User {current_user.email} processing text with prompt: {request.prompt[:50]}...")
        response = openai_service.process_text_with_prompt(request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@llm_router.post("/simple", response_model=dict)
async def simple_completion(
    text: str,
    current_user: UserResponse = Depends(get_current_user_from_token),
    prompt: str = "You are a helpful assistant.",
    model: str = "gpt-4o",
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Simple text completion endpoint
    
    **Authentication Required**: Bearer token must be provided in Authorization header
    
    - **text**: Input text to process
    - **prompt**: System prompt (optional, default: "You are a helpful assistant.")
    - **model**: OpenAI model to use (optional, default: gpt-4o)
    """
    try:
        logger.info(f"User {current_user.email} simple completion request for text: {text[:50]}...")
        result = openai_service.simple_completion(text, prompt, model)
        
        return {
            "success": True,
            "result": result,
            "model_used": model
        }
        
    except Exception as e:
        logger.error(f"Error in simple completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@llm_router.get("/models", response_model=List[str])
async def get_available_models(
    current_user: UserResponse = Depends(get_current_user_from_token),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Get list of available OpenAI models
    
    **Authentication Required**: Bearer token must be provided in Authorization header
    """
    try:
        models = openai_service.get_available_models()
        return models
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@llm_router.get("/health", response_model=dict)
async def health_check(
    current_user: UserResponse = Depends(get_current_user_from_token),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Health check endpoint to validate OpenAI API key and service status
    
    **Authentication Required**: Bearer token must be provided in Authorization header
    """
    try:
        is_valid = openai_service.validate_api_key()
        
        return {
            "status": "healthy" if is_valid else "unhealthy",
            "api_key_valid": is_valid,
            "service": "OpenAI LLM Service"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "api_key_valid": False,
            "service": "OpenAI LLM Service",
            "error": str(e)
        }


@llm_router.post("/analyze-email", response_model=LLMResponse)
async def analyze_email(
    email_content: str,
    current_user: UserResponse = Depends(get_current_user_from_token),
    analysis_type: str = "sentiment",
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Analyze email content with predefined prompts
    
    **Authentication Required**: Bearer token must be provided in Authorization header
    
    - **email_content**: The email content to analyze
    - **analysis_type**: Type of analysis (sentiment, intent, summary, key_points, urgency)
    """
    try:
        # Define analysis prompts
        prompts = {
            "sentiment": "Analyze the sentiment of the following email. Respond with: Positive, Negative, or Neutral, followed by a brief explanation.",
            "intent": "Analyze the intent of the following email. What is the sender trying to achieve? Respond with a brief summary.",
            "summary": "Provide a concise summary of the following email, highlighting the main points.",
            "key_points": "Extract the key points from the following email and list them as bullet points.",
            "urgency": "Analyze the urgency level of the following email. Respond with: High, Medium, or Low, followed by a brief explanation."
        }
        
        if analysis_type not in prompts:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid analysis type. Available types: {list(prompts.keys())}"
            )
        
        request = LLMRequest(
            text=email_content,
            prompt=prompts[analysis_type],
            model="gpt-4o",
            max_tokens=200,
            temperature=0.3
        )
        
        logger.info(f"User {current_user.email} analyzing email with type: {analysis_type}")
        response = openai_service.process_text_with_prompt(request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@llm_router.get("/analysis-types", response_model=dict)
async def get_analysis_types(
    current_user: UserResponse = Depends(get_current_user_from_token)
):
    """
    Get available email analysis types
    
    **Authentication Required**: Bearer token must be provided in Authorization header
    """
    return {
        "available_types": [
            "sentiment",
            "intent", 
            "summary",
            "key_points",
            "urgency"
        ],
        "descriptions": {
            "sentiment": "Analyze the emotional tone of the email",
            "intent": "Determine what the sender is trying to achieve",
            "summary": "Provide a concise summary of the main points",
            "key_points": "Extract and list the key points",
            "urgency": "Assess the urgency level of the email"
        }
    }
