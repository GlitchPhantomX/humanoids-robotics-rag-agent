"""
Integration tests for CLI compatibility to ensure backward compatibility is maintained
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

# Add the rag-chatbot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_cli_imports():
    """Test that CLI modules can be imported without errors"""
    try:
        from cli import RAGChatbotCLI, main
        assert RAGChatbotCLI is not None
        assert main is not None
        print("SUCCESS: CLI modules imported successfully")
    except ImportError as e:
        print(f"ERROR: Failed to import CLI modules: {e}")
        raise

def test_cli_class_structure():
    """Test that CLI class has expected methods"""
    from cli import RAGChatbotCLI

    cli = RAGChatbotCLI
    methods = dir(cli)

    # Check for essential methods
    assert 'chat' in methods, "chat method missing"
    assert 'interactive_mode' in methods, "interactive_mode method missing"
    assert 'process_single_message' in methods, "process_single_message method missing"

    print("SUCCESS: CLI class structure is correct")

def test_cli_init_fails_without_api_key():
    """Test that CLI initialization fails without API key (as expected)"""
    # Temporarily remove OPENAI_API_KEY from environment
    original_key = os.environ.get('OPENAI_API_KEY')
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']

    try:
        from cli import RAGChatbotCLI
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY missing"):
            RAGChatbotCLI()
        print("SUCCESS: CLI properly fails without API key")
    finally:
        # Restore original key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key

@patch('cli.AsyncOpenAI')
@patch('cli.cohere.Client')
@patch('cli.QdrantClient')
def test_cli_init_with_mocked_dependencies(mock_qdrant, mock_cohere, mock_openai):
    """Test CLI initialization with mocked dependencies"""
    # Temporarily set a fake API key
    original_key = os.environ.get('OPENAI_API_KEY')
    os.environ['OPENAI_API_KEY'] = 'fake-key'

    try:
        from cli import RAGChatbotCLI

        # Mock the clients
        mock_openai_instance = MagicMock()
        mock_cohere_instance = MagicMock()
        mock_qdrant_instance = MagicMock()

        mock_openai.return_value = mock_openai_instance
        mock_cohere.return_value = mock_cohere_instance
        mock_qdrant.return_value = mock_qdrant_instance

        # Initialize CLI
        cli = RAGChatbotCLI()

        # Verify clients were created
        assert cli.client is not None
        assert cli.cohere_client is not None
        assert cli.qdrant is not None

        print("SUCCESS: CLI initializes with mocked dependencies")
    finally:
        # Restore original key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

@patch('cli.AsyncOpenAI')
@patch('cli.cohere.Client')
@patch('cli.QdrantClient')
def test_cli_chat_method_structure(mock_qdrant, mock_cohere, mock_openai):
    """Test that CLI chat method exists and has correct signature"""
    # Temporarily set a fake API key
    original_key = os.environ.get('OPENAI_API_KEY')
    os.environ['OPENAI_API_KEY'] = 'fake-key'

    try:
        from cli import RAGChatbotCLI

        # Mock the clients
        mock_openai_instance = MagicMock()
        mock_cohere_instance = MagicMock()
        mock_qdrant_instance = MagicMock()

        mock_openai.return_value = mock_openai_instance
        mock_cohere.return_value = mock_cohere_instance
        mock_qdrant.return_value = mock_qdrant_instance

        cli = RAGChatbotCLI()

        # Check that chat method exists and is async
        assert hasattr(cli, 'chat'), "chat method missing"
        assert asyncio.iscoroutinefunction(cli.chat), "chat method should be async"

        print("SUCCESS: CLI chat method has correct structure")
    finally:
        # Restore original key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

def test_main_function_exists():
    """Test that main function exists in cli module"""
    from cli import main
    assert callable(main), "main function should be callable"
    print("SUCCESS: Main function exists and is callable")

def test_cli_argument_parser():
    """Test that CLI argument parsing structure is preserved"""
    import argparse

    # We can't easily test argparse without mocking sys.argv,
    # but we can verify the main function structure exists
    from cli import main

    # The main function should contain argument parsing logic
    import inspect
    source = inspect.getsource(main)

    # Check that it uses argparse (contains expected patterns)
    assert 'ArgumentParser' in source or 'argparse' in source, "Argument parsing logic should exist"

    print("SUCCESS: CLI argument parsing structure preserved")

def test_cli_backward_compatibility():
    """Test that CLI maintains backward compatibility patterns"""
    from cli import RAGChatbotCLI

    # Check that the CLI class has the expected interface
    cli_instance = RAGChatbotCLI.__dict__

    # Look for expected methods that would be used in original functionality
    methods = [name for name in dir(RAGChatbotCLI) if not name.startswith('_')]
    assert 'chat' in methods
    assert 'interactive_mode' in methods
    assert 'process_single_message' in methods

    print("SUCCESS: CLI maintains backward compatibility interface")

if __name__ == "__main__":
    print("Running CLI compatibility integration tests...")

    test_cli_imports()
    test_cli_class_structure()
    test_cli_init_fails_without_api_key()
    test_cli_init_with_mocked_dependencies()
    test_cli_chat_method_structure()
    test_main_function_exists()
    test_cli_argument_parser()
    test_cli_backward_compatibility()

    print("\nSUCCESS: All CLI compatibility integration tests passed!")