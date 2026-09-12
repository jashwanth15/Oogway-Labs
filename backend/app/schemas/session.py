from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.chat import ChatMessageResponse, ArtifactResponse


class SessionCreate(BaseModel):
    title: Optional[str] = "New Growth Session"
    model_used: Optional[str] = "ollama:mistral"
    meta_info: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    model_used: Optional[str] = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    model_used: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0


class SessionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    model_used: str
    created_at: datetime
    updated_at: datetime
    meta_info: Optional[Dict[str, Any]] = None
    messages: List[ChatMessageResponse] = []
    artifacts: List[ArtifactResponse] = []
