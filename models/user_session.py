"""
User Session Model
Based on the data model specification
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserSession(BaseModel):
    """
    Represents an authenticated user session
    """
    user_id: str = Field(..., description="Unique identifier for the user")
    session_token: str = Field(..., description="Authentication token")
    expires_at: datetime = Field(..., description="When the session expires")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the session was created")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last interaction timestamp")

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"