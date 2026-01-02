from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.schemas.chat import ChatRequest
from app.services.llm.openai import OpenAIProvider
from app.core.prompts import get_system_prompt
from app.services.tools_bridge import tools_bridge
from app.core.database import get_db, async_session_factory
from app.models.session import Session
from app.models.message import Message as MessageModel
from app.models.message import Message as MessageModel
from app.services.summarizer import summarizer
import json
import time
from opentelemetry import trace

router = APIRouter()
tracer = trace.get_tracer(__name__)

@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    x_openai_api_key: str | None = Header(None, alias="X-OpenAI-API-Key"),
    x_anthropic_api_key: str | None = Header(None, alias="X-Anthropic-API-Key"),
    x_google_api_key: str | None = Header(None, alias="X-Google-API-Key"),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Provider Factory Logic
        model_id = request.model.lower()
        provider = None
        
        if "claude" in model_id:
            from app.services.llm.anthropic import AnthropicProvider
            provider = AnthropicProvider(api_key=x_anthropic_api_key)
        elif "gemini" in model_id:
            from app.services.llm.gemini import GoogleProvider
            provider = GoogleProvider(api_key=x_google_api_key)
        else:
            # Default to OpenAI
            provider = OpenAIProvider(api_key=x_openai_api_key)
        
        session_id = request.session_id
        session = None
        
        # 1. Handle Session
        if session_id:
            # Check if session exists
            try:
                # Handle string-to-UUID conversion if needed, though Pydantic usually handles it
                sess_uuid = UUID(session_id) if isinstance(session_id, str) else session_id
                session = await db.get(Session, sess_uuid)
            except ValueError:
                pass # Invalid UUID format
                
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # History loading moved to generate() for summarization support
            
        else:
            # Create new Session
            # Use the first message content as title (truncated)
            first_msg = request.messages[0].content if request.messages else "New Chat"
            title = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
            
            session = Session(title=title)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = str(session.id)
        
        # 2. Save User Message(s) to DB
        # We assume request.messages contains NEW input. 
        # If the frontend sends full history, we should potentially filter?
        # For this implementation, we assume the Frontend sends ONLY the new messages 
        # OR we rely on the fact that we loaded history and we append `request.messages`.
        # Standard Chat Interfaces often send full context. 
        # But we want to use the DB as the source of truth.
        # Decision: We will strictly APPEND `request.messages` to the DB and Context.
        # This implies the Frontend should only send the NEW user prompt in `request.messages`.
        
        new_db_msgs = []
        for m in request.messages:
            db_msg = MessageModel(
                session_id=session.id,
                role=m.role,
                content=m.content
            )
            db.add(db_msg)
            new_db_msgs.append(db_msg)
            
        await db.commit()
        
        # 3. Stream & Save
        async def generate():
            # We need a new DB session for saving the response since the dependency one closes
            accumulated_response = ""
            total_tokens = 0
            start_time = time.time()
            decision_count = 0
            accumulated_thoughts = []
            
            # Yield Session ID first
            yield f"data: {json.dumps({'session_id': str(session.id)})}\n\n"
            
            async with async_session_factory() as db_inner:
                # 3a. Load & Summarize Context
                # Reload session to get latest summary
                current_session = await db_inner.get(Session, session.id)
                summary = current_session.context_summary
                
                # Load Full History
                result = await db_inner.execute(
                    select(MessageModel)
                    .where(MessageModel.session_id == session.id)
                    .order_by(MessageModel.created_at)
                )
                history = result.scalars().all()
                
                # Summarization Logic
                HISTORY_LIMIT = 20 # Threshold to trigger summarization
                context_messages = []
                
                if len(history) > HISTORY_LIMIT:
                    # Report status
                    yield f"data: {json.dumps({'thought': 'Summarizing conversation history...'})}\n\n"
                    
                    # Keep recent N messages, summarize the rest
                    KEEP_RECENT = 10
                    to_summarize = history[:-KEEP_RECENT]
                    recent_history = history[-KEEP_RECENT:]
                    
                    # Generate Summary
                    new_summary = await summarizer.summarize(to_summarize, current_summary=summary)
                    
                    # Update Session
                    current_session.context_summary = new_summary
                    summary = new_summary
                    db_inner.add(current_session)
                    await db_inner.commit()
                    
                    yield f"data: {json.dumps({'thought': 'Context summary updated.'})}\n\n"
                    
                    # Prepare Context
                    history = recent_history

                # Build Prompt
                messages = [{"role": "system", "content": get_system_prompt()}]
                
                # Add Summary if exists
                if summary:
                   messages.append({"role": "system", "content": f"PREVIOUS CONVERSATION SUMMARY:\n{summary}"})
                   
                # Add History
                for m in history:
                    msg = {"role": m.role}
                    if m.content:
                        msg["content"] = m.content
                    if m.tool_calls:
                        msg["tool_calls"] = m.tool_calls
                    if m.tool_call_id:
                        msg["tool_call_id"] = m.tool_call_id
                    messages.append(msg)
                
                # 3b. Get Tools
                available_tools = tools_bridge.get_openai_tools()
                
                # 3c. Stream from Provider
                stream = provider.chat_completion(
                    messages=messages,
                    model=request.model,
                    stream=True,
                    tools=available_tools if available_tools else None
                )
                
                async for event in stream:
                    if not event:
                        continue
                        
                    event_type = event.get("type")
                    content = event.get("content")
                    
                    if event_type == "content":
                        if content:
                            accumulated_response += content
                            yield f"data: {json.dumps({'content': content})}\n\n"
                            
                    elif event_type in ["thought", "tool_start"]:
                        if content:
                            accumulated_thoughts.append(content)
                            yield f"data: {json.dumps({'thought': content})}\n\n"
                            
                    elif event_type == "usage":
                        usage = event.get("usage", {})
                        if usage:
                            count = usage.get("total_tokens", 0)
                            total_tokens += count
                            yield f"data: {json.dumps({'token_usage': count})}\n\n"
                            
                    elif event_type == "persist":
                        # Save intermediate message to DB
                        msg_data = event.get("msg")
                        if msg_data:
                            # Count decisions (tool calls)
                            if msg_data.get("tool_calls"):
                                 decision_count += len(msg_data["tool_calls"])
                                 
                            # Note: We are already in db_inner context
                            db_msg = MessageModel(
                                session_id=session.id,
                                role=msg_data["role"],
                                content=msg_data.get("content"),
                                tool_calls=msg_data.get("tool_calls"),
                                tool_call_id=msg_data.get("tool_call_id"),
                                status=msg_data.get("status"),
                                token_count=None
                            )
                            db_inner.add(db_msg)
                            await db_inner.commit()
                
                # Yield metrics BEFORE [DONE]
                duration = time.time() - start_time
                yield f"data: {json.dumps({'execution_time': duration, 'decision_count': decision_count})}\n\n"
                
                # Save the final assistant message
                db_msg = MessageModel(
                    session_id=session.id,
                    role="assistant",
                    content=accumulated_response,
                    token_count=total_tokens,
                    execution_time=duration,
                    decision_count=decision_count,
                    feedback={"thoughts": "\n".join(accumulated_thoughts)} if accumulated_thoughts else None
                )
                db_inner.add(db_msg)
                await db_inner.commit()
                await db_inner.refresh(db_msg)
                
                # Send the ID to the client
                yield f"data: {json.dumps({'message_id': str(db_msg.id)})}\n\n"
                
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
