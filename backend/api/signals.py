# backend/api/signals.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.models.signal import RawSignal, NormalizedSignal
from backend.utils.signal_normalizer import normalize_signal
from backend.services.firestore_service import firestore_service
from backend.services.websocket_manager import ws_manager

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.post("/ingest", response_model=NormalizedSignal)
async def ingest_signal(raw: RawSignal, background_tasks: BackgroundTasks):
    """
    Main entry point for all signal sources.
    Normalizes the signal and stores it — then triggers pipeline via background task.
    
    In production, agents would be triggered here.
    For Day 1, we normalize + store + broadcast.
    """
    normalized = normalize_signal(raw)
    
    # Store signal
    background_tasks.add_task(firestore_service.save_signal, normalized)
    
    # Broadcast to WebSocket clients (Flutter app shows new signal in live feed)
    background_tasks.add_task(
        ws_manager.broadcast,
        "new_signal",
        normalized.model_dump(),
        "signal"
    )
    
    return normalized


@router.get("/stream/social")
async def get_mock_social_posts(scenario: str | None = None, limit: int = 20):
    """
    Returns mock social posts — optionally filtered by scenario tag.
    The Flutter app uses this to show the raw signal feed.
    """
    from backend.services.mock_social_stream import mock_social_stream
    
    posts = (
        mock_social_stream.get_posts_for_scenario(scenario)
        if scenario
        else mock_social_stream.get_all_posts()
    )
    return {"posts": posts[:limit], "total": len(posts)}
