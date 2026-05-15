# backend/models/trace.py
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
import uuid


class AgentTrace(BaseModel):
    """
    Records every agent decision for the Trace Viewer in the Flutter app.
    This is what makes CIRO's reasoning visible — the key differentiator.
    """
    trace_id: str = Field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:8]}")
    incident_id: str
    agent: str  # "classification_agent", "resource_allocation_agent", etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    input_summary: str   # Human-readable description of what the agent received
    reasoning: str       # The agent's reasoning (from LLM or rule-based logic)
    output: dict         # The structured output produced
    
    decision: str        # e.g., "CLASSIFY_AND_RESPOND", "FLAG_FOR_VERIFICATION"
    next_agent: Optional[str] = None  # Which agent runs next
    
    latency_ms: int = 0
    model: Optional[str] = None  # "gemini-1.5-flash", "rule-based", etc.
    is_degraded: bool = False     # True if LLM failed and rules were used
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
