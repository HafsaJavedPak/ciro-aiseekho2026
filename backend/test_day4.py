import asyncio
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.signal import NormalizedSignal, SignalLocation, RawSignal
from backend.agents.orchestrator import orchestrator
from backend.services.firestore_service import firestore_service
from backend.services.mock_sensor_stream import mock_sensor_stream
from backend.utils.signal_normalizer import normalize_signal

async def run_test():
    print("=== Starting Day 4 Pipeline Test: Recovery & False Alarm ===")
    
    # 1. Clear in-memory state for clean test run
    firestore_service._memory = {"incidents": {}, "signals": {}, "traces": []}
    
    # Crisis: Sensor breach indicating high severity flooding
    signal1 = await mock_sensor_stream.trigger_sensor_breach(
        sensor_id="sen_w1", value=2.1, threshold=1.2, crisis_hint="urban_flooding"
    )
    
    print("\n[Step 1] Processing initial crisis (Flooding)...")
    await orchestrator.process_signal(signal1)
    
    incidents = await firestore_service.get_active_incidents()
    incident_id = incidents[0]['incident_id']
    print(f"Incident {incident_id} created with status: {incidents[0]['status']}")
    
    # 2. Inject false alarm field report
    raw = RawSignal(
        source_type="field_report",
        source_name="rescue_unit_alpha",
        raw_content="False alarm verified. No crisis detected on site. Cancelling alert.",
        location=SignalLocation(
            lat=signal1.location.lat,
            lng=signal1.location.lng,
            area_name=signal1.location.area_name,
            precision="high"
        ),
        crisis_type_hint="unknown",
        timestamp=datetime.utcnow()
    )
    
    signal2 = normalize_signal(raw)
    signal2.credibility_score = 0.99  # Field reports are highly credible
    
    print("\n[Step 2] Injecting False Alarm Field Report...")
    await orchestrator.process_signal(signal2)
    
    # Verify results
    print("\n--- TEST RESULTS ---")
    
    # We use get_incident directly since it might be in Firestore or memory
    inc = await firestore_service.get_incident(incident_id)
    
    if inc is None:
        print(f"Could not find {incident_id}.")
        return
        
    print(f"\nIncident: {inc['incident_id']} | Type: {inc['classification']['crisis_type']}")
    print(f"Status: {inc['status']} | Stage: {inc['pipeline_stage']}")
    
    traces = await firestore_service.get_traces_for_incident(inc['incident_id'])
    print(f"Traces ({len(traces)} generated):")
    for t in traces:
        if t['agent'] == 'recovery_agent':
            print(f"  [{t['agent']}] Decision: {t['decision']}")
            print(f"    Action: {t['output'].get('action_type')}")
            print(f"    Message: {t['output'].get('retraction_message')}")

if __name__ == "__main__":
    asyncio.run(run_test())
