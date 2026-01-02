from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    messages: List[Message]
    model: str = "gpt-4"
    stream: bool = True
