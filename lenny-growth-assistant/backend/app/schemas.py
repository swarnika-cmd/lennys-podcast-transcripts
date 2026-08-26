from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

# Citation structure
class Citation(BaseModel):
    guest: Optional[str] = None
    title: Optional[str] = None
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    chunk_index: int

# Message schemas
class MessageBase(BaseModel):
    role: str
    content: str
    citations: Optional[List[Citation]] = None

class MessageCreate(MessageBase):
    pass

class MessageOut(MessageBase):
    id: int
    session_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# Session schemas
class SessionBase(BaseModel):
    metadata: Optional[Dict[str, Any]] = None

class SessionCreate(SessionBase):
    pass

class SessionOut(BaseModel):
    id: UUID
    created_at: datetime
    messages: List[MessageOut] = []
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def from_sqlalchemy(cls, data: Any) -> Any:
        if hasattr(data, "session_metadata"):
            return {
                "id": data.id,
                "created_at": data.created_at,
                "messages": data.messages if hasattr(data, "messages") else [],
                "metadata": data.session_metadata
            }
        return data

    model_config = {
        "from_attributes": True
    }

# Request and Response schemas for chat
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None  # "ollama", "openai", "anthropic"
    mode: Optional[str] = "standard"  # "standard", "essay"

class ChatResponse(BaseModel):
    content: str
    citations: List[Citation]
    provider: str
    mode: str
