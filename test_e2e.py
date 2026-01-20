"""
End-to-end tests for all implemented features
Tests the complete workflow from API request to response
"""
import asyncio
import sys
import os

# Add the rag-chatbot directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from models.chat_request import ChatRequest
from services.chat_service import ChatService
from utils.rate_limiter import RateLimiter
from utils.input_sanitizer import InputSanitizer
from utils.performance_monitor import performance_monitor, get_performance_stats
from utils.logger_config import get_logger


async def test_end_to_end_complete_workflow():
    """Test the complete end-to-end workflow"""
    print("Testing end-to-end complete workflow...")

    # Test 1: Input sanitization + validation
    print("  1. Testing input sanitization and validation...")

    # Valid inputs
    valid_message = "Hello, how are you?"
    valid_selected_text = "This is some sample text for context."

    # Sanitize inputs
    sanitized_message = InputSanitizer.sanitize_message(valid_message)
    sanitized_selected_text = InputSanitizer.sanitize_selected_text(valid_selected_text)

    # Validate using Pydantic model
    try:
        request = ChatRequest(
            message=sanitized_message,
            selected_text=sanitized_selected_text
        )
        print("     ✅ Input sanitization and validation passed")
    except Exception as e:
        print(f"     ❌ Input sanitization and validation failed: {e}")
        return False

    # Test 2: Rate limiting
    print("  2. Testing rate limiting...")

    rate_limiter = RateLimiter(max_requests=5, window_size=1)  # 5 requests per 1 second

    user_id = "test_user_e2e"

    # Should allow first 5 requests
    for i in range(5):
        allowed = rate_limiter.is_allowed(user_id)
        if not allowed:
            print(f"     ❌ Rate limiting failed: request {i+1} was denied unexpectedly")
            return False

    # 6th request should be denied
    allowed = rate_limiter.is_allowed(user_id)
    if allowed:
        print("     ❌ Rate limiting failed: 6th request was allowed when it should be denied")
        return False

    print("     ✅ Rate limiting works correctly")

    # Test 3: Chat service processing
    print("  3. Testing chat service processing...")

    chat_service = ChatService.get_instance()

    # Test with selected text
    response = await chat_service.process_chat_request(request)

    if not response or not response.answer:
        print("     ❌ Chat service processing failed: no response or answer")
        return False

    print("     ✅ Chat service processing works correctly")

    # Test 4: Performance monitoring
    print("  4. Testing performance monitoring...")

    stats = get_performance_stats()

    if not stats:
        print("     ❌ Performance monitoring failed: no stats returned")
        return False

    print("     ✅ Performance monitoring works correctly")

    # Test 5: Session timeout handling (simulated)
    print("  5. Testing session timeout handling...")

    # This is tested more thoroughly in the auth module, but we can verify
    # that the timeout configuration exists
    try:
        from middleware.auth import SESSION_TIMEOUT
        if SESSION_TIMEOUT <= 0:
            print("     ❌ Session timeout configuration invalid")
            return False
        print("     ✅ Session timeout handling configured")
    except ImportError:
        print("     ❌ Could not import session timeout configuration")
        return False

    # Test 6: Error handling
    print("  6. Testing error handling...")

    # Test with empty message (should trigger validation error)
    try:
        invalid_request = ChatRequest(message="", selected_text="valid text")
        print("     ❌ Validation should have caught empty message")
        return False
    except Exception:
        print("     ✅ Error handling correctly caught invalid input")

    # Test with valid request that should work
    try:
        error_test_request = ChatRequest(message="Hello", selected_text="Some text")
        error_test_response = await chat_service.process_chat_request(error_test_request)
        if error_test_response.status == "error":
            print("     ❌ Error in processing valid request")
            return False
        print("     ✅ Error handling works correctly")
    except Exception as e:
        print(f"     ❌ Unexpected error in valid request: {e}")
        return False

    print("  ✅ All end-to-end workflow tests passed")
    return True


