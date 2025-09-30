#!/usr/bin/env python3
"""
Example usage of the LLM service
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path to import the llm module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import OpenAIService, LLMRequest, ChatRequest, ChatMessage, ChatRole

# Load environment variables
load_dotenv()


def main():
    """Demonstrate LLM service usage"""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        return
    
    try:
        # Initialize the service
        print("🚀 Initializing OpenAI service...")
        service = OpenAIService()
        
        # Test API key validation
        print("🔑 Validating API key...")
        if not service.validate_api_key():
            print("❌ API key validation failed")
            return
        print("✅ API key is valid")
        
        # Example 1: Simple text processing
        print("\n📝 Example 1: Simple text processing")
        print("-" * 50)
        
        request = LLMRequest(
            text="I love this new product! It's amazing and works perfectly.",
            prompt="Analyze the sentiment of this customer feedback. Respond with: Positive, Negative, or Neutral, followed by a brief explanation.",
            model="gpt-4o",
            max_tokens=100,
            temperature=0.3
        )
        
        response = service.process_text_with_prompt(request)
        
        if response.success:
            print(f"✅ Analysis: {response.content}")
            print(f"📊 Model: {response.model_used}")
            print(f"🔢 Tokens used: {response.tokens_used}")
        else:
            print(f"❌ Error: {response.error}")
        
        # Example 2: Simple completion
        print("\n💬 Example 2: Simple completion")
        print("-" * 50)
        
        result = service.simple_completion(
            text="What is the capital of France?",
            prompt="You are a geography expert. Answer concisely."
        )
        print(f"✅ Answer: {result}")
        
        # Example 3: Chat conversation
        print("\n🗣️ Example 3: Chat conversation")
        print("-" * 50)
        
        chat_request = ChatRequest(
            messages=[
                ChatMessage(role=ChatRole.SYSTEM, content="You are a helpful customer service assistant."),
                ChatMessage(role=ChatRole.USER, content="I have a problem with my order"),
                ChatMessage(role=ChatRole.ASSISTANT, content="I'm sorry to hear you're having an issue. Can you tell me more about what's wrong?"),
                ChatMessage(role=ChatRole.USER, content="The product arrived damaged")
            ],
            model="gpt-4o",
            temperature=0.7
        )
        
        chat_response = service.chat_completion(chat_request)
        
        if chat_response.success:
            print(f"✅ Assistant: {chat_response.message.content}")
            print(f"📊 Model: {chat_response.model_used}")
            print(f"🔢 Tokens used: {chat_response.tokens_used}")
        else:
            print(f"❌ Error: {chat_response.error}")
        
        # Example 4: Email analysis
        print("\n📧 Example 4: Email analysis")
        print("-" * 50)
        
        email_content = """
        Hi there,
        
        I'm writing to inquire about your solar panel installation services. 
        I'm interested in getting a quote for my home. Could you please send me 
        more information about your packages and pricing?
        
        Thanks,
        John Smith
        """
        
        email_request = LLMRequest(
            text=email_content,
            prompt="Analyze this email and determine the sender's intent. What are they trying to achieve?",
            model="gpt-4o",
            max_tokens=150,
            temperature=0.3
        )
        
        email_response = service.process_text_with_prompt(email_request)
        
        if email_response.success:
            print(f"✅ Intent Analysis: {email_response.content}")
            print(f"📊 Model: {email_response.model_used}")
            print(f"🔢 Tokens used: {email_response.tokens_used}")
        else:
            print(f"❌ Error: {email_response.error}")
        
        # Example 5: Get available models
        print("\n🔧 Example 5: Available models")
        print("-" * 50)
        
        models = service.get_available_models()
        print(f"✅ Available models: {', '.join(models[:5])}...")  # Show first 5 models
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
