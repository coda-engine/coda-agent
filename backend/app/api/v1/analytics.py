from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text
from app.core.database import get_db
from app.models.session import Session
from app.models.message import Message
from app.schemas.analytics import AnalyticsOverview, ToolAnalytics, ToolUsage, DecisionAnalytics, DecisionUsage

router = APIRouter()

@router.get("/usage", response_model=AnalyticsOverview)
async def get_usage_analytics(db: AsyncSession = Depends(get_db)):
    # Total Sessions
    result = await db.execute(select(func.count(Session.id)))
    total_sessions = result.scalar() or 0
    
    # Total Messages
    result = await db.execute(select(func.count(Message.id)))
    total_messages = result.scalar() or 0
    
    # Total Tokens
    result = await db.execute(select(func.sum(Message.token_count)))
    total_tokens = result.scalar() or 0
    
    # Avg Execution Time
    result = await db.execute(select(func.avg(Message.execution_time)).where(Message.execution_time != None))
    avg_exec = result.scalar() or 0.0
    
    return AnalyticsOverview(
        total_sessions=total_sessions,
        total_messages=total_messages,
        total_tokens=total_tokens,
        avg_execution_time=round(float(avg_exec), 2)
    )

@router.get("/tools", response_model=ToolAnalytics)
async def get_tool_analytics(db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT 
            COALESCE(elem->'function'->>'name', 'Unknown') as tool_name, 
            COUNT(*) as count
        FROM messages, 
             jsonb_array_elements(CAST(tool_calls AS jsonb)) as elem
        WHERE tool_calls IS NOT NULL 
          AND jsonb_typeof(CAST(tool_calls AS jsonb)) = 'array'
        GROUP BY 1
        ORDER BY 2 DESC
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    usage = [ToolUsage(tool_name=row[0], count=row[1]) for row in rows]
    return ToolAnalytics(usage=usage)

@router.get("/decisions", response_model=DecisionAnalytics)
async def get_decision_analytics(db: AsyncSession = Depends(get_db)):
    # Aggregate tool usage first
    query = text("""
        SELECT 
            COALESCE(elem->'function'->>'name', 'Unknown') as tool_name, 
            COUNT(*) as count
        FROM messages, 
             jsonb_array_elements(CAST(tool_calls AS jsonb)) as elem
        WHERE tool_calls IS NOT NULL 
          AND jsonb_typeof(CAST(tool_calls AS jsonb)) = 'array'
        GROUP BY 1
    """)
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Classification Logic
    categories = {"Optimization": 0, "Statistical Analysis": 0, "General": 0}
    OPTIMIZATION_TOOLS = {'cp_sat', 'generic_vrp', 'linear_continuous', 'linear_sum_assignment', 'milp', 'min_cost_flow', 'simple_max_flow'}
    STATS_TOOLS = {'t_test'}
    
    for row in rows:
        name = row[0]
        count = row[1]
        if name in OPTIMIZATION_TOOLS:
            categories["Optimization"] += count
        elif name in STATS_TOOLS:
            categories["Statistical Analysis"] += count
        else:
            categories["General"] += count
            
    usage = [DecisionUsage(category=k, count=v) for k, v in categories.items() if v > 0]
    return DecisionAnalytics(usage=usage)
