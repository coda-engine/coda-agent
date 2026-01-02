from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.session import Session
from app.models.message import Message
from app.schemas.session import SessionCreate, SessionRead, SessionWithMessages, ForkSessionRequest

router = APIRouter()

@router.get("/", response_model=List[SessionRead])
async def list_sessions(
    skip: int = 0, 
    limit: int = 50, 
    db: AsyncSession = Depends(get_db)
):
    query = select(Session).order_by(Session.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=SessionRead)
async def create_session(
    session_in: SessionCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Auto-generate title if not provided could be done here or later
    new_session = Session(title=session_in.title or "New Chat")
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

@router.get("/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    query = select(Session).options(selectinload(Session.messages)).where(Session.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return session

@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    query = select(Session).where(Session.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    await db.delete(session)
    await db.commit()
    return {"ok": True}

@router.post("/{session_id}/fork", response_model=SessionRead)
async def fork_session(
    session_id: UUID, 
    fork_req: ForkSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Original Session
    query = select(Session).where(Session.id == session_id)
    result = await db.execute(query)
    original_session = result.scalar_one_or_none()
    
    if not original_session:
        raise HTTPException(status_code=404, detail="Original session not found")
        
    # 2. Fetch Messages to Clone
    msgs_query = select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    msgs_result = await db.execute(msgs_query)
    messages = msgs_result.scalars().all()
    
    # Filter if message_id provided
    cutoff_time = None
    if fork_req.message_id:
        target = next((m for m in messages if m.id == fork_req.message_id), None)
        if target:
            cutoff_time = target.created_at
            
    # 3. Create New Session
    new_title = f"Fork of {original_session.title}"[:100]
    new_session = Session(title=new_title, context_summary=original_session.context_summary)
    db.add(new_session)
    await db.flush() # Get ID
    
    # 4. Clone Messages
    for msg in messages:
        if cutoff_time and msg.created_at > cutoff_time:
            continue
            
        new_msg = Message(
            session_id=new_session.id,
            role=msg.role,
            content=msg.content,
            tool_calls=msg.tool_calls,
            tool_call_id=msg.tool_call_id,
            status=msg.status,
            token_count=msg.token_count,
            execution_time=msg.execution_time,
            decision_count=msg.decision_count
        )
        db.add(new_msg)
        
    await db.commit()
    await db.refresh(new_session)
    
    return new_session

