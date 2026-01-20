"""
Input sanitization utility for chatbot requests
Provides functions to sanitize user inputs and prevent common security issues
"""
import re
import html
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

class InputSanitizer:
    """
    Utility class for sanitizing user inputs
    """

    @staticmethod
    def sanitize_text(text: Optional[str], max_length: int = 10000) -> Optional[str]:
        """
        Sanitize text input by removing dangerous characters and limiting length

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length for the text

        Returns:
            Sanitized text or None if input was None
        """
        if text is None:
            return None

        # Remove null bytes which can cause issues
        text = text.replace('\x00', '')

        # HTML encode dangerous characters
        text = html.escape(text)

        # Remove or replace control characters (except common whitespace)
        # Keep \n, \r, \t, and regular spaces
        text = re.sub(r'[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', text)

        # Limit length
        if len(text) > max_length:
            logger.warning(f"Text input truncated from {len(text)} to {max_length} characters")
            text = text[:max_length]

        return text.strip()

    @staticmethod
    def sanitize_message(message: Optional[str]) -> Optional[str]:
        """
        Sanitize message input with specific rules for chat messages

        Args:
            message: Message text to sanitize

        Returns:
            Sanitized message or None if input was None
        """
        if message is None:
            return None

        # Apply general sanitization
        sanitized = InputSanitizer.sanitize_text(message, max_length=2000)

        # Additional message-specific sanitization
        # Remove excessive whitespace but preserve meaningful formatting
        sanitized = re.sub(r'\s+', ' ', sanitized)

        return sanitized.strip()

    @staticmethod
    def sanitize_selected_text(selected_text: Optional[str]) -> Optional[str]:
        """
        Sanitize selected text input with specific rules

        Args:
            selected_text: Selected text to sanitize

        Returns:
            Sanitized selected text or None if input was None
        """
        if selected_text is None:
            return None

        # Apply general sanitization but with larger max length
        sanitized = InputSanitizer.sanitize_text(selected_text, max_length=10000)

        # Additional selected text-specific sanitization
        # Remove excessive whitespace but preserve formatting
        sanitized = re.sub(r'[ \t]+', ' ', sanitized)  # Multiple spaces/tabs to single space
        sanitized = re.sub(r'\n\s*\n', '\n\n', sanitized)  # Multiple newlines to max 2

        return sanitized.strip()

    @staticmethod
    def remove_xss_attempts(text: str) -> str:
        """
        Remove potential XSS attempts from text

        Args:
            text: Text to clean from XSS attempts

        Returns:
            Cleaned text
        """
        if not text:
            return text

        # Remove common XSS patterns
        xss_patterns = [
            r'javascript:',  # JavaScript protocol
            r'vbscript:',    # VBScript protocol
            r'on\w+\s*=',    # Event handlers like onclick, onload, etc.
            r'<script[^>]*>.*?</script>',  # Script tags
            r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
            r'<object[^>]*>.*?</object>',  # Object tags
            r'<embed[^>]*>.*?</embed>',    # Embed tags
        ]

        for pattern in xss_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        return text

    @staticmethod
    def validate_input_lengths(message: Optional[str], selected_text: Optional[str]) -> bool:
        """
        Validate that input lengths are within acceptable ranges

        Args:
            message: Message text to validate
            selected_text: Selected text to validate

        Returns:
            True if inputs are valid, False otherwise
        """
        if message and len(message) > 2000:
            logger.warning(f"Message exceeds maximum length: {len(message)} > 2000")
            return False

        if selected_text and len(selected_text) > 10000:
            logger.warning(f"Selected text exceeds maximum length: {len(selected_text)} > 10000")
            return False

        return True


# Convenience functions
def sanitize_message_input(message: Optional[str]) -> Optional[str]:
    """
    Convenience function to sanitize message input
    """
    return InputSanitizer.sanitize_message(message)


def sanitize_selected_text_input(selected_text: Optional[str]) -> Optional[str]:
    """
    Convenience function to sanitize selected text input
    """
    return InputSanitizer.sanitize_selected_text(selected_text)


def sanitize_text_input(text: Optional[str], max_length: int = 10000) -> Optional[str]:
    """
    Convenience function to sanitize general text input
    """
    return InputSanitizer.sanitize_text(text, max_length)