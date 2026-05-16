import copy
from backend.graph.state import IncidentState
from backend.models.allocation import AllocationResult, ConflictDetails
from backend.agents.resource_allocation import CRISIS_RESOURCE_REQUIREMENTS

async def allocation_node(state: IncidentState) -> dict:
    """Allocates resources to crises and resolves multi-crisis conflicts."""
    classification = state["classification"]
    active_incidents = state.get("active_incidents", [])
    
    # We will simulate resource state logic here instead of DB call for now,
    # or assume it's injected. For simplicity we mock a static resource state.
    resource_state = {
        "ambulances": {"available": 10},
        "rescue_teams": {"available": 5},
        "police_units": {"available": 10},
        "water_tankers": {"available": 2},
        "shelters": {"available": 2}
    }
    
    c_type = classification.crisis_type if classification else "unknown"
    c_sev = classification.severity if classification else 1
    
    reqs = CRISIS_RESOURCE_REQUIREMENTS.get(c_type, {}).get(c_sev, {"police_units": 1})
    
    assigned = {}
    conflicts = []
    
    for res_type, needed in reqs.items():
        if res_type not in resource_state: continue
        available = resource_state[res_type]["available"]
        if available >= needed:
            assigned[res_type] = needed
            resource_state[res_type]["available"] -= needed
        elif available > 0:
            assigned[res_type] = available
            conflicts.append(ConflictDetails(
                resource=res_type, needed=needed, assigned=available, deficit=needed-available,
                reason="Partial availability."
            ))
            resource_state[res_type]["available"] = 0
        else:
            assigned[res_type] = 0
            conflicts.append(ConflictDetails(
                resource=res_type, needed=needed, assigned=0, deficit=needed,
                reason="No resources available."
            ))
            
    has_conflicts = len(conflicts) > 0
    allocation_plan = AllocationResult(
        incident_id=state["incident_id"] or "temp", 
        assigned=assigned, 
        conflicts=conflicts
    )
    
    return {
        "allocation_plan": allocation_plan,
        "agent_traces": [{"agent": "resource_allocation", "decision": "PARTIAL_ALLOCATION" if has_conflicts else "FULL_ALLOCATION", "status": "success"}]
    }
