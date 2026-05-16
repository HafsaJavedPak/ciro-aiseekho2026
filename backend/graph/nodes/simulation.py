from backend.graph.state import IncidentState
from backend.models.simulation import SimulationResult
from backend.agents.simulation import ACTION_TEMPLATES

async def simulation_node(state: IncidentState) -> dict:
    """Computes before/after states for allocated resources."""
    allocation = state["allocation_plan"]
    classification = state["classification"]
    severity = classification.severity if classification else 1
    
    simulations = []
    
    if allocation.assigned.get("rescue_teams", 0) > 0:
        tmpl = ACTION_TEMPLATES["DISPATCH_RESCUE"]
        simulations.append(SimulationResult(
            action_type="DISPATCH_RESCUE_TEAM",
            before_state=tmpl["before"],
            after_state={"coverage_pct": min(100, tmpl["after_delta"]["coverage_pct"] * allocation.assigned["rescue_teams"])},
            response_time_improvement_min=tmpl["base_improvement"] * (1 + severity*0.1),
            side_effects=tmpl["side_effects"]
        ))
        
    if allocation.assigned.get("ambulances", 0) > 0:
        tmpl = ACTION_TEMPLATES["DISPATCH_MEDICAL"]
        simulations.append(SimulationResult(
            action_type="DISPATCH_AMBULANCES",
            before_state=tmpl["before"],
            after_state={"triage_capacity": tmpl["after_delta"]["triage_capacity"] * allocation.assigned["ambulances"]},
            response_time_improvement_min=tmpl["base_improvement"],
            side_effects=tmpl["side_effects"]
        ))
        
    return {
        "simulations": simulations,
        "agent_traces": [{"agent": "simulation", "decision": "SIMULATION_COMPLETE", "status": "success"}]
    }
