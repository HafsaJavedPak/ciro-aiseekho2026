# backend/services/firestore_service.py
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from backend.config import settings
from backend.models.signal import NormalizedSignal
from backend.models.incident import Incident
from backend.models.trace import AgentTrace


def _initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    Checks if already initialized (important — calling this twice crashes).
    """
    if firebase_admin._apps:
        return  # Already initialized
    
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        try:
            cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
        except Exception:
            print("[Firestore] No credentials found — using mock mode")
            return
    else:
        # Development: try credentials file, fall back to emulator
        try:
            cred = credentials.Certificate("firebase-credentials.json")
        except Exception:
            print("[Firestore] No credentials found — using mock mode")
            return
    
    firebase_admin.initialize_app(cred, {
        "projectId": settings.FIREBASE_PROJECT_ID
    })


class FirestoreService:
    """
    All database operations in one place.
    
    Collection structure mirrors the architecture spec:
    /incidents/{id}
    /incidents/{id}/signals/{id}
    /incidents/{id}/traces/{id}
    /incidents/{id}/allocations/{id}
    /resources/current_state
    """
    
    def __init__(self):
        _initialize_firebase()
        try:
            self._db = firestore.client()
            self._available = True
        except Exception as e:
            print(f"[Firestore] Not available: {e}. Using in-memory fallback.")
            self._db = None
            self._available = False
            # In-memory store for development without Firebase
            self._memory: dict = {
                "incidents": {},
                "signals": {},
                "traces": [],
            }
    
    # ---- Incident operations ----
    
    async def save_incident(self, incident: Incident) -> str:
        """Create or update an incident document."""
        data = incident.model_dump()
        data["created_at"] = incident.created_at
        data["updated_at"] = datetime.utcnow()
        
        if self._available:
            import asyncio
            def _set():
                self._db.collection("incidents").document(incident.incident_id).set(data)
            await asyncio.to_thread(_set)
        else:
            self._memory["incidents"][incident.incident_id] = data
        
        return incident.incident_id
    
    async def get_incident(self, incident_id: str) -> dict | None:
        if self._available:
            import asyncio
            def _get():
                doc = self._db.collection("incidents").document(incident_id).get()
                return doc.to_dict() if doc.exists else None
            return await asyncio.to_thread(_get)
        return self._memory["incidents"].get(incident_id)
    
    async def get_active_incidents(self) -> list[dict]:
        """Fetch all non-resolved incidents — called by the mobile feed."""
        if self._available:
            import asyncio
            def _stream():
                from google.cloud.firestore import FieldFilter
                docs = (
                    self._db.collection("incidents")
                    .where(filter=FieldFilter("status", "in", ["detecting", "active", "monitoring", "notified", "awaiting_approval"]))
                    .stream()
                )
                return [d.to_dict() for d in docs]
            return await asyncio.to_thread(_stream)
        
        active_statuses = {"detecting", "active", "monitoring", "notified", "awaiting_approval"}
        return [
            v for v in self._memory["incidents"].values()
            if v.get("status") in active_statuses
        ]
    
    async def update_incident_status(self, incident_id: str, status: str):
        if self._available:
            import asyncio
            def _update():
                self._db.collection("incidents").document(incident_id).update({
                    "status": status,
                    "updated_at": datetime.utcnow()
                })
            await asyncio.to_thread(_update)
        elif incident_id in self._memory["incidents"]:
            self._memory["incidents"][incident_id]["status"] = status
    
    # ---- Signal operations ----
    
    async def save_signal(self, signal: NormalizedSignal, incident_id: str | None = None):
        data = signal.model_dump()
        data["timestamp"] = signal.timestamp
        
        if self._available and incident_id:
            import asyncio
            def _set_sig_inc():
                (self._db.collection("incidents")
                         .document(incident_id)
                         .collection("signals")
                         .document(signal.signal_id)
                         .set(data))
            await asyncio.to_thread(_set_sig_inc)
        else:
            if self._available:
                import asyncio
                def _set_sig():
                    self._db.collection("signals").document(signal.signal_id).set(data)
                await asyncio.to_thread(_set_sig)
            else:
                self._memory["signals"][signal.signal_id] = data
    
    # ---- Trace operations ----
    
    async def save_trace(self, trace: AgentTrace):
        data = trace.model_dump()
        data["timestamp"] = trace.timestamp
        
        if self._available:
            import asyncio
            def _set_trace():
                (self._db.collection("incidents")
                         .document(trace.incident_id)
                         .collection("traces")
                         .document(trace.trace_id)
                         .set(data))
            await asyncio.to_thread(_set_trace)
        else:
            self._memory["traces"].append(data)
    
    async def get_traces_for_incident(self, incident_id: str) -> list[dict]:
        if self._available:
            import asyncio
            def _stream_traces():
                docs = (
                    self._db.collection("incidents")
                            .document(incident_id)
                            .collection("traces")
                            .order_by("timestamp")
                            .stream()
                )
                return [d.to_dict() for d in docs]
            return await asyncio.to_thread(_stream_traces)
        
        return [
            t for t in self._memory["traces"]
            if t.get("incident_id") == incident_id
        ]
    
    # ---- Resource state ----
    
    async def get_resource_state(self) -> dict:
        """Single document tracking all resource availability."""
        if self._available:
            import asyncio
            def _get_res():
                doc = self._db.collection("resources").document("current_state").get()
                return doc.to_dict() if doc.exists else self._default_resources()
            return await asyncio.to_thread(_get_res)
        return self._default_resources()
    
    async def update_resource_state(self, resources: dict):
        if self._available:
            import asyncio
            def _set_res():
                self._db.collection("resources").document("current_state").set(resources)
            await asyncio.to_thread(_set_res)
    
    def _default_resources(self) -> dict:
        return {
            "ambulances": {"total": 12, "available": 9},
            "rescue_teams": {"total": 4, "available": 3},
            "police_units": {"total": 8, "available": 6},
            "water_tankers": {"total": 3, "available": 2},
            "shelters": {"total": 5, "available": 4},
            "utility_teams": {"total": 3, "available": 2},
        }


# Singleton
firestore_service = FirestoreService()
