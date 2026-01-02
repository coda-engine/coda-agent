from typing import List
from pydantic import BaseModel

class AnalyticsOverview(BaseModel):
    total_sessions: int
    total_messages: int
    total_tokens: int
    avg_execution_time: float

class ToolUsage(BaseModel):
    tool_name: str
    count: int

class ToolAnalytics(BaseModel):
    usage: List[ToolUsage]

class DecisionUsage(BaseModel):
    category: str
    count: int

class DecisionAnalytics(BaseModel):
    usage: List[DecisionUsage]
