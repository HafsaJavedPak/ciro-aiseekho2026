# backend/models/agent_io.py
from pydantic import BaseModel
from typing import List, Optional
from backend.models.signal import NormalizedSignal, SignalLocation

class IncidentContext(BaseModel):
    """
    Output of the Signal Fusion Agent.
    Groups signals that belong together before an Incident is officially created or updated.
    """
    cluster_id: str
    signals: List[NormalizedSignal]
    center_location: SignalLocation
    signal_types: List[str]
    is_new_incident: bool = True
    target_incident_id: Optional[str] = None


class SignalCredibility(BaseModel):
    signal_id: str
    score: float
    reasoning: str


class CredibilityReport(BaseModel):
    """
    Output of the Credibility & Conflict Agent.
    Scores each signal and flags any contradictions.
    """
    signal_credibility: List[SignalCredibility]
    has_contradiction: bool = False
    contradiction_details: Optional[str] = None
    overall_confidence_multiplier: float = 1.0
