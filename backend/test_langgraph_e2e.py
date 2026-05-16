import asyncio
from backend.graph.orchestrator import orchestrator_graph
from backend.models.signal import NormalizedSignal, SignalLocation

async def run_e2e():
    print("--- Starting LangGraph E2E Test ---")
    
    # 1. Create a dummy signal
    signal = NormalizedSignal(
        signal_id="sig_e2e_001",
        source_type="citizen_report",
        source_name="AppUser",
        location=SignalLocation(lat=31.5204, lng=74.3587, area_name="Downtown Metro Station"),
        timestamp="2026-05-17T02:00:00Z",
        raw_content="There is a massive flood near the metro station, water level is rising quickly!",
        extracted_keywords=["flood", "metro", "water"],
        crisis_type_hint="urban_flooding",
        credibility_score=0.9
    )
    
    # 2. Initial State
    initial_state = {
        "signal": signal,
        "active_incidents": [],
        "errors": [],
        "agent_traces": []
    }
    
    # 3. Execute Graph
    config = {"configurable": {"thread_id": "test_thread_1"}}
    final_state = await orchestrator_graph.ainvoke(initial_state, config=config)
    
    # 4. Print results
    print("\n--- Execution Completed ---")
    print(f"Incident ID: {final_state.get('incident_id')}")
    print(f"Status: {final_state.get('status')}")
    print(f"Classification: {final_state.get('classification')}")
    print(f"Allocation Plan: {final_state.get('allocation_plan')}")
    print(f"Simulations: {len(final_state.get('simulations', []))} run")
    print("Agent Traces:")
    for trace in final_state.get("agent_traces", []):
        print(f"  - {trace['agent']}: {trace.get('decision')} (Status: {trace.get('status')})")

if __name__ == "__main__":
    asyncio.run(run_e2e())
