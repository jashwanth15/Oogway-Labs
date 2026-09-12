from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Citation(BaseModel):
    episode_id: str
    guest: str
    title: str
    youtube_url: Optional[str] = None
    timestamp: Optional[str] = None
    snippet: str
    relevance_score: Optional[float] = None


class ArtifactPayload(BaseModel):
    id: Optional[str] = None
    title: str
    artifact_type: str = "markdown"  # markdown | html | code
    content: str


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    message_id: Optional[str] = None
    title: str
    artifact_type: str
    content: str
    created_at: datetime


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    created_at: datetime
    artifacts: Optional[List[ArtifactResponse]] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, description="User prompt or question")
    model: Optional[str] = Field(None, description="e.g. 'ollama:mistral', 'claude-3-5-sonnet', 'gpt-4o'")
    skill: Optional[str] = Field(None, description="Optional skill trigger: 'ship30', 'artifact', 'rag'")


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    guest_filter: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[Citation]
    total_found: int
