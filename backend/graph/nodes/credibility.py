from backend.graph.state import IncidentState
from backend.models.agent_io import CredibilityReport, SignalCredibility

async def credibility_node(state: IncidentState) -> dict:
    """Scores signals and detects contradictions."""
    context = state["context"]
    signal_creds = []
    crisis_hints = set()
    
    for sig in context.signals:
        signal_creds.append(
            SignalCredibility(
                signal_id=sig.signal_id,
                score=sig.credibility_score,
                reasoning=f"Base credibility score derived from {sig.source_type}"
            )
        )
        if sig.crisis_type_hint:
            crisis_hints.add(sig.crisis_type_hint)
            
    has_contradiction = len(crisis_hints) > 1
    contradiction_details = None
    multiplier = 1.0
    
    if has_contradiction:
        contradiction_details = f"Conflicting reports detected: {', '.join(crisis_hints)}"
        multiplier = 0.7
        decision = "CONTRADICTION_DETECTED"
    else:
        decision = "COHERENT_SIGNALS"
        
    report = CredibilityReport(
        signal_credibility=signal_creds,
        has_contradiction=has_contradiction,
        contradiction_details=contradiction_details,
        overall_confidence_multiplier=multiplier
    )
    
    return {
        "credibility_report": report,
        "agent_traces": [{"agent": "credibility_agent", "decision": decision, "status": "success"}]
    }
