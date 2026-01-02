from sqlalchemy import String, DateTime, func, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
from app.core.database import Base
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .session import Session

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    
    role: Mapped[str] = mapped_column(String, nullable=False) # user, assistant, system, tool
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tool call data (JSON) - stores [{id, function: {name, arguments}, type}]
    tool_calls: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    
    # Tool result data (JSON) - stores the output or tool_call_id
    tool_call_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Observability
    token_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    execution_time: Mapped[Optional[float]] = mapped_column(nullable=True) # in seconds
    decision_count: Mapped[Optional[int]] = mapped_column(nullable=True) # Number of tool calls/decisions
    status: Mapped[Optional[str]] = mapped_column(nullable=True) # success, error, etc.
    feedback: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True) # { score: 1|-1, comment: str }
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
