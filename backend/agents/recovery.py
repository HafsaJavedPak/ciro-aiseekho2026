# backend/agents/recovery.py
from typing import Any, Optional, Dict
from backend.agents.base import BaseAgent
from backend.models.incident import Incident
from backend.models.signal import NormalizedSignal

class RecoveryAgent(BaseAgent):
    """
    Monitors incoming signals against active incidents to detect false alarms
    and issue retractions.
    """
    @property
    def agent_name(self) -> str:
        return "recovery_agent"

    async def execute(self, incident_id: str, input_data: dict, **kwargs) -> tuple[Dict[str, str], str, str, Optional[str]]:
        incident: Incident = input_data['incident']
        new_signal: NormalizedSignal = input_data['new_signal']
        
        # Contradiction detection logic
        action_type = "CONFIRM"
        retraction_message = None
        reasoning = "New signal confirms or is neutral to current crisis classification."
        decision = "CONFIRMED"
        
        # If a highly credible field report explicitly contradicts the incident
        if new_signal.source_type == "field_report" and new_signal.credibility_score > 0.8:
            if new_signal.crisis_type_hint != incident.classification.crisis_type or "false alarm" in new_signal.raw_content.lower():
                action_type = "RETRACT"
                retraction_message = f"RETRACTION: Previous alert for {incident.location.area_name} is cancelled. Verified as false alarm by field personnel."
                reasoning = "High-credibility field report explicitly contradicts current classification. Initiating retraction."
                decision = "RETRACTED"
                incident.status = "false_alarm"
                incident.pipeline_stage = "resolved"

        elif new_signal.credibility_score < 0.4 and incident.classification.confidence < 0.5:
            # Degraded mode escalation
            action_type = "ESCALATE"
            reasoning = "System operating in degraded confidence mode. Manual verification required."
            decision = "FLAGGED_MANUAL"
            incident.status = "monitoring"

        output = {
            "action_type": action_type,
            "retraction_message": retraction_message
        }

        return output, reasoning, decision, None

    def _summarize_input(self, input_data: dict) -> str:
        return f"Checking signal {input_data['new_signal'].signal_id} against active incident {input_data['incident'].incident_id}."
