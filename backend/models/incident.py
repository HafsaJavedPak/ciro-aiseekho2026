# backend/models/incident.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


class IncidentLocation(BaseModel):
    lat: float
    lng: float
    area_name: str
    affected_radius_km: float = 0.5


class CrisisClassification(BaseModel):
    """Output of the Classification Agent."""
    crisis_type: Literal[
        "urban_flooding", "heatwave", "road_accident",
        "power_outage", "fire", "infrastructure_failure",
        "disease_cluster", "unknown"
    ]
    severity: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    counter_hypothesis: Optional[str] = None
    counter_confidence: Optional[float] = None
    affected_population: int = 0


class Incident(BaseModel):
    """
    The core entity — represents a detected crisis event.
    Created when enough signals cluster together.
    Updated as new signals arrive and agents re-evaluate.
    """
    incident_id: str = Field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:8]}")
    status: Literal["detecting", "active", "monitoring", "resolved", "false_alarm", "notified", "awaiting_approval"] = "detecting"
    
    location: IncidentLocation
    classification: Optional[CrisisClassification] = None
    
    # Signal tracking
    signal_ids: list[str] = Field(default_factory=list)
    signal_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Agent pipeline state — tracks what has run
    pipeline_stage: Literal[
        "ingested", "fused", "classified",
        "severity_assessed", "resources_allocated",
        "simulated", "notified", "monitoring"
    ] = "ingested"
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
