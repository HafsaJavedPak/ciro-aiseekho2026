# backend/agents/resource_allocation.py
import copy
from typing import Any, Optional, Dict, List
from backend.agents.base import BaseAgent
from backend.models.allocation import AllocationResult, ConflictDetails
from backend.models.incident import Incident

# Static resource requirements mapping
CRISIS_RESOURCE_REQUIREMENTS = {
    "urban_flooding": {3: {"ambulances": 1, "rescue_teams": 1, "water_tankers": 0}, 4: {"ambulances": 2, "rescue_teams": 2, "water_tankers": 1}},
    "heatwave": {3: {"ambulances": 2, "shelters": 1}, 4: {"ambulances": 4, "shelters": 2}},
    "road_accident": {2: {"ambulances": 1, "police_units": 1}, 3: {"ambulances": 2, "police_units": 2}},
}

class ResourceAllocationAgent(BaseAgent):
    """
    Allocates resources to crises and resolves multi-crisis conflicts.
    Rule-based, prioritizing incidents by severity, confidence, and population.
    """
    
    @property
    def agent_name(self) -> str:
        return "resource_allocation_agent"

    def compute_priority(self, incident: Incident) -> float:
        severity = incident.classification.severity if incident.classification else 1
        confidence = incident.classification.confidence if incident.classification else 0.5
        pop_k = (incident.classification.affected_population if incident.classification else 0) / 1000
        
        return (severity * 0.35) + (confidence * 0.20) + (pop_k * 0.25)

    async def execute(self, incident_id: str, input_data: dict, **kwargs) -> tuple[AllocationResult, str, str, Optional[str]]:
        current_incident: Incident = input_data['incident']
        all_incidents: List[Incident] = input_data['active_incidents']
        resource_state: Dict[str, Any] = copy.deepcopy(input_data['resource_state'])
        
        # Sort all incidents by priority
        sorted_incidents = sorted(all_incidents, key=self.compute_priority, reverse=True)
        
        allocation_plan = None
        has_conflicts = False
        reasoning_lines = []
        
        # Allocate globally to detect conflicts realistically
        for incident in sorted_incidents:
            c_type = incident.classification.crisis_type if incident.classification else "unknown"
            c_sev = incident.classification.severity if incident.classification else 1
            
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
                        reason=f"Resource depleted by higher priority incident."
                    ))
                    resource_state[res_type]["available"] = 0
                else:
                    assigned[res_type] = 0
                    conflicts.append(ConflictDetails(
                        resource=res_type, needed=needed, assigned=0, deficit=needed,
                        reason="No resources available. Depleted."
                    ))
            
            if incident.incident_id == current_incident.incident_id:
                allocation_plan = AllocationResult(incident_id=incident.incident_id, assigned=assigned, conflicts=conflicts)
                has_conflicts = len(conflicts) > 0
                
        if has_conflicts:
            reasoning = "Multi-crisis conflict detected. Resources depleted by higher priority incidents."
            decision = "PARTIAL_ALLOCATION"
        else:
            reasoning = "Full resource allocation granted based on priority score."
            decision = "FULL_ALLOCATION"

        return allocation_plan, reasoning, decision, "simulation_agent"

    def _summarize_input(self, input_data: dict) -> str:
        inc = input_data['incident']
        return f"Allocating resources for {inc.classification.crisis_type} amongst {len(input_data['active_incidents'])} total crises."
