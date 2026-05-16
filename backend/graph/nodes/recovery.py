from backend.graph.state import IncidentState

async def recovery_node(state: IncidentState) -> dict:
    """Monitors signals against active incidents for false alarms."""
    new_signal = state["signal"]
    context = state["context"]
    active_incidents = state.get("active_incidents", [])
    
    if context.is_new_incident:
        return {"agent_traces": [{"agent": "recovery_agent", "decision": "CONFIRMED", "status": "success"}]}
        
    incident = next((i for i in active_incidents if i.incident_id == context.target_incident_id), None)
    if not incident:
        return {"agent_traces": [{"agent": "recovery_agent", "decision": "CONFIRMED", "status": "success"}]}

    action_type = "CONFIRM"
    retraction_message = None
    decision = "CONFIRMED"
    status_update = "detecting"
    
    if new_signal.source_type == "field_report" and new_signal.credibility_score > 0.8:
        if new_signal.crisis_type_hint != (incident.classification.crisis_type if incident.classification else "") or "false alarm" in new_signal.raw_content.lower():
            action_type = "RETRACT"
            retraction_message = f"RETRACTION: Previous alert for {incident.location.area_name} is cancelled. Verified as false alarm by field personnel."
            decision = "RETRACTED"
            status_update = "retracted"
    elif new_signal.credibility_score < 0.4 and (incident.classification.confidence if incident.classification else 0) < 0.5:
        action_type = "ESCALATE"
        decision = "FLAGGED_MANUAL"
        status_update = "monitoring"

    return {
        "status": status_update if action_type != "CONFIRM" else state.get("status", "detecting"),
        "retraction_message": retraction_message,
        "agent_traces": [{"agent": "recovery_agent", "decision": decision, "action": action_type, "status": "success"}]
    }
