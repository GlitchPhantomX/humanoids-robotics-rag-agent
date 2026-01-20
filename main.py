"""
Backward Compatibility Entry Point
Maintains existing CLI functionality while allowing for new web features
"""
import sys
import os

# Add the app directory to path to import existing functionality
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def main():
    """
    Main entry point that maintains backward compatibility
    """
    print("🤖 RAG Chatbot - Backward Compatibility Mode")
    print("For interactive CLI mode, run: python cli.py --interactive")
    print("For single message mode, run: python cli.py 'your message'")
    print("For web server mode, run: uvicorn app.main:app --reload")
    print("\nThis maintains the original functionality while enabling new features.")


if __name__ == "__main__":
    main()
