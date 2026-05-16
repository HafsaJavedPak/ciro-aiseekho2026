import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.signal import NormalizedSignal, SignalLocation, VelocityContext
from backend.agents.orchestrator import orchestrator
from backend.services.firestore_service import firestore_service
from backend.services.mock_sensor_stream import mock_sensor_stream

async def run_test():
    print("=== Starting Day 3 Pipeline Test: Multi-Crisis Allocation ===")
    
    # 1. Clear in-memory state for clean test run
    firestore_service._memory = {"incidents": {}, "signals": {}, "traces": []}
    
    # Crisis 1: Sensor breach indicating high severity flooding in G-10
    signal1 = await mock_sensor_stream.trigger_sensor_breach(
        sensor_id="sen_w1", value=2.1, threshold=1.2, crisis_hint="urban_flooding"
    )
    
    # Crisis 2: Sensor breach indicating heatwave in F-7
    signal2 = await mock_sensor_stream.trigger_sensor_breach(
        sensor_id="sen_t1", value=48.5, threshold=42.0, crisis_hint="heatwave"
    )
    
    # Process both signals (this will trigger the full pipeline including Day 3 agents)
    print("Processing Crisis 1 (Flooding)...")
    await orchestrator.process_signal(signal1)
    
    print("\nProcessing Crisis 2 (Heatwave)...")
    await orchestrator.process_signal(signal2)
    
    # Verify results
    print("\n--- TEST RESULTS ---")
    incidents = await firestore_service.get_active_incidents()
    print(f"Active Incidents: {len(incidents)}")
    
    for inc in incidents:
        print(f"\nIncident: {inc['incident_id']} | Type: {inc['classification']['crisis_type']}")
        print(f"Status: {inc['status']} | Stage: {inc['pipeline_stage']}")
        
        traces = await firestore_service.get_traces_for_incident(inc['incident_id'])
        print(f"Traces ({len(traces)} generated):")
        for t in traces:
            if t['agent'] in ['resource_allocation_agent', 'simulation_agent', 'stakeholder_messaging_agent']:
                print(f"  [{t['agent']}] Decision: {t['decision']}")
                if t['agent'] == 'resource_allocation_agent':
                    print(f"    Assigned: {t['output'].get('assigned', {})}")
                    print(f"    Conflicts: {t['output'].get('conflicts', [])}")
                if t['agent'] == 'stakeholder_messaging_agent':
                    print(f"    Messages generated: {list(t['output'].keys())}")

if __name__ == "__main__":
    asyncio.run(run_test())
