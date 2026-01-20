"""
CLI entry point for the RAG Chatbot
Maintains backward compatibility with existing CLI functionality
"""
import asyncio
import argparse
import sys
from typing import Optional
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
import cohere
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Import from existing modules
from app.agent import (
    get_embedding,
    retrieve_textbook,
    smart_agent_stream,
    OPENAI_API_KEY,
    COHERE_API_KEY,
    QDRANT_API_KEY,
    QDRANT_URL,
    COLLECTION_NAME
)

class RAGChatbotCLI:
    """
    CLI interface for the RAG Chatbot that maintains backward compatibility
    """

    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError("❌ OPENAI_API_KEY missing")

        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.cohere_client = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None
        self.qdrant = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        ) if QDRANT_API_KEY and QDRANT_URL else None

    async def chat(self, message: str):
        """
        Main chat function that processes user message and returns response
        """
        print(f"🤔 Processing: {message}")
        print("-" * 50)

        # Create a simple async generator to simulate streaming for CLI
        full_response = ""
        async for chunk_data in smart_agent_stream(message):
            # Parse the SSE data
            if chunk_data.startswith("data: "):
                data_str = chunk_data[6:]  # Remove "data: " prefix
                try:
                    data = json.loads(data_str)
                    if data.get('type') == 'content':
                        content = data.get('data', '')
                        if content and content != '[DONE]':
                            full_response += content
                            print(content, end='', flush=True)
                    elif data.get('type') == 'done':
                        break
                except json.JSONDecodeError:
                    # If it's not JSON, it might be raw content
                    if '[DONE]' not in data_str:
                        full_response += data_str
                        print(data_str, end='', flush=True)

        print("\n" + "-" * 50)
        return full_response

    async def interactive_mode(self):
        """
        Interactive chat mode
        """
        print("🤖 RAG Chatbot CLI - Interactive Mode")
        print("Type 'quit', 'exit', or 'q' to exit")
        print("-" * 50)

        while True:
            try:
                message = input("\n💬 You: ").strip()

                if message.lower() in ['quit', 'exit', 'q', '']:
                    print("👋 Goodbye!")
                    break

                await self.chat(message)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break

    async def process_single_message(self, message: str):
        """
        Process a single message (non-interactive mode)
        """
        await self.chat(message)


def main():
    parser = argparse.ArgumentParser(
        description="RAG Chatbot CLI - Maintain backward compatibility with existing functionality"
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send to the chatbot (interactive mode if not provided)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive chat mode"
    )

    args = parser.parse_args()

    try:
        chatbot = RAGChatbotCLI()
    except RuntimeError as e:
        print(f"❌ Error initializing chatbot: {e}")
        sys.exit(1)

    # Determine mode based on arguments
    if args.interactive or (not args.message and sys.stdin.isatty()):
        # Interactive mode
        asyncio.run(chatbot.interactive_mode())
    elif args.message:
        # Single message mode
        asyncio.run(chatbot.process_single_message(args.message))
    else:
        # Read from stdin if no message provided but not in interactive mode
        message = sys.stdin.read().strip()
        if message:
            asyncio.run(chatbot.process_single_message(message))
        else:
            print("❌ No message provided. Use --interactive for interactive mode or provide a message as an argument.")
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()