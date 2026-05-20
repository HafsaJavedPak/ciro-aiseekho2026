from backend.graph.state import IncidentState

def route_after_recovery(state: IncidentState) -> str:
    """Routes based on the recovery node's status."""
    status = state.get("status", "")
    if status == "retracted":
        return "END"
    return "CONTINUE"

def route_after_classification(state: IncidentState) -> str:
    """Routes based on the classification confidence."""
    classification = state.get("classification")
    if not classification:
        return "END"
    
    # HITL: Pause if human approval is needed
    if state.get("status") == "awaiting_approval":
        return "END"
        
    if classification.confidence < 0.6:
        # In a real system, this might route to a human-in-the-loop node
        # For our graph, if it's low confidence we just stop, or we could still allocate
        # Let's route to allocation anyway for the sake of the E2E demo, 
        # but mark as 'detecting' which happens in classification_node.
        return "CONTINUE"
    return "CONTINUE"
