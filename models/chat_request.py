"""
Chat Request Model
Based on the data model specification
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class ChatRequest(BaseModel):
    """
    Represents a user's query to the chatbot system
    """
    id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000, description="The user's question or message")
    selected_text: Optional[str] = Field(None, max_length=10000, description="Text selected by user that restricts the answer scope")
    user_id: Optional[str] = Field(None, min_length=1, max_length=255, description="Identifier of the authenticated user")
    session_token: Optional[str] = Field(None, min_length=10, max_length=500, description="Authentication session token")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When the request was made")
    streaming_enabled: bool = Field(default=False, description="Whether to stream the response")

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v.strip()) > 2000:
            raise ValueError('Message exceeds maximum length of 2000 characters')
        # Check for potentially dangerous content
        if re.search(r'<script|javascript:|vbscript:|on\w+\s*=|<iframe|<object|<embed', v, re.IGNORECASE):
            raise ValueError('Message contains potentially dangerous content')
        return v.strip()

    @field_validator('selected_text')
    @classmethod
    def validate_selected_text(cls, v):
        if v is not None:
            if len(v) > 10000:
                raise ValueError('Selected text exceeds maximum length of 10000 characters')
            # Check for potentially dangerous content
            if re.search(r'<script|javascript:|vbscript:|on\w+\s*=|<iframe|<object|<embed', v, re.IGNORECASE):
                raise ValueError('Selected text contains potentially dangerous content')
            return v.strip()
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if v is not None:
            if len(v) > 255:
                raise ValueError('User ID exceeds maximum length of 255 characters')
            # Basic format validation - should be alphanumeric with some common separators
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('User ID contains invalid characters')
        return v

    @field_validator('session_token')
    @classmethod
    def validate_session_token(cls, v):
        if v is not None:
            if len(v) < 10 or len(v) > 500:
                raise ValueError('Session token must be between 10 and 500 characters')
            # Basic format validation - should look like a token (alphanumeric with possible separators)
            if not re.match(r'^[a-zA-Z0-9._-]+$', v):
                raise ValueError('Session token contains invalid characters')
        return v