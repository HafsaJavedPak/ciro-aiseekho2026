# backend/models/allocation.py
from pydantic import BaseModel, Field
from typing import Dict, List

class ConflictDetails(BaseModel):
    resource: str
    needed: int
    assigned: int
    deficit: int
    reason: str

class AllocationResult(BaseModel):
    incident_id: str
    assigned: Dict[str, int]
    conflicts: List[ConflictDetails] = Field(default_factory=list)
