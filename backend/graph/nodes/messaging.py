import json
import google.generativeai as genai
from backend.graph.state import IncidentState
from backend.config import settings

def _rule_based_fallback(classification, area_name):
    c_type = classification.crisis_type if classification else "crisis"
    return {
        "public_alert": f"ALERT: {c_type.replace('_', ' ').title()} in {area_name}. Please avoid the area and stay safe.",
        "hospital_alert": f"Heads up: {c_type.replace('_', ' ').title()} reported in {area_name}. Expect potential influx of patients.",
        "media_brief": f"Emergency services are responding to a {c_type.replace('_', ' ').title()} in {area_name}."
    }

async def messaging_node(state: IncidentState) -> dict:
    """Generates targeted alerts for stakeholders."""
    classification = state["classification"]
    allocation = state["allocation_plan"]
    context = state["context"]
    area_name = context.center_location.area_name if context else "Unknown Area"
    
    if not settings.GEMINI_API_KEY:
        msgs = _rule_based_fallback(classification, area_name)
        return {
            "messages": msgs,
            "status": "notified",
            "agent_traces": [{"agent": "messaging", "decision": "FALLBACK_USED", "status": "fallback"}]
        }

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-3.5-flash")
        
        prompt = f"""
        You are the Stakeholder Messaging Agent of CIRO.
        Generate 3 distinct alert messages for the following crisis:
        
        Crisis: {classification.crisis_type} (Severity {classification.severity})
        Location: {area_name}
        Allocated Resources: {allocation.assigned if allocation else 'Unknown'}
        
        Output a JSON object with exactly three string fields:
        - "public_alert": A calm, instructional warning for the general public in the area.
        - "hospital_alert": A brief, technical heads-up for local hospital trauma wards.
        - "media_brief": A short factual statement for news outlets.
        """
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
            )
        )
        msgs = json.loads(response.text)
        
        return {
            "messages": msgs,
            "status": "notified",
            "agent_traces": [{"agent": "messaging", "decision": "MESSAGES_GENERATED", "status": "success"}]
        }
    except Exception as e:
        msgs = _rule_based_fallback(classification, area_name)
        return {
            "messages": msgs,
            "status": "notified",
            "errors": [f"Messaging Error: {str(e)}"],
            "agent_traces": [{"agent": "messaging", "decision": "FALLBACK", "status": "error"}]
        }
