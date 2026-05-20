# backend/api/signals.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.models.signal import RawSignal, NormalizedSignal
from backend.utils.signal_normalizer import normalize_signal
from backend.services.firestore_service import firestore_service
from backend.services.websocket_manager import ws_manager
from backend.agents.orchestrator import orchestrator

router = APIRouter(prefix="/signals", tags=["Signals"])


from backend.graph.orchestrator import orchestrator_graph
from backend.models.incident import Incident

async def run_graph_and_save(signal: NormalizedSignal):
    try:
        active_incident_dicts = await firestore_service.get_active_incidents()
        active_incidents = [Incident(**d) for d in active_incident_dicts]
        
        initial_state = {
            "signal": signal,
            "active_incidents": active_incidents,
            "errors": [],
            "agent_traces": []
        }
        
        config = {"configurable": {"thread_id": f"thread_{signal.signal_id}"}}
        final_state = await orchestrator_graph.ainvoke(initial_state, config=config)
        
        incident_id = final_state.get("incident_id")
        if not incident_id:
            return
            
        context = final_state.get("context")
        classification = final_state.get("classification")
        status = final_state.get("status", "detecting")
        
        existing = next((i for i in active_incidents if i.incident_id == incident_id), None)
        
        if existing:
            incident = existing
            if signal.signal_id not in incident.signal_ids:
                incident.signal_ids.append(signal.signal_id)
                incident.signal_count += 1
            if classification:
                incident.classification = classification
            incident.status = status
        else:
            incident = Incident(
                incident_id=incident_id,
                status=status,
                location={"lat": context.center_location.lat, "lng": context.center_location.lng, "area_name": context.center_location.area_name} if context else {"lat": signal.location.lat, "lng": signal.location.lng, "area_name": signal.location.area_name},
                classification=classification,
                signal_ids=[signal.signal_id],
                signal_count=1,
                pipeline_stage="notified" if final_state.get("messages") else "classified"
            )
            
        await firestore_service.save_incident(incident)
        
        traces = final_state.get("agent_traces", [])
        if traces:
            for trace in traces:
                from backend.models.trace import AgentTrace
                agent_trace = AgentTrace(
                    incident_id=incident_id,
                    agent=trace.get("agent", "unknown"),
                    decision=trace.get("decision", "unknown"),
                    input_summary="Processed by LangGraph Node",
                    reasoning=trace.get("status", ""),
                    output={}
                )
                await firestore_service.save_trace(agent_trace)
                
        await ws_manager.broadcast("incident_update", incident.model_dump(), "incident")
    except Exception as e:
        import traceback
        with open("graph_error.log", "w") as f:
            f.write(traceback.format_exc())



@router.post("/ingest", response_model=NormalizedSignal)
async def ingest_signal(raw: RawSignal, background_tasks: BackgroundTasks):
    """
    Main entry point for all signal sources.
    Normalizes the signal and stores it — then triggers pipeline via background task.
    """
    normalized = normalize_signal(raw)
    
    # Store signal
    background_tasks.add_task(firestore_service.save_signal, normalized)
    
    # Broadcast to WebSocket clients
    background_tasks.add_task(
        ws_manager.broadcast,
        "new_signal",
        normalized.model_dump(),
        "signal"
    )
    
    import asyncio
    # Trigger the Antigravity LangGraph Pipeline completely decoupled from the request cycle
    asyncio.create_task(run_graph_and_save(normalized))
    
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
