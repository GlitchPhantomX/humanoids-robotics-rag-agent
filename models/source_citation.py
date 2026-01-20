"""
Source Citation Model
Based on the data model specification
"""
from pydantic import BaseModel, Field
from typing import Optional

class SourceCitation(BaseModel):
    """
    Represents a citation to the source document used in the response
    """
    title: str = Field(..., min_length=1, max_length=200, description="Title of the source document or section")
    page: str = Field(..., description="Page number or section identifier")
    url: Optional[str] = Field(None, description="URL to the source location")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0)")
    content_preview: Optional[str] = Field(None, description="Brief preview of the cited content")

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"