"""
API Router for Chatbot endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
import logging
import json
import time
from uuid import uuid4

# Create router for chat endpoints
router = APIRouter(prefix="/chat", tags=["chat"])

# Import models from models directory
from ..models.chat_request import ChatRequest
from ..models.chat_response import ChatResponse
from ..services.chat_service import ChatService
from ..middleware.auth import authenticate_request
from ..middleware.rate_limit import apply_rate_limit
from ..utils.logger_config import log_api_request, get_logger

# Initialize logger
logger = logging.getLogger(__name__)

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    user_data: dict = Depends(authenticate_request),
    rate_limit: None = Depends(apply_rate_limit),
    chat_service: ChatService = Depends(ChatService.get_instance),
    request_id: str = None
):
    """
    Main chat endpoint that handles chat requests with authentication and selected text restriction
    """
    # Generate request ID if not provided
    if request_id is None:
        request_id = str(uuid4())

    # Extract user ID for logging
    user_id = user_data.get("user", {}).get("id") or user_data.get("userId") or "unknown"

    start_time = time.time()

    try:
        # Process the chat request through the service
        response = await chat_service.process_chat_request(request)

        duration = time.time() - start_time

        # Log successful API request
        enhanced_logger = get_logger(__name__, user_id)
        log_api_request(
            enhanced_logger,
            endpoint="/chat",
            method="POST",
            user_id=user_id,
            request_id=request_id,
            duration=duration,
            status_code=200,
            message="Chat request processed successfully"
        )

        return response
    except HTTPException as he:
        duration = time.time() - start_time
        enhanced_logger = get_logger(__name__, user_id)
        log_api_request(
            enhanced_logger,
            endpoint="/chat",
            method="POST",
            user_id=user_id,
            request_id=request_id,
            duration=duration,
            status_code=he.status_code,
            message=f"Chat request failed with HTTP {he.status_code}"
        )
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as ve:
        duration = time.time() - start_time
        enhanced_logger = get_logger(__name__, user_id)
        enhanced_logger.error(
            f"Validation error in chat endpoint: {str(ve)}",
            extra={'request_id': request_id, 'user_id': user_id}
        )
        log_api_request(
            enhanced_logger,
            endpoint="/chat",
            method="POST",
            user_id=user_id,
            request_id=request_id,
            duration=duration,
            status_code=400,
            message=f"Validation error: {str(ve)}"
        )
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(ve)}")
    except Exception as e:
        duration = time.time() - start_time
        enhanced_logger = get_logger(__name__, user_id)
        enhanced_logger.error(
            f"Error processing chat request: {str(e)}",
            extra={'request_id': request_id, 'user_id': user_id}
        )
        log_api_request(
            enhanced_logger,
            endpoint="/chat",
            method="POST",
            user_id=user_id,
            request_id=request_id,
            duration=duration,
            status_code=500,
            message=f"Internal server error: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    user_data: dict = Depends(authenticate_request),
    rate_limit: None = Depends(apply_rate_limit),
    chat_service: ChatService = Depends(ChatService.get_instance)
):
    """
    Streaming chat endpoint that returns responses as Server-Sent Events (SSE)
    """
    # Generate request ID
    request_id = str(uuid4())
    # Extract user ID for logging
    user_id = user_data.get("user", {}).get("id") or user_data.get("userId") or "unknown"

    start_time = time.time()

    async def event_generator():
        try:
            # Validate inputs before processing
            if not request.message or not request.message.strip():
                error_chunk = {
                    "type": "error",
                    "data": "Message cannot be empty",
                    "status": "error"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

            # Use the streaming method from chat service
            async for chunk in chat_service.process_chat_request_streaming(request):
                yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            duration = time.time() - start_time
            enhanced_logger = get_logger(__name__, user_id)
            enhanced_logger.error(
                f"Error in streaming chat request: {str(e)}",
                extra={'request_id': request_id, 'user_id': user_id}
            )
            log_api_request(
                enhanced_logger,
                endpoint="/chat/stream",
                method="POST",
                user_id=user_id,
                request_id=request_id,
                duration=duration,
                status_code=500,
                message=f"Streaming error: {str(e)}"
            )
            error_chunk = {
                "type": "error",
                "data": "An error occurred while processing your request. Please try again.",
                "status": "error"
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        finally:
            # Log completion
            duration = time.time() - start_time
            enhanced_logger = get_logger(__name__, user_id)
            log_api_request(
                enhanced_logger,
                endpoint="/chat/stream",
                method="POST",
                user_id=user_id,
                request_id=request_id,
                duration=duration,
                status_code=200,
                message="Streaming chat request completed"
            )
            # Send completion signal
            done_chunk = {
                "type": "done",
                "status": "complete"
            }
            yield f"data: {json.dumps(done_chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "X-RateLimit-Limit": str(getattr(request.state, 'rate_limit_limit', 10)),
            "X-RateLimit-Remaining": str(getattr(request.state, 'rate_limit_remaining', 10)),
            "X-RateLimit-Reset": str(getattr(request.state, 'rate_limit_reset', int(time.time()) + 60)),
        }
    )

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint that doesn't require authentication
    """
    from ..utils.performance_monitor import get_performance_stats
    import time

    # Get performance statistics
    perf_stats = get_performance_stats()

    # Basic health check - try to access key systems
    dependencies_healthy = True

    # This could be expanded to check database connections, external services, etc.
    # For now, we'll just return basic health status with performance metrics

    return {
        "status": "healthy",
        "service": "chat-api",
        "timestamp": time.time(),
        "version": "1.0.0",
        "dependencies": {
            "database": "not configured",  # Would check actual DB connection in real implementation
            "external_apis": "not configured"  # Would check actual API connections
        },
        "performance": perf_stats,
        "checks": {
            "response_time": "ok",
            "memory": "ok",  # Would check actual memory in real implementation
            "disk_space": "ok"  # Would check actual disk space in real implementation
        }
    }

@router.post("/session")
async def create_session():
    """
    Create a new chat session
    """
    # Implementation will be added in later phases
    pass

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get information about a specific chat session
    """
    # Implementation will be added in later phases
    pass