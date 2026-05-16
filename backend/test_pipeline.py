import asyncio
import os
import sys
from datetime import datetime

# Add the project root to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.signal import NormalizedSignal, SignalLocation, VelocityContext
from backend.agents.orchestrator import orchestrator
from backend.services.firestore_service import firestore_service

async def run_test():
    print("=== Starting CIRO Pipeline Test ===")
    
    # 1. Ensure firestore fallback is working by fetching incidents
    incidents = await firestore_service.get_active_incidents()
    print(f"Active incidents before test: {len(incidents)}")
    
    # 2. Create a mock signal
    signal = NormalizedSignal(
        source_type="social",
        source_name="MockFeed",
        raw_content="Terrible flooding here in G-10, cars are underwater!",
        extracted_keywords=["flooding", "water", "cars"],
        crisis_type_hint="urban_flooding",
        location=SignalLocation(
            lat=33.6844,
            lng=73.0479,
            area_name="G-10, Islamabad",
            precision="high"
        ),
        urgency_score=0.9,
        credibility_score=0.8,
        velocity_context=VelocityContext(mentions_last_5min=15, trend="rising")
    )
    
    # 3. Process the signal
    print(f"Processing signal: {signal.signal_id}")
    await orchestrator.process_signal(signal)
    
    # 4. Verify results
    incidents_after = await firestore_service.get_active_incidents()
    print(f"Active incidents after test: {len(incidents_after)}")
    
    for inc in incidents_after:
        print(f"Incident: {inc['incident_id']} - Status: {inc['status']} - Stage: {inc['pipeline_stage']}")
        print(f"Classification: {inc.get('classification')}")
        
    traces = await firestore_service.get_traces_for_incident(incidents_after[0]['incident_id'])
    print(f"Traces generated: {len(traces)}")
    for t in traces:
        print(f"  [{t['agent']}] Decision: {t['decision']} -> {t['reasoning']}")

if __name__ == "__main__":
    asyncio.run(run_test())
