# backend/agents/credibility.py
from typing import Any, Optional
from backend.agents.base import BaseAgent
from backend.models.agent_io import IncidentContext, CredibilityReport, SignalCredibility

class CredibilityAgent(BaseAgent):
    """
    Scores signals and detects contradictions across an IncidentContext.
    Currently rule-based.
    """
    
    @property
    def agent_name(self) -> str:
        return "credibility_agent"

    async def execute(self, incident_id: str, input_data: IncidentContext, **kwargs) -> tuple[CredibilityReport, str, str, Optional[str]]:
        
        signal_creds = []
        crisis_hints = set()
        
        for sig in input_data.signals:
            signal_creds.append(
                SignalCredibility(
                    signal_id=sig.signal_id,
                    score=sig.credibility_score,
                    reasoning=f"Base credibility score derived from {sig.source_type}"
                )
            )
            if sig.crisis_type_hint:
                crisis_hints.add(sig.crisis_type_hint)
                
        # Simple contradiction detection: if multiple distinct crisis hints exist in the cluster
        has_contradiction = len(crisis_hints) > 1
        contradiction_details = None
        multiplier = 1.0
        
        if has_contradiction:
            contradiction_details = f"Conflicting reports detected: {', '.join(crisis_hints)}"
            multiplier = 0.7  # Penalize overall confidence
            reasoning = "Multiple signals suggest conflicting crisis types. Contradiction flag set."
            decision = "CONTRADICTION_DETECTED"
        else:
            reasoning = "Signals are coherent with no detected contradictions."
            decision = "COHERENT_SIGNALS"
            
        report = CredibilityReport(
            signal_credibility=signal_creds,
            has_contradiction=has_contradiction,
            contradiction_details=contradiction_details,
            overall_confidence_multiplier=multiplier
        )
        
        return report, reasoning, decision, "classification_agent"

    def _summarize_input(self, input_data: IncidentContext) -> str:
        return f"Assessing credibility and conflicts for {len(input_data.signals)} signals in cluster."
