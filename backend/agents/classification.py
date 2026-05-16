# backend/agents/classification.py
import json
import google.generativeai as genai
from typing import Any, Optional
from backend.agents.base import BaseAgent
from backend.models.agent_io import IncidentContext, CredibilityReport
from backend.models.incident import CrisisClassification
from backend.config import settings

class ClassificationAgent(BaseAgent):
    """
    Uses Gemini to classify the crisis type, severity, and confidence based on all signals.
    """
    
    @property
    def agent_name(self) -> str:
        return "classification_agent"

    @property
    def model_name(self) -> str:
        return "gemini-1.5-flash"

    async def execute(self, incident_id: str, input_data: dict, **kwargs) -> tuple[CrisisClassification, str, str, Optional[str]]:
        """
        input_data requires:
        - 'context': IncidentContext
        - 'credibility': CredibilityReport
        """
        context: IncidentContext = input_data['context']
        cred: CredibilityReport = input_data['credibility']
        
        # In a real setup, we configure this once in main.py, doing it here for safety
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        else:
            # Fallback if no API key is provided
            return self._rule_based_fallback(context, cred)

        model = genai.GenerativeModel("gemini-1.5-flash")
        
        signals_text = json.dumps([s.model_dump() for s in context.signals], default=str)
        
        prompt = f"""
        You are the Crisis Classification Agent of CIRO.
        Your task is to classify an unfolding event based on the incoming signals.
        
        INCIDENT CONTEXT:
        Location: {context.center_location.area_name} (Lat: {context.center_location.lat}, Lng: {context.center_location.lng})
        Signals: {signals_text}
        
        CREDIBILITY REPORT:
        Has Contradiction: {cred.has_contradiction}
        Details: {cred.contradiction_details}
        
        Provide a JSON response matching the required schema. Ensure you include:
        - crisis_type: must be one of ["urban_flooding", "heatwave", "road_accident", "power_outage", "fire", "infrastructure_failure", "disease_cluster", "unknown"]
        - severity: 1 to 5
        - confidence: 0.0 to 1.0 (apply the credibility report findings)
        - reasoning: brief explanation of your decision
        - counter_hypothesis: if there is a contradiction, what is the alternative theory?
        - affected_population: estimate based on the location (integer)
        """
        
        try:
            # We use generation_config to enforce JSON output (response_schema is supported in later SDK versions)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                )
            )
            
            output_dict = json.loads(response.text)
            classification = CrisisClassification(**output_dict)
            
            reasoning = f"LLM Classification: {classification.crisis_type} (Severity {classification.severity}, Conf {classification.confidence:.2f})"
            decision = "CLASSIFIED"
            next_agent = "severity_prediction_agent" # Proceed to next step in architecture
            
            return classification, reasoning, decision, next_agent
            
        except Exception as e:
            print(f"[ClassificationAgent] LLM failed: {e}. Using fallback.")
            return self._rule_based_fallback(context, cred)
            
    def _rule_based_fallback(self, context: IncidentContext, cred: CredibilityReport):
        """Fallback if API is down or key is missing."""
        hint = context.signals[0].crisis_type_hint if context.signals else "unknown"
        confidence = 0.85 * cred.overall_confidence_multiplier
        
        classification = CrisisClassification(
            crisis_type=hint or "unknown",
            severity=3,
            confidence=confidence,
            reasoning="Rule-based fallback due to LLM failure/missing key.",
            affected_population=5000
        )
        return classification, "Used rule-based fallback.", "CLASSIFICATION_FAILED", None

    def _summarize_input(self, input_data: dict) -> str:
        ctx = input_data.get('context')
        return f"Classifying {len(ctx.signals)} signals for {ctx.center_location.area_name}."
