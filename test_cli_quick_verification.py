"""
Quick verification tests for CLI compatibility to ensure backward compatibility is maintained
"""
import sys
import os

# Add the rag-chatbot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_cli_imports():
    """Test that CLI modules can be imported without errors"""
    try:
        from cli import RAGChatbotCLI, main
        print("SUCCESS: CLI modules imported successfully")
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import CLI modules: {e}")
        return False

def test_cli_class_structure():
    """Test that CLI class has expected methods"""
    from cli import RAGChatbotCLI

    cli = RAGChatbotCLI
    methods = dir(cli)

    # Check for essential methods
    essential_methods = ['chat', 'interactive_mode', 'process_single_message']
    missing_methods = [method for method in essential_methods if method not in methods]

    if missing_methods:
        print(f"ERROR: Missing essential methods: {missing_methods}")
        return False

    print("SUCCESS: CLI class structure is correct")
    return True

def test_main_function_exists():
    """Test that main function exists in cli module"""
    from cli import main
    if not callable(main):
        print("ERROR: Main function is not callable")
        return False
    print("SUCCESS: Main function exists and is callable")
    return True

def test_cli_argument_parser():
    """Test that CLI argument parsing structure is preserved"""
    from cli import main

    # The main function should contain argument parsing logic
    import inspect
    source = inspect.getsource(main)

    # Check that it uses argparse (contains expected patterns)
    if 'ArgumentParser' not in source and 'argparse' not in source:
        print("ERROR: Argument parsing logic not found")
        return False

    print("SUCCESS: CLI argument parsing structure preserved")
    return True

def test_cli_backward_compatibility():
    """Test that CLI maintains backward compatibility patterns"""
    from cli import RAGChatbotCLI

    # Check that the CLI class has the expected interface
    methods = [name for name in dir(RAGChatbotCLI) if not name.startswith('_')]
    expected_methods = ['chat', 'interactive_mode', 'process_single_message']

    missing_methods = [method for method in expected_methods if method not in methods]
    if missing_methods:
        print(f"ERROR: Missing expected methods: {missing_methods}")
        return False

    print("SUCCESS: CLI maintains backward compatibility interface")
    return True

if __name__ == "__main__":
    print("Running quick CLI compatibility verification tests...")

    all_tests = [
        test_cli_imports,
        test_cli_class_structure,
        test_main_function_exists,
        test_cli_argument_parser,
        test_cli_backward_compatibility
    ]

    passed_tests = 0
    total_tests = len(all_tests)

    for test_func in all_tests:
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"FAILED: {test_func.__name__}")
        except Exception as e:
            print(f"ERROR in {test_func.__name__}: {e}")

    print(f"\nSUMMARY: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("SUCCESS: All CLI compatibility verification tests passed!")
    else:
        print("WARNING: Some compatibility tests failed - please review")