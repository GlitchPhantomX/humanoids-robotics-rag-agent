"""
Simple performance test to verify the optimizations work
"""
import asyncio
import time
from services.chat_service import ChatService
from models.chat_request import ChatRequest

async def test_performance_optimization():
    """Test that the performance optimizations work correctly"""
    print("Testing performance optimizations...")

    # Create chat service instance
    chat_service = ChatService.get_instance()

    # Test regular request
    print("1. Testing regular chat request...")
    request = ChatRequest(
        message="Hello, how are you?",
        selected_text=None
    )

    start_time = time.time()
    response = await chat_service.process_chat_request(request)
    end_time = time.time()

    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"   Regular request processing time: {processing_time:.2f}ms")
    print(f"   Response status: {response.status}")

    # Test selected text restriction
    print("2. Testing selected text restriction...")
    request_with_text = ChatRequest(
        message="What is AI?",
        selected_text="AI is artificial intelligence. It is a branch of computer science."
    )

    start_time = time.time()
    response_with_text = await chat_service.process_chat_request(request_with_text)
    end_time = time.time()

    processing_time_with_text = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"   Selected text request processing time: {processing_time_with_text:.2f}ms")
    print(f"   Response status: {response_with_text.status}")

    # Test streaming performance
    print("3. Testing streaming response performance...")
    streaming_request = ChatRequest(
        message="Hello, provide a short response",
        selected_text=None
    )

    start_time = time.time()
    chunks = []
    async for chunk in chat_service.process_chat_request_streaming(streaming_request):
        chunks.append(chunk)
        # Break after getting a few chunks to avoid waiting too long
        if chunk.get("type") == "done" or len(chunks) > 10:
            break
    end_time = time.time()

    streaming_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"   Streaming request processing time: {streaming_time:.2f}ms")
    print(f"   Number of chunks received: {len(chunks)}")

    # Test streaming with selected text
    print("4. Testing streaming with selected text...")
    streaming_request_with_text = ChatRequest(
        message="What is AI?",
        selected_text="AI is artificial intelligence and machine learning."
    )

    start_time = time.time()
    text_chunks = []
    async for chunk in chat_service.process_chat_request_streaming(streaming_request_with_text):
        text_chunks.append(chunk)
        if chunk.get("type") == "done" or len(text_chunks) > 10:
            break
    end_time = time.time()

    streaming_text_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"   Streaming with selected text processing time: {streaming_text_time:.2f}ms")
    print(f"   Number of chunks received: {len(text_chunks)}")

    # Summary
    print("\nPerformance Test Results:")
    print(f"- Regular request: {processing_time:.2f}ms")
    print(f"- Selected text request: {processing_time_with_text:.2f}ms")
    print(f"- Streaming request: {streaming_time:.2f}ms")
    print(f"- Streaming with selected text: {streaming_text_time:.2f}ms")

    # Check if performance meets requirements (<500ms)
    all_under_500ms = all(time < 500 for time in [
        processing_time,
        processing_time_with_text,
        streaming_time,
        streaming_text_time
    ])

    print(f"\nAll requests under 500ms: {all_under_500ms}")

    if all_under_500ms:
        print("[PASS] Performance optimization successful!")
        return True
    else:
        print("[FAIL] Performance optimization needs improvement!")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_performance_optimization())
    print(f"\nPerformance test completed. Success: {success}")