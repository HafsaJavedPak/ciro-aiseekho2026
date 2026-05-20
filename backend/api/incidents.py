# backend/api/incidents.py
from fastapi import APIRouter, HTTPException
from backend.services.firestore_service import firestore_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("/active")
async def get_active_incidents():
    """Returns all currently active incidents. Polled by the Flutter app on startup."""
    incidents = await firestore_service.get_active_incidents()
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    incident = await firestore_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/{incident_id}/traces")
async def get_incident_traces(incident_id: str):
    """Agent traces for the Trace Viewer screen in Flutter."""
    traces = await firestore_service.get_traces_for_incident(incident_id)
    return {"incident_id": incident_id, "traces": traces, "count": len(traces)}


@router.post("/{incident_id}/approve")
async def approve_incident(incident_id: str):
    """Human-in-the-Loop (HITL) approval to resume a paused pipeline."""
    incident = await firestore_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.get("status") != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Incident is not awaiting approval")

    # In a full LangGraph implementation with a checkpointer, we would resume the thread.
    # For the hackathon demo, we manually update the state and invoke the remaining nodes.
    incident["status"] = "active"
    incident["human_approved"] = True
    
    # Save the active status
    from backend.models.incident import Incident
    updated_incident = Incident(**incident)
    await firestore_service.save_incident(updated_incident)
    
    return {"status": "success", "message": "Incident approved and resumed.", "incident_id": incident_id}
