# backend/agents/simulation.py
from typing import Any, Optional, List
from backend.agents.base import BaseAgent
from backend.models.simulation import SimulationResult
from backend.models.allocation import AllocationResult
from backend.models.incident import Incident

ACTION_TEMPLATES = {
    "DISPATCH_RESCUE": {
        "before": {"coverage_pct": 0},
        "after_delta": {"coverage_pct": 80},
        "base_improvement": 15,
        "side_effects": ["Traffic slightly increased on access roads."]
    },
    "DISPATCH_MEDICAL": {
        "before": {"triage_capacity": 0},
        "after_delta": {"triage_capacity": 50},
        "base_improvement": 20,
        "side_effects": ["Local hospitals alerted for incoming patients."]
    }
}

class SimulationAgent(BaseAgent):
    """
    Computes before/after states for allocated resources.
    """
    @property
    def agent_name(self) -> str:
        return "simulation_agent"

    async def execute(self, incident_id: str, input_data: dict, **kwargs) -> tuple[List[SimulationResult], str, str, Optional[str]]:
        incident: Incident = input_data['incident']
        allocation: AllocationResult = input_data['allocation']
        
        simulations = []
        severity = incident.classification.severity if incident.classification else 1
        
        # Simulate rescue team impact
        if allocation.assigned.get("rescue_teams", 0) > 0:
            tmpl = ACTION_TEMPLATES["DISPATCH_RESCUE"]
            simulations.append(SimulationResult(
                action_type="DISPATCH_RESCUE_TEAM",
                before_state=tmpl["before"],
                after_state={"coverage_pct": min(100, tmpl["after_delta"]["coverage_pct"] * allocation.assigned["rescue_teams"])},
                response_time_improvement_min=tmpl["base_improvement"] * (1 + severity*0.1),
                side_effects=tmpl["side_effects"]
            ))
            
        # Simulate medical impact
        if allocation.assigned.get("ambulances", 0) > 0:
            tmpl = ACTION_TEMPLATES["DISPATCH_MEDICAL"]
            simulations.append(SimulationResult(
                action_type="DISPATCH_AMBULANCES",
                before_state=tmpl["before"],
                after_state={"triage_capacity": tmpl["after_delta"]["triage_capacity"] * allocation.assigned["ambulances"]},
                response_time_improvement_min=tmpl["base_improvement"],
                side_effects=tmpl["side_effects"]
            ))

        reasoning = f"Simulated impact of {len(simulations)} deployment actions."
        decision = "SIMULATION_COMPLETE"

        return simulations, reasoning, decision, "stakeholder_messaging_agent"

    def _summarize_input(self, input_data: dict) -> str:
        return f"Simulating impacts for {input_data['allocation'].assigned}"
