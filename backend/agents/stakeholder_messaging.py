# backend/agents/stakeholder_messaging.py
import json
import google.generativeai as genai
from typing import Any, Optional, Dict
from backend.agents.base import BaseAgent
from backend.models.incident import Incident
from backend.config import settings

class StakeholderMessagingAgent(BaseAgent):
    """
    LLM Agent that generates targeted alerts for different stakeholders.
    """
    @property
    def agent_name(self) -> str:
        return "stakeholder_messaging_agent"

    @property
    def model_name(self) -> str:
        return "gemini-1.5-flash"

    async def execute(self, incident_id: str, input_data: dict, **kwargs) -> tuple[Dict[str, str], str, str, Optional[str]]:
        incident: Incident = input_data['incident']
        allocation = input_data.get('allocation')
        
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        else:
            return self._rule_based_fallback(incident)

        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        You are the Stakeholder Messaging Agent of CIRO.
        Generate 3 distinct alert messages for the following crisis:
        
        Crisis: {incident.classification.crisis_type} (Severity {incident.classification.severity})
        Location: {incident.location.area_name}
        Allocated Resources: {allocation.assigned if allocation else 'Unknown'}
        
        Output a JSON object with exactly three string fields:
        - "public_alert": A calm, instructional warning for the general public in the area.
        - "hospital_alert": A brief, technical heads-up for local hospital trauma wards.
        - "media_brief": A short factual statement for news outlets.
        """
        
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                )
            )
            output_dict = json.loads(response.text)
            
            reasoning = "Generated 3 distinct stakeholder messages using LLM."
            decision = "MESSAGES_GENERATED"
            return output_dict, reasoning, decision, None
            
        except Exception as e:
            print(f"[StakeholderMessagingAgent] LLM failed: {e}. Using fallback.")
            return self._rule_based_fallback(incident)

    def _rule_based_fallback(self, incident: Incident):
        c_type = incident.classification.crisis_type if incident.classification else "crisis"
        msgs = {
            "public_alert": f"ALERT: {c_type.replace('_', ' ').title()} in {incident.location.area_name}. Please avoid the area and stay safe.",
            "hospital_alert": f"Heads up: {c_type.replace('_', ' ').title()} reported in {incident.location.area_name}. Expect potential influx of patients.",
            "media_brief": f"Emergency services are responding to a {c_type.replace('_', ' ').title()} in {incident.location.area_name}."
        }
        return msgs, "Used rule-based fallback.", "FALLBACK_USED", None

    def _summarize_input(self, input_data: dict) -> str:
        return f"Generating messages for {input_data['incident'].incident_id}"
