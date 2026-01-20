"""
Chat Service Base
Handles the business logic for chat operations
"""
from typing import Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.chat_request import ChatRequest
from models.chat_response import ChatResponse
from utils.input_sanitizer import sanitize_message_input, sanitize_selected_text_input
from utils.performance_monitor import monitor_performance, start_performance_monitoring, end_performance_monitoring

class ChatService:
    """
    Base class for chat service functionality
    """

    def __init__(self):
        # Initialize any required dependencies
        pass

    @classmethod
    def get_instance(cls):
        """
        Singleton pattern to get chat service instance
        """
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    @monitor_performance(name="process_chat_request", endpoint="/chat")
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat request and return a response
        Implements selected text restriction logic when selected_text is provided
        """
        import uuid
        from datetime import datetime
        import logging
        import traceback

        # Initialize logger for error tracking
        logger = logging.getLogger(__name__)

        try:
            # Sanitize inputs
            message = sanitize_message_input(request.message)
            selected_text = sanitize_selected_text_input(request.selected_text)

            # Validate input after sanitization
            if not message or not message.strip():
                raise ValueError("Message cannot be empty")

            # Check if selected_text is provided for restriction
            if selected_text:
                # Implement selected text restriction logic
                # Try to answer based only on the provided selected_text
                answer = self._generate_answer_from_selected_text(message, selected_text)
            else:
                # Use regular RAG pipeline if no selected text restriction
                answer = self._generate_answer_from_rag(message)

            # Create response with appropriate status
            response = ChatResponse(
                id=str(uuid.uuid4()),
                request_id=request.id or str(uuid.uuid4()),
                answer=answer,
                status="complete",
                timestamp=datetime.utcnow()
            )

            return response
        except ValueError as ve:
            logger.error(f"Validation error in chat request: {str(ve)}")
            # Return a user-friendly error response
            return ChatResponse(
                id=str(uuid.uuid4()),
                request_id=request.id or str(uuid.uuid4()),
                answer="Invalid request: " + str(ve),
                status="error",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Unexpected error processing chat request: {str(e)}\n{traceback.format_exc()}")
            # Return a safe error response without exposing internal details
            return ChatResponse(
                id=str(uuid.uuid4()),
                request_id=request.id or str(uuid.uuid4()),
                answer="An error occurred while processing your request. Please try again.",
                status="error",
                timestamp=datetime.utcnow()
            )

    def _generate_answer_from_selected_text(self, message: str, selected_text: str) -> str:
        """
        Generate answer based only on the provided selected text
        If the selected text doesn't contain enough information to answer the question,
        return an appropriate message
        """
        # Convert both to lowercase for comparison
        lower_selected_text = selected_text.lower()
        lower_message = message.lower()

        # Check if the selected text contains information related to the question
        # This is a simplified approach - in a real implementation, we'd use semantic similarity
        message_keywords = set(lower_message.split())

        # Count how many keywords from the message appear in the selected text
        matched_keywords = [word for word in message_keywords if word in lower_selected_text]

        # If we have some keyword matches, try to construct an answer from the selected text
        if len(matched_keywords) > 0:
            # For now, return a portion of the selected text that seems relevant
            # In a real implementation, we'd use NLP techniques to extract relevant parts
            return f"Based on the selected text: {selected_text[:500]}{'...' if len(selected_text) > 500 else ''}"
        else:
            # If the selected text doesn't seem to contain relevant information
            return "The selected text does not contain enough information to answer this question. Please select text that is relevant to your question."

    @monitor_performance(name="process_chat_request_streaming", endpoint="/chat/stream")
    async def process_chat_request_streaming(self, request: ChatRequest):
        """
        Process a chat request and yield response chunks for streaming
        Implements selected text restriction logic when selected_text is provided
        """
        import uuid
        from datetime import datetime
        import asyncio
        import logging
        import traceback

        # Initialize logger for error tracking
        logger = logging.getLogger(__name__)

        try:
            # Sanitize inputs
            message = sanitize_message_input(request.message)
            selected_text = sanitize_selected_text_input(request.selected_text)

            # Validate input after sanitization
            if not message or not message.strip():
                error_chunk = {
                    "type": "error",
                    "data": "Message cannot be empty",
                    "status": "error",
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield error_chunk

            # Generate a request ID if not provided
            request_id = request.id or str(uuid.uuid4())

            # Check if selected_text is provided for restriction
            if selected_text:
                # Use the streaming version of selected text restriction
                async for chunk in self._generate_answer_from_selected_text_streaming(message, selected_text, request_id):
                    yield chunk
            else:
                # Use regular RAG pipeline if no selected text restriction
                async for chunk in self._generate_answer_from_rag_streaming(message, request_id):
                    yield chunk
        except Exception as e:
            logger.error(f"Unexpected error in streaming chat request: {str(e)}\n{traceback.format_exc()}")
            # Send error chunk and then completion
            error_chunk = {
                "type": "error",
                "data": "An error occurred while processing your request. Please try again.",
                "status": "error",
                "timestamp": datetime.utcnow().isoformat()
            }
            yield error_chunk
            # Send completion signal
            done_chunk = {
                "type": "done",
                "status": "complete",
                "timestamp": datetime.utcnow().isoformat()
            }
            yield done_chunk

    def _generate_answer_from_selected_text(self, message: str, selected_text: str) -> str:
        """
        Generate answer based only on the provided selected text
        If the selected text doesn't contain enough information to answer the question,
        return an appropriate message
        """
        # Convert both to lowercase for comparison
        lower_selected_text = selected_text.lower()
        lower_message = message.lower()

        # Check if the selected text contains information related to the question
        # This is a simplified approach - in a real implementation, we'd use semantic similarity
        message_keywords = set(lower_message.split())

        # Count how many keywords from the message appear in the selected text
        matched_keywords = [word for word in message_keywords if word in lower_selected_text]

        # If we have some keyword matches, try to construct an answer from the selected text
        if len(matched_keywords) > 0:
            # For now, return a portion of the selected text that seems relevant
            # In a real implementation, we'd use NLP techniques to extract relevant parts
            return f"Based on the selected text: {selected_text[:500]}{'...' if len(selected_text) > 500 else ''}"
        else:
            # If the selected text doesn't seem to contain relevant information
            return "The selected text does not contain enough information to answer this question. Please select text that is relevant to your question."

    async def _generate_answer_from_selected_text_streaming(self, message: str, selected_text: str, request_id: str):
        """
        Generate answer based only on the provided selected text with streaming
        Yields chunks of the response for streaming
        """
        import asyncio
        import json
        from datetime import datetime

        # Convert both to lowercase for comparison
        lower_selected_text = selected_text.lower()
        lower_message = message.lower()

        # Check if the selected text contains information related to the question
        message_keywords = set(lower_message.split())

        # Count how many keywords from the message appear in the selected text
        matched_keywords = [word for word in message_keywords if word in lower_selected_text]

        if len(matched_keywords) > 0:
            # Prepare the answer text
            answer_prefix = "Based on the selected text: "
            relevant_text = selected_text[:500] if len(selected_text) > 500 else selected_text
            full_answer = f"{answer_prefix}{relevant_text}{'...' if len(selected_text) > 500 else ''}"

            # Stream the response in chunks
            full_text = full_answer
            chunk_size = 20  # Increased chunk size for better performance

            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i + chunk_size]

                response_chunk = {
                    "type": "content",
                    "data": {
                        "id": f"chunk-{i}",
                        "request_id": request_id,
                        "content": chunk,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }

                yield response_chunk
                # Minimal delay for performance - only when necessary for streaming experience
                await asyncio.sleep(0.01)  # Reduced from 50ms to 10ms
        else:
            # Send a message indicating insufficient information
            insufficient_msg = "The selected text does not contain enough information to answer this question. Please select text that is relevant to your question."

            # Stream the response in chunks
            chunk_size = 20  # Increased chunk size for better performance

            for i in range(0, len(insufficient_msg), chunk_size):
                chunk = insufficient_msg[i:i + chunk_size]

                response_chunk = {
                    "type": "content",
                    "data": {
                        "id": f"chunk-{i}",
                        "request_id": request_id,
                        "content": chunk,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }

                yield response_chunk
                # Minimal delay for performance - only when necessary for streaming experience
                await asyncio.sleep(0.01)  # Reduced from 50ms to 10ms

    def _generate_answer_from_rag(self, message: str) -> str:
        """
        Generate answer using regular RAG pipeline (placeholder implementation)
        """
        # Placeholder implementation - this would connect to RAG in a real implementation
        return f"This is a placeholder response for: {message}. The full RAG implementation will be completed in later phases."

    async def _generate_answer_from_rag_streaming(self, message: str, request_id: str):
        """
        Generate answer using regular RAG pipeline with streaming
        Yields chunks of the response for streaming
        """
        import asyncio
        import json
        from datetime import datetime

        # Placeholder implementation - this would connect to RAG in a real implementation
        full_answer = f"This is a placeholder response for: {message}. The full RAG implementation will be completed in later phases."

        # Stream the response in chunks with optimized chunk size
        chunk_size = 20  # Increased chunk size for better performance

        for i in range(0, len(full_answer), chunk_size):
            chunk = full_answer[i:i + chunk_size]

            response_chunk = {
                "type": "content",
                "data": {
                    "id": f"chunk-{i}",
                    "request_id": request_id,
                    "content": chunk,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            yield response_chunk
            # Minimal delay for performance - only when necessary for streaming experience
            await asyncio.sleep(0.01)  # Reduced from 50ms to 10ms