import operator
from typing import TypedDict, Annotated, Optional, List, Dict, Any

class IncidentState(TypedDict):
    # Core Data
    signal: Any                      # NormalizedSignal
    incident_id: Optional[str]
    active_incidents: List[Any]      # List of Incident
    
    # Processed Context
    context: Optional[Any]           # IncidentContext
    credibility_report: Optional[Any]# CredibilityReport
    classification: Optional[Any]    # CrisisClassification
    allocation_plan: Optional[Any]   # AllocationResult
    simulations: Optional[List[Any]] # List of SimulationResult
    messages: Optional[Dict[str, str]]
    
    # Execution Lifecycle
    status: str                      # e.g. 'detecting', 'active', 'retracted', 'monitoring', 'error'
    retraction_message: Optional[str]
    
    # Reducers for appending data safely
    errors: Annotated[List[str], operator.add]
    agent_traces: Annotated[List[dict], operator.add]
