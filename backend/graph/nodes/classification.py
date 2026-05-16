import json
import google.generativeai as genai
from backend.graph.state import IncidentState
from backend.models.incident import CrisisClassification
from backend.config import settings

def _rule_based_fallback(context, cred) -> CrisisClassification:
    hint = context.signals[0].crisis_type_hint if context.signals else "unknown"
    confidence = 0.85 * cred.overall_confidence_multiplier
    return CrisisClassification(
        crisis_type=hint or "unknown",
        severity=3,
        confidence=confidence,
        reasoning="Rule-based fallback due to LLM failure/missing key.",
        affected_population=5000
    )

async def classification_node(state: IncidentState) -> dict:
    """Classifies crisis type and severity."""
    context = state["context"]
    cred = state["credibility_report"]
    
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    else:
        classification = _rule_based_fallback(context, cred)
        return {
            "classification": classification,
            "agent_traces": [{"agent": "classification_agent", "decision": "CLASSIFICATION_FAILED", "status": "fallback"}]
        }

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        signals_text = json.dumps([s.model_dump() for s in context.signals], default=str)
        prompt = f"""
        You are the Crisis Classification Agent of CIRO.
        INCIDENT CONTEXT:
        Location: {context.center_location.area_name}
        Signals: {signals_text}
        
        CREDIBILITY REPORT:
        Has Contradiction: {cred.has_contradiction}
        Details: {cred.contradiction_details}
        
        Provide JSON matching:
        - crisis_type: ["urban_flooding", "heatwave", "road_accident", "power_outage", "fire", "infrastructure_failure", "disease_cluster", "unknown"]
        - severity: 1 to 5
        - confidence: 0.0 to 1.0
        - reasoning: brief explanation
        - counter_hypothesis: if contradiction exists
        - affected_population: int
        """
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                response_mime_type="application/json",
            )
        )
        
        output_dict = json.loads(response.text)
        classification = CrisisClassification(**output_dict)
        
        return {
            "classification": classification,
            "status": "active" if classification.confidence >= 0.6 else "detecting",
            "agent_traces": [{"agent": "classification_agent", "decision": "CLASSIFIED", "status": "success"}]
        }
    except Exception as e:
        return {
            "classification": _rule_based_fallback(context, cred),
            "errors": [f"Classification Error: {str(e)}"],
            "agent_traces": [{"agent": "classification_agent", "decision": "FALLBACK", "status": "error"}]
        }
