# backend/models/signal.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


class SignalLocation(BaseModel):
    lat: float
    lng: float
    area_name: str
    precision: Literal["high", "medium", "low"] = "medium"


class VelocityContext(BaseModel):
    mentions_last_5min: int = 0
    trend: Literal["rising", "stable", "falling"] = "stable"


class RawSignal(BaseModel):
    """
    What comes IN from external sources — messy, variable format.
    Each source adapter transforms its raw data into this shape.
    """
    source_type: Literal["social", "weather", "sensor", "citizen_report", "field_report"]
    source_name: str
    raw_content: str
    location: SignalLocation
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional enrichment from source
    crisis_type_hint: Optional[str] = None
    extracted_keywords: list[str] = Field(default_factory=list)


class NormalizedSignal(BaseModel):
    """
    What the Ingestion Service produces — clean, scored, ready for agents.
    This is the contract between ingestion and the Antigravity layer.
    """
    signal_id: str = Field(default_factory=lambda: f"sig_{uuid.uuid4().hex[:8]}")
    source_type: Literal["social", "weather", "sensor", "citizen_report", "field_report"]
    source_name: str
    raw_content: str
    extracted_keywords: list[str] = Field(default_factory=list)
    crisis_type_hint: Optional[str] = None
    location: SignalLocation
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Computed by ingestion pipeline
    urgency_score: float = Field(ge=0.0, le=1.0, default=0.5)
    credibility_score: float = Field(ge=0.0, le=1.0, default=0.5)
    velocity_context: VelocityContext = Field(default_factory=VelocityContext)
    
    processed: bool = False
    
    class Config:
        # Allows datetime serialization to ISO format in JSON responses
        json_encoders = {datetime: lambda v: v.isoformat()}
