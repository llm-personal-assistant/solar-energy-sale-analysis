# LLM Service

A comprehensive OpenAI API integration service for text processing and analysis within the email service ecosystem.

## Features

- **Text Processing**: Process any text with custom prompts using OpenAI models
- **Chat Completion**: Handle multi-turn conversations with context
- **Email Analysis**: Pre-built analysis functions for email content
- **Model Management**: Support for multiple OpenAI models
- **Error Handling**: Robust error handling and logging
- **API Validation**: Health checks and API key validation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root with:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Integration

The LLM service can be integrated into your FastAPI application:

```python
from llm import llm_router

app = FastAPI()
app.include_router(llm_router)
```

## API Endpoints

**⚠️ Authentication Required**: All endpoints require a valid Bearer token in the Authorization header.

### Core Endpoints

#### POST `/llm/process`
Process text with a custom prompt.

**Request Body:**
```json
{
  "text": "Your input text here",
  "prompt": "Your system prompt or instruction",
  "model": "gpt-4o",
  "max_tokens": 150,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "content": "Generated response text",
  "model_used": "gpt-4o",
  "tokens_used": 45
}
```

#### POST `/llm/chat`
Handle chat-based conversations.

**Request Body:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "model": "gpt-4o",
  "max_tokens": 100,
  "temperature": 0.7
}
```

#### POST `/llm/simple`
Simple text completion endpoint.

**Query Parameters:**
- `text`: Input text to process
- `prompt`: System prompt (optional)
- `model`: OpenAI model to use (optional)

### Email Analysis Endpoints

#### POST `/llm/analyze-email`
Analyze email content with predefined prompts.

**Request Body:**
```json
{
  "email_content": "Email content to analyze",
  "analysis_type": "sentiment"
}
```

**Available Analysis Types:**
- `sentiment`: Analyze emotional tone
- `intent`: Determine sender's intent
- `summary`: Provide concise summary
- `key_points`: Extract key points
- `urgency`: Assess urgency level

#### GET `/llm/analysis-types`
Get available email analysis types.

### Utility Endpoints

#### GET `/llm/models`
Get list of available OpenAI models.

#### GET `/llm/health`
Health check endpoint to validate API key and service status.

## Usage Examples

### Python Code Examples

#### Basic Text Processing

```python
from llm import OpenAIService, LLMRequest

# Initialize service
service = OpenAIService()

# Create request
request = LLMRequest(
    text="Analyze this customer feedback",
    prompt="You are a customer service expert. Analyze the sentiment and provide insights.",
    model="gpt-4o",
    max_tokens=200,
    temperature=0.3
)

# Process request
response = service.process_text_with_prompt(request)

if response.success:
    print(f"Analysis: {response.content}")
    print(f"Tokens used: {response.tokens_used}")
else:
    print(f"Error: {response.error}")
```

#### Simple Completion

```python
from llm import OpenAIService

service = OpenAIService()

# Simple completion
result = service.simple_completion(
    text="What is the capital of France?",
    prompt="You are a geography expert. Answer concisely."
)

print(result)
```

#### Chat Conversation

```python
from llm import OpenAIService, ChatRequest, ChatMessage, ChatRole

service = OpenAIService()

# Create chat request
request = ChatRequest(
    messages=[
        ChatMessage(role=ChatRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=ChatRole.USER, content="Hello, how are you?"),
        ChatMessage(role=ChatRole.ASSISTANT, content="Hello! I'm doing well, thank you."),
        ChatMessage(role=ChatRole.USER, content="Can you help me with Python?")
    ],
    model="gpt-4o",
    temperature=0.7
)

# Get response
response = service.chat_completion(request)

if response.success:
    print(f"Assistant: {response.message.content}")
else:
    print(f"Error: {response.error}")
```

### cURL Examples

#### Process Text

```bash
curl -X POST "http://localhost:8000/llm/process" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "text": "This is a sample email about a product inquiry",
    "prompt": "Analyze the sentiment of this email",
    "model": "gpt-4o",
    "max_tokens": 100,
    "temperature": 0.3
  }'
```

#### Analyze Email

```bash
curl -X POST "http://localhost:8000/llm/analyze-email" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email_content": "Hi, I am interested in your solar panels. Can you send me more information?",
    "analysis_type": "intent"
  }'
```

#### Health Check

```bash
curl -X GET "http://localhost:8000/llm/health" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Authentication

All LLM endpoints require authentication using a Bearer token. The token must be obtained through the authentication service and included in the Authorization header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Getting an Access Token

1. **Sign up/Sign in** through the auth service:
   ```bash
   # Sign in
   curl -X POST "http://localhost:8000/auth/signin" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "your-email@example.com",
       "password": "your-password"
     }'
   ```

2. **Use the access_token** from the response in subsequent LLM API calls.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |

### Model Configuration

The service supports various OpenAI models:

- `gpt-4o` (default)
- `gpt-4`
- `gpt-4-turbo-preview`
- And other available models

### Parameters

- **temperature**: Controls randomness (0.0-2.0, default: 0.7)
- **max_tokens**: Maximum tokens in response (optional)
- **model**: OpenAI model to use (default: gpt-4o)

## Error Handling

The service includes comprehensive error handling:

- API key validation
- Rate limit handling
- Network error recovery
- Invalid request validation
- Detailed error logging

## Logging

The service uses Python's built-in logging with structured logging support:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Testing

Test the service functionality:

```python
# Run the service directly for testing
python openai_service.py
```

## Integration with Email Service

This LLM service is designed to integrate seamlessly with the email analysis workflow:

1. **Email Processing**: Analyze incoming emails for sentiment, intent, and urgency
2. **Content Generation**: Generate responses or summaries
3. **Classification**: Categorize emails automatically
4. **Insights**: Extract key information from email conversations

## Security Considerations

- Store API keys securely in environment variables
- Implement rate limiting for production use
- Monitor token usage and costs
- Validate all input data
- Use HTTPS in production

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your OpenAI API key is valid
3. Ensure you have sufficient API credits
4. Check the OpenAI API status page for service issues
