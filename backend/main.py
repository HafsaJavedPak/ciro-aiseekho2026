# backend/main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.services.websocket_manager import ws_manager
from backend.services.firestore_service import firestore_service
from backend.api import signals, incidents, demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Use for: starting background tasks, initializing connections.
    """
    print(f"[CIRO] Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"[CIRO] Environment: {settings.ENVIRONMENT}")
    
    # Start WebSocket heartbeat as background task
    heartbeat_task = asyncio.create_task(ws_manager.heartbeat())
    
    yield  # App runs here
    
    # Cleanup on shutdown
    heartbeat_task.cancel()
    print("[CIRO] Shutting down gracefully")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Multi-agent crisis intelligence and resource orchestration system",
    lifespan=lifespan,
)

# CORS — allows Flutter web and mobile to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(signals.router)
app.include_router(incidents.router)
app.include_router(demo.router)


@app.get("/")
async def health_check():
    """Simple health check — load balancers and Cloud Run use this."""
    return {
        "status": "operational",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket connection endpoint.
    Flutter app connects here for all real-time updates.
    
    Message format:
    {
      "event": "new_signal" | "incident_update" | "trace" | "alert" | "heartbeat",
      "type": "signal" | "incident" | "trace" | "alert" | "resource" | "system",
      "data": { ... },
      "timestamp": "ISO8601"
    }
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Listen for messages from the client (e.g., subscribe to specific incident)
            data = await websocket.receive_text()
            # For Day 1: just echo back. Day 2+ will handle subscriptions.
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/{incident_id}")
async def websocket_incident_endpoint(websocket: WebSocket, incident_id: str):
    """
    Incident-specific WebSocket room.
    Flutter Trace Viewer connects here to get real-time trace updates for one incident.
    """
    await ws_manager.connect(websocket, room=incident_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
