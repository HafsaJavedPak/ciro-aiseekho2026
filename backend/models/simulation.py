# backend/models/simulation.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any

class SimulationResult(BaseModel):
    action_type: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    response_time_improvement_min: float
    side_effects: List[str]
