#!/usr/bin/env python3
"""
Test script for the LLM service
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import OpenAIService, LLMRequest, ChatRequest, ChatMessage, ChatRole

# Load environment variables
load_dotenv()


class TestLLMService(unittest.TestCase):
    """Test cases for LLM service"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the OpenAI API key for testing
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            self.service = OpenAIService()
    
    def test_llm_request_validation(self):
        """Test LLM request model validation"""
        # Valid request
        request = LLMRequest(
            text="Test text",
            prompt="Test prompt"
        )
        self.assertEqual(request.text, "Test text")
        self.assertEqual(request.prompt, "Test prompt")
        self.assertEqual(request.model, "gpt-4o")  # Default value
        self.assertEqual(request.temperature, 0.7)  # Default value
    
    def test_chat_message_validation(self):
        """Test chat message model validation"""
        message = ChatMessage(
            role=ChatRole.USER,
            content="Hello"
        )
        self.assertEqual(message.role, ChatRole.USER)
        self.assertEqual(message.content, "Hello")
    
    def test_chat_request_validation(self):
        """Test chat request model validation"""
        messages = [
            ChatMessage(role=ChatRole.SYSTEM, content="You are helpful"),
            ChatMessage(role=ChatRole.USER, content="Hello")
        ]
        
        request = ChatRequest(messages=messages)
        self.assertEqual(len(request.messages), 2)
        self.assertEqual(request.model, "gpt-4o")  # Default value
    
    @patch('llm.openai_service.openai.OpenAI')
    def test_process_text_with_prompt_success(self, mock_openai):
        """Test successful text processing"""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.model = "gpt-4o"
        mock_response.usage.total_tokens = 50
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create service with mocked client
        service = OpenAIService()
        service.client = mock_client
        
        # Test request
        request = LLMRequest(
            text="Test text",
            prompt="Test prompt"
        )
        
        response = service.process_text_with_prompt(request)
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.model_used, "gpt-4o")
        self.assertEqual(response.tokens_used, 50)
    
    @patch('llm.openai_service.openai.OpenAI')
    def test_process_text_with_prompt_failure(self, mock_openai):
        """Test text processing failure"""
        # Mock the OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        # Create service with mocked client
        service = OpenAIService()
        service.client = mock_client
        
        # Test request
        request = LLMRequest(
            text="Test text",
            prompt="Test prompt"
        )
        
        response = service.process_text_with_prompt(request)
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertEqual(response.error, "API Error")
    
    def test_simple_completion(self):
        """Test simple completion method"""
        with patch.object(self.service, 'process_text_with_prompt') as mock_process:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.content = "Simple response"
            mock_process.return_value = mock_response
            
            result = self.service.simple_completion("Test", "Prompt")
            
            self.assertEqual(result, "Simple response")
            mock_process.assert_called_once()
    
    def test_simple_completion_error(self):
        """Test simple completion with error"""
        with patch.object(self.service, 'process_text_with_prompt') as mock_process:
            # Mock error response
            mock_response = MagicMock()
            mock_response.success = False
            mock_response.error = "API Error"
            mock_process.return_value = mock_response
            
            result = self.service.simple_completion("Test", "Prompt")
            
            self.assertEqual(result, "Error: API Error")
    
    def test_get_available_models(self):
        """Test getting available models"""
        with patch.object(self.service, 'client') as mock_client:
            # Mock models response
            mock_model1 = MagicMock()
            mock_model1.id = "gpt-4o"
            mock_model2 = MagicMock()
            mock_model2.id = "gpt-4"
            mock_model3 = MagicMock()
            mock_model3.id = "davinci"  # Non-GPT model
            
            mock_models = MagicMock()
            mock_models.data = [mock_model1, mock_model2, mock_model3]
            mock_client.models.list.return_value = mock_models
            
            models = self.service.get_available_models()
            
            # Should only return GPT models
            self.assertIn("gpt-4o", models)
            self.assertIn("gpt-4", models)
            self.assertNotIn("davinci", models)
    
    def test_validate_api_key(self):
        """Test API key validation"""
        with patch.object(self.service, 'process_text_with_prompt') as mock_process:
            # Mock successful validation
            mock_response = MagicMock()
            mock_response.success = True
            mock_process.return_value = mock_response
            
            is_valid = self.service.validate_api_key()
            
            self.assertTrue(is_valid)
            mock_process.assert_called_once()


def run_tests():
    """Run all tests"""
    print("🧪 Running LLM Service Tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLLMService)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} error(s) occurred")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
