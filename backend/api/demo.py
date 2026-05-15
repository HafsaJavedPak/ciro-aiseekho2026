# backend/api/demo.py
import asyncio
from fastapi import APIRouter, BackgroundTasks
from backend.services.mock_social_stream import mock_social_stream
from backend.services.weather_service import weather_service
from backend.services.websocket_manager import ws_manager
from backend.services.firestore_service import firestore_service
from backend.config import settings

router = APIRouter(prefix="/demo", tags=["Demo Control"])


@router.post("/trigger/{scenario_name}")
async def trigger_demo_scenario(scenario_name: str, background_tasks: BackgroundTasks):
    """
    Single endpoint to kick off a scripted demo scenario.
    
    Call this during the hackathon presentation to start the
    pre-scripted signal sequence — crisis emerges, escalates, resolves.
    
    Available scenarios: flood_g10, flood_g10_contradiction, heat_f7, dual_crisis
    """
    valid_scenarios = ["flood_g10", "flood_g10_contradiction", "heat_f7", "dual_crisis"]
    
    if scenario_name not in valid_scenarios:
        return {
            "error": f"Unknown scenario '{scenario_name}'",
            "valid": valid_scenarios
        }
    
    async def run_scenario():
        from backend.utils.signal_normalizer import normalize_signal
        
        # Broadcast scenario start
        await ws_manager.broadcast("demo_started", {
            "scenario": scenario_name,
            "message": f"Demo scenario '{scenario_name}' starting"
        }, "system")
        
        # Stream social posts for this scenario
        async def on_signal(normalized_signal):
            await firestore_service.save_signal(normalized_signal)
            await ws_manager.broadcast("new_signal", normalized_signal.model_dump(), "signal")
        
        await mock_social_stream.stream_scenario(scenario_name, on_signal)
        
        # After social posts, fetch weather for extra signal richness
        weather_signal = await weather_service.fetch_current_weather(
            settings.DEMO_CITY_LAT,
            settings.DEMO_CITY_LNG,
            settings.DEMO_CITY_NAME
        )
        if weather_signal:
            await firestore_service.save_signal(weather_signal)
            await ws_manager.broadcast("new_signal", weather_signal.model_dump(), "signal")
        
        await ws_manager.broadcast("demo_completed", {"scenario": scenario_name}, "system")
    
    background_tasks.add_task(run_scenario)
    
    return {
        "status": "started",
        "scenario": scenario_name,
        "message": "Scenario running in background. Watch WebSocket for updates."
    }


@router.get("/scenarios")
async def list_scenarios():
    """What demo scenarios are available."""
    return {
        "scenarios": [
            {"name": "flood_g10", "description": "Urban flooding emerges in G-10"},
            {"name": "flood_g10_contradiction", "description": "Flooding → false alarm correction"},
            {"name": "heat_f7", "description": "Heat emergency in F-7"},
            {"name": "dual_crisis", "description": "Two simultaneous crises competing for resources"},
        ]
    }


@router.post("/reset")
async def reset_demo_state():
    """Clear all active incidents for a clean demo restart."""
    await ws_manager.broadcast("demo_reset", {"message": "State cleared"}, "system")
    return {"status": "reset", "message": "Demo state cleared"}
