from backend.graph.state import IncidentState
from backend.models.agent_io import IncidentContext
from backend.utils.geospatial import is_within_cluster

async def fusion_node(state: IncidentState) -> dict:
    """Groups new signals into existing incidents or creates a new cluster."""
    new_signal = state["signal"]
    active_incidents = state.get("active_incidents", [])
    
    target_incident = None
    
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
        is_new = False
        target_id = target_incident.incident_id
        signals = [new_signal]
    else:
        is_new = True
        target_id = None
        signals = [new_signal]
        
    signal_types = list(set([s.source_type for s in signals]))
    incident_id_assigned = target_id if not is_new else f"inc_candidate_{new_signal.signal_id[-4:]}"
        
    context = IncidentContext(
        cluster_id=incident_id_assigned,
        signals=signals,
        center_location=new_signal.location,
        signal_types=signal_types,
        is_new_incident=is_new,
        target_incident_id=target_id
    )
    
    return {
        "context": context,
        "incident_id": incident_id_assigned,
        "agent_traces": [{"agent": "signal_fusion_agent", "decision": "APPEND_TO_EXISTING" if target_incident else "CREATE_NEW_CLUSTER", "status": "success"}]
    }
