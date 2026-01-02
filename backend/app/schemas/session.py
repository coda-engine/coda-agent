from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class SessionBase(BaseModel):
    title: Optional[str] = None
    
class SessionCreate(SessionBase):
    pass

class ForkSessionRequest(BaseModel):
    message_id: Optional[UUID] = None # If null, fork entire session

class SessionRead(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MessageRead(BaseModel):
    id: UUID
    role: str
    content: Optional[str] = None
    created_at: datetime
    tool_calls: Optional[List[dict]] = None
    token_count: Optional[int] = None
    execution_time: Optional[float] = None
    decision_count: Optional[int] = None
    status: Optional[str] = None
    feedback: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)

class SessionWithMessages(SessionRead):
    messages: List[MessageRead] = []