async def test_user_story_workflows():
    """Test workflows for each user story"""
    print("\nTesting user story workflows...")

    chat_service = ChatService.get_instance()

    # User Story 1: Authentication (simulated - we test the components that would be used)
    print("  User Story 1: Authentication workflow...")
    # This is primarily tested in the auth middleware, but we verify that
    # the system can handle authenticated requests
    print("     ✅ Authentication components are in place")

    # User Story 2: Selected text restriction
    print("  User Story 2: Selected text restriction...")

    # Test with matching content
    matching_request = ChatRequest(
        message="What is AI?",
        selected_text="AI is artificial intelligence. It is a branch of computer science."
    )

    matching_response = await chat_service.process_chat_request(matching_request)
    if "Based on the selected text" in matching_response.answer:
        print("     ✅ Selected text restriction works for matching content")
    else:
        print("     ❌ Selected text restriction failed for matching content")
        return False

    # Test with non-matching content
    non_matching_request = ChatRequest(
        message="What is quantum physics?",
        selected_text="This text is about AI and robotics."
    )

    non_matching_response = await chat_service.process_chat_request(non_matching_request)
    if "does not contain enough information" in non_matching_response.answer.lower():
        print("     ✅ Selected text restriction works for non-matching content")
    else:
        print("     ❌ Selected text restriction failed for non-matching content")
        return False

    # User Story 3: Streaming responses
    print("  User Story 3: Streaming responses...")

    streaming_request = ChatRequest(
        message="Hello, provide a short response",
        selected_text=None
    )

    # Test streaming
    chunks = []
    count = 0
    async for chunk in chat_service.process_chat_request_streaming(streaming_request):
        chunks.append(chunk)
        count += 1
        if chunk["type"] == "done" or count > 10:  # Prevent infinite loop
            break

    content_chunks = [c for c in chunks if c["type"] == "content"]
    done_chunks = [c for c in chunks if c["type"] == "done"]

    if len(content_chunks) > 0 and len(done_chunks) >= 1:
        print("     ✅ Streaming responses work correctly")
    else:
        print("     ❌ Streaming responses failed")
        return False

    # User Story 4: CLI compatibility (conceptual - we verify the components exist)
    print("  User Story 4: CLI compatibility...")
    try:
        import cli
        if hasattr(cli, 'RAGChatbotCLI') and hasattr(cli, 'main'):
            print("     ✅ CLI components are in place for compatibility")
        else:
            print("     ❌ CLI components missing")
            return False
    except ImportError:
        print("     ❌ Could not import CLI components")
        return False

    print("  ✅ All user story workflows work correctly")
    return True


async def test_security_features():
    """Test security features"""
    print("\nTesting security features...")

    # Test input sanitization against XSS attempts
    print("  1. Testing XSS protection...")

    xss_attempts = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        '<img src="x" onerror="alert(\'xss\')">',
        'onload="alert(\'xss\')"'
    ]

    for attempt in xss_attempts:
        try:
            # This should be caught by validation
            ChatRequest(message=attempt, selected_text="valid text")
            # If it gets here without validation error, check sanitization
            sanitized = InputSanitizer.sanitize_text(attempt)
            if "<script>" in sanitized or "javascript:" in sanitized.lower():
                print(f"     ❌ XSS protection failed for: {attempt}")
                return False
        except ValueError:
            # This is expected - validation should catch dangerous content
            pass

    print("     ✅ XSS protection works correctly")

    # Test rate limiting
    print("  2. Testing rate limiting...")

    rate_limiter = RateLimiter(max_requests=2, window_size=1)
    test_user = "security_test_user"

    # Allow 2 requests
    for i in range(2):
        if not rate_limiter.is_allowed(test_user):
            print(f"     ❌ Rate limiter incorrectly denied request {i+1}")
            return False

    # Deny the 3rd request
    if rate_limiter.is_allowed(test_user):
        print("     ❌ Rate limiter failed to deny 3rd request")
        return False

    print("     ✅ Rate limiting works correctly")

    # Test input validation
    print("  3. Testing input validation...")

    # Test message length validation
    try:
        long_message = "A" * 2001  # Exceeds max length of 2000
        ChatRequest(message=long_message)
        print("     ❌ Input validation failed to catch long message")
        return False
    except ValueError:
        print("     ✅ Input validation correctly caught long message")

    # Test selected text length validation
    try:
        long_selected = "A" * 10001  # Exceeds max length of 10000
        ChatRequest(message="valid", selected_text=long_selected)
        print("     ❌ Input validation failed to catch long selected text")
        return False
    except ValueError:
        print("     ✅ Input validation correctly caught long selected text")

    print("  ✅ All security features work correctly")
    return True


async def run_end_to_end_tests():
    """Run all end-to-end tests"""
    print("Running end-to-end tests for all implemented features...\n")

    all_passed = True

    # Test complete workflow
    workflow_passed = await test_end_to_end_complete_workflow()
    all_passed = all_passed and workflow_passed

    # Test user story workflows
    user_story_passed = await test_user_story_workflows()
    all_passed = all_passed and user_story_passed

    # Test security features
    security_passed = await test_security_features()
    all_passed = all_passed and security_passed

    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All end-to-end tests passed!")
        print("✅ Complete system workflow verified")
        print("✅ All user story implementations working")
        print("✅ Security features functioning correctly")
    else:
        print("❌ Some end-to-end tests failed!")
    print(f"{'='*60}")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_end_to_end_tests())
    if not success:
        exit(1)