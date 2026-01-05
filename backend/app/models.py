"""
Pydantic models for API request/response.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class FeedbackType(str, Enum):
    """Feedback type enum."""
    POSITIVE = "positive"
    NEGATIVE = "negative"


class SearchMode(str, Enum):
    """Search mode enum."""
    TEXT = "text"
    IMAGE = "image"
    HYBRID = "hybrid"


# Request Models
class TextSearchRequest(BaseModel):
    """Text-based search request."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    top_k: int = Field(default=20, ge=1, le=500, description="Number of results to return")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking iterations")


class ImageSearchRequest(BaseModel):
    """Image-based search request (image file sent separately)."""
    top_k: int = Field(default=20, ge=1, le=500, description="Number of results to return")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking iterations")


class FeedbackItem(BaseModel):
    """Single feedback item."""
    image_id: str = Field(..., description="Image ID")
    feedback: FeedbackType = Field(..., description="Feedback type (positive/negative)")


class RelevanceFeedbackRequest(BaseModel):
    """Relevance feedback request."""
    session_id: str = Field(..., description="Session ID")
    feedback_items: list[FeedbackItem] = Field(default=[], description="List of feedback items")
    text_feedback: Optional[str] = Field(default=None, description="Optional natural language feedback")
    top_k: int = Field(default=20, ge=1, le=500, description="Number of results to return")


class PseudoFeedbackRequest(BaseModel):
    """Pseudo (blind) relevance feedback request."""
    session_id: str = Field(..., description="Session ID")
    top_m: int = Field(default=5, ge=1, le=20, description="Number of top results to assume relevant")
    top_k: int = Field(default=20, ge=1, le=500, description="Number of results to return")


# Response Models
class ImageResult(BaseModel):
    """Single image result."""
    image_id: str
    filename: str
    url: str
    similarity_score: float
    metadata: Optional[dict] = None


class QueryVector(BaseModel):
    """Query vector representation for visualization."""
    x: float
    y: float
    iteration: int


class SearchResponse(BaseModel):
    """Search response."""
    session_id: str
    iteration: int
    results: list[ImageResult]
    query_vectors: list[QueryVector]  # For visualization across iterations
    total_images: int


class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    iterations: int
    current_query_type: SearchMode
    feedback_counts: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    index_loaded: bool
    total_images: int

