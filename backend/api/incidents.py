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
