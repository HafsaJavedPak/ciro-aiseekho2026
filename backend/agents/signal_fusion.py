# backend/agents/signal_fusion.py
import uuid
from typing import Any, List, Optional
from backend.agents.base import BaseAgent
from backend.models.agent_io import IncidentContext
from backend.models.signal import NormalizedSignal
from backend.models.incident import Incident
from backend.utils.geospatial import is_within_cluster

class SignalFusionAgent(BaseAgent):
    """
    Groups new signals into existing incidents or creates a new cluster.
    This is deterministic (rule-based), utilizing geospatial clustering.
    """
    
    @property
    def agent_name(self) -> str:
        return "signal_fusion_agent"

    async def execute(self, incident_id: str, input_data: dict, **kwargs) -> tuple[IncidentContext, str, str, Optional[str]]:
        """
        input_data should contain:
        - 'new_signal': NormalizedSignal
        - 'active_incidents': List[Incident]
        """
        new_signal: NormalizedSignal = input_data['new_signal']
        active_incidents: List[Incident] = input_data.get('active_incidents', [])
        
        target_incident: Optional[Incident] = None
        
        # Spatial Clustering Logic
        for incident in active_incidents:
            if is_within_cluster(
                new_signal.location.lat, new_signal.location.lng,
                incident.location.lat, incident.location.lng,
                threshold_km=1.5
            ):
                target_incident = incident
                break
                
        if target_incident:
            # Add to existing incident context
            is_new = False
            target_id = target_incident.incident_id
            signals = [] # In a real implementation we would fetch existing signals here, for now we just pass the new one
            signals.append(new_signal)
            reasoning = f"Signal matches active incident {target_id} within 1.5km radius."
            decision = "APPEND_TO_EXISTING"
        else:
            # Create new cluster
            is_new = True
            target_id = None
            signals = [new_signal]
            reasoning = "Signal location > 1.5km from any active incident. Creating new cluster."
            decision = "CREATE_NEW_CLUSTER"
            
        signal_types = list(set([s.source_type for s in signals]))
            
        context = IncidentContext(
            cluster_id=incident_id,
            signals=signals,
            center_location=new_signal.location, # Naive center for now
            signal_types=signal_types,
            is_new_incident=is_new,
            target_incident_id=target_id
        )
        
        return context, reasoning, decision, "credibility_agent"

    def _summarize_input(self, input_data: Any) -> str:
        sig = input_data.get('new_signal')
        return f"Evaluating new {sig.source_type} signal at {sig.location.area_name} against active incidents."
