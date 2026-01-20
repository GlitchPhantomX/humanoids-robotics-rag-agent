"""
Chat Response Model
Based on the data model specification
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .source_citation import SourceCitation  # Import will be created next

class ChatResponse(BaseModel):
    """
    Represents the chatbot's response to a user query
    """
    id: str = Field(..., description="Unique identifier for the response")
    request_id: str = Field(..., description="Reference to the original request")
    answer: str = Field(..., max_length=10000, description="The chatbot's answer to the query")
    sources: Optional[List[SourceCitation]] = Field(None, description="Citations for RAG-based answers")
    status: str = Field(..., description="Status of the response (e.g., 'complete', 'streaming', 'error')")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the response was generated")
    stream_token: Optional[str] = Field(None, description="Token for streaming continuation")

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"