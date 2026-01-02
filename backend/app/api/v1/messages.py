from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.message import Message

router = APIRouter()

class FeedbackCreate(BaseModel):
    score: int  # 1 for up, -1 for down
    comment: Optional[str] = None

@router.post("/{message_id}/feedback")
async def create_feedback(
    message_id: UUID, 
    feedback: FeedbackCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Async query using select
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalars().first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Update feedback
    # Ensure message.feedback is a dict, default to empty
    current_feedback = message.feedback if message.feedback else {}
    
    # Update with new data
    # Use model_dump for Pydantic v2
    current_feedback.update(feedback.model_dump())
    
    # Reassign to trigger update
    # In SQLAlchemy, specialized types like JSONB might need explicit reassignment
    message.feedback = dict(current_feedback)
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return {"status": "success", "feedback": message.feedback}
