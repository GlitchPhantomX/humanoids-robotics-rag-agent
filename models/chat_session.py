"""
Chat Session Model
Based on the data model specification
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ChatSession(BaseModel):
    """
    Represents a conversation session between user and chatbot
    """
    session_id: str = Field(..., description="Unique identifier for the chat session")
    user_id: Optional[str] = Field(None, description="Associated user (null for anonymous sessions)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the session started")
    last_message_at: datetime = Field(default_factory=datetime.utcnow, description="When the last message was sent")
    message_count: int = Field(default=0, ge=0, description="Number of messages in the session")
    active: bool = Field(default=True, description="Whether the session is currently active")

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"