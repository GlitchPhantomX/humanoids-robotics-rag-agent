# RAG Chatbot with Authentication and Advanced Features

This project implements a RAG (Retrieval-Augmented Generation) chatbot with authentication, selected text restriction, streaming responses, rate limiting, and comprehensive security features. It maintains backward compatibility with the existing CLI interface while adding new web-based functionality.

## Features

- **Authentication**: Enforced using existing auth-backend system
- **Selected Text Restriction**: Answers restricted to selected text content
- **Streaming Responses**: Real-time progressive response display
- **Rate Limiting**: Token-based rate limiting with sliding window algorithm
- **Input Sanitization**: Comprehensive input sanitization to prevent XSS and other attacks
- **Performance Monitoring**: Built-in performance tracking and metrics
- **Comprehensive Error Handling**: Robust error handling throughout the application
- **CLI Compatibility**: Maintains all existing CLI functionality
- **Web API**: FastAPI-based backend with SSE streaming

## CLI Usage (Backward Compatible)

The existing CLI functionality is preserved and can be used as before:

### Interactive Mode
```bash
python cli.py --interactive
# or
python cli.py -i
```

### Single Message Mode
```bash
python cli.py "Your question here"
```

### Alternative Entry Point
```bash
python main.py  # Shows available options
```

## Web API Usage

The new web API provides authenticated chat functionality with additional features:

### Start Web Server
```bash
uvicorn app.main:app --reload
# or
python -m uvicorn app.main:app --reload
```

### API Endpoints
- `POST /api/chat/` - Main chat endpoint with authentication, rate limiting, and input sanitization
- `POST /api/chat/stream` - Streaming chat endpoint with Server-Sent Events, rate limiting, and input sanitization
- `GET /api/chat/health` - Health check endpoint
- `GET /api/chat/health` - Health check endpoint with system status

## Security Features

### Authentication
- Session token validation via auth backend
- Support for both Authorization header and session cookies
- Secure session management

### Rate Limiting
- Sliding window rate limiting algorithm
- 10 requests per 60-second window per authenticated user
- Configurable limits
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Input Sanitization
- HTML encoding of dangerous characters
- Removal of control characters
- XSS prevention
- Length validation
- Message-specific sanitization rules
- Selected text-specific sanitization rules

### Error Handling
- Comprehensive error handling with appropriate HTTP status codes
- Safe error messages that don't expose internal details
- Structured error responses

## Performance Monitoring

The system includes built-in performance monitoring with:
- Response time tracking
- Average and 95th percentile response times
- Error rate monitoring
- Active request tracking
- Endpoint-specific metrics

## Architecture

### CLI Components
- `cli.py` - Main CLI entry point with interactive and single-message modes
- `app/agent.py` - Core RAG logic shared between CLI and web API

### Web API Components
- `api/chat.py` - FastAPI router with authentication, rate limiting, and error handling
- `services/chat_service.py` - Business logic layer with performance monitoring
- `models/chat_request.py` - Request data model
- `models/chat_response.py` - Response data model
- `middleware/auth.py` - Authentication validation
- `middleware/rate_limit.py` - Rate limiting middleware
- `utils/input_sanitizer.py` - Input sanitization utilities
- `utils/performance_monitor.py` - Performance monitoring utilities
- `utils/rate_limiter.py` - Rate limiting utilities

### Frontend Components
- `docusaurus/src/components/Chatbot/index.tsx` - React chatbot component
- `docusaurus/src/components/Chatbot/Chatbot.module.css` - Component styling

## Environment Variables

Create a `.env` file with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key
COHERE_API_KEY=your_cohere_api_key
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_URL=your_qdrant_url
AUTH_BACKEND_URL=http://localhost:8001  # Optional, defaults to http://localhost:8001
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (see above)

3. For CLI usage: Run commands directly with `python cli.py`

4. For web API: Start the server with `uvicorn app.main:app --reload`

## Backward Compatibility

All existing CLI functionality is preserved:
- Command-line arguments work exactly as before
- Interactive mode functions identically
- Response formatting remains unchanged
- Error handling is maintained

New features do not affect existing CLI behavior.

## Testing

The system includes comprehensive test suites:
- `test_cli_compatibility.py` - CLI compatibility tests
- `test_integration.py` - Integration tests for all user stories
- `test_cli_quick_verification.py` - Quick CLI verification tests

Run tests with:
```bash
python -m pytest
# or run specific test files
python test_cli_compatibility.py
python test_integration.py
```

## Performance Requirements

The system is optimized to meet the following performance requirements:
- Response times under 500ms for 95% of requests
- Proper rate limiting to prevent abuse
- Efficient input sanitization without significant performance impact
- Streaming responses for improved user experience