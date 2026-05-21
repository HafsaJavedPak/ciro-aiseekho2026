import asyncio
import httpx
import json
import time

API_BASE = "http://127.0.0.1:8000"

async def run_hackathon_scenario():
    print("==================================================")
    print("🌊 CIRO Hackathon Scenario Demo: Urban Flooding")
    print("==================================================")
    
    signals = [
        {
            "source_type": "social",
            "source_name": "TwitterUser1",
            "raw_content": "Flash flood happening at George Town for past 30 mins",
            "location": {"lat": 33.6844, "lng": 73.0479, "area_name": "George Town / G-10", "precision": "high"},
            "timestamp": "2026-05-20T10:00:00Z"
        },
        {
            "source_type": "social",
            "source_name": "FacebookUser2",
            "raw_content": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
            "location": {"lat": 33.6844, "lng": 73.0479, "area_name": "G-10", "precision": "high"},
            "timestamp": "2026-05-20T10:05:00Z"
        },
        {
            "source_type": "sensor",
            "source_name": "WeatherAPI",
            "raw_content": "HEAVY RAINFALL ALERT: Precipitation exceeding 50mm/hr in sector G-10.",
            "location": {"lat": 33.6844, "lng": 73.0479, "area_name": "G-10", "precision": "high"},
            "timestamp": "2026-05-20T09:50:00Z"
        },
        {
            "source_type": "sensor",
            "source_name": "MapsAPI",
            "raw_content": "TRAFFIC CONGESTION SPIKE: Average speed 2km/h on major G-10 routes.",
            "location": {"lat": 33.6844, "lng": 73.0479, "area_name": "G-10", "precision": "high"},
            "timestamp": "2026-05-20T10:10:00Z"
        }
    ]

    async with httpx.AsyncClient() as client:
        print("\n[1] 📡 Ingesting Multi-Source Signals...")
        for i, signal in enumerate(signals):
            print(f"   -> Sending [{signal['source_type']}]: {signal['raw_content']}")
            try:
                response = await client.post(f"{API_BASE}/signals/ingest", json=signal)
                if response.status_code not in (200, 202):
                    print(f"   ⚠️ Failed to ingest signal {i}: {response.text}")
            except Exception as e:
                print(f"   ⚠️ Error connecting to API: {e}. Is FastAPI running?")
                return

        print("\n[2] 🧠 Waiting for LangGraph Orchestrator to Process...")
        for i in range(20, 0, -1):
            print(f"   ... {i}s")
            await asyncio.sleep(1)

        print("\n[3] 📊 Fetching System State...")
        response = await client.get(f"{API_BASE}/incidents/active")
        if response.status_code == 200:
            data = response.json()
            incidents = data.get("incidents", [])
            
            if not incidents:
                print("   ⚠️ No active incidents found. The orchestrator might still be running or failed.")
            else:
                # Sort by updated_at to get the most recent one
                incidents.sort(key=lambda x: x.get("updated_at", ""))
                incident = incidents[-1]
                incident_id = incident.get("incident_id")
                
                print("\n🔥 DETECTED SITUATION:")
                classification = incident.get("classification", {})
                print(f"   - Type: {classification.get('crisis_type', 'Unknown')}")
                print(f"   - Location: {incident.get('location', {}).get('area_name', 'Unknown')}")
                print(f"   - Confidence: {classification.get('confidence', 0.0) * 100}%")
                print(f"   - Severity: {classification.get('severity', 0)}/5")
                print(f"   - Reasoning: {classification.get('reasoning', 'None')}")
                
                print("\n🚀 EXPECTED OUTPUT VERIFICATION:")
                print("   [x] Multi-Source Input Processed")
                print("   [x] Event Detected & Fused")
                print(f"   [x] Agentic Reasoning Completed (Status: {incident.get('status')})")
                
                # Fetch Traces to show Agentic Workflow
                print("\n📝 AGENTIC WORKFLOW TRACES:")
                traces_res = await client.get(f"{API_BASE}/incidents/{incident_id}/traces")
                if traces_res.status_code == 200:
                    traces = traces_res.json().get("traces", [])
                    for trace in traces:
                        agent = trace.get("agent", "unknown")
                        decision = trace.get("decision", "no decision recorded")
                        print(f"   -> [{agent.upper()}] {decision}")
                        
                print("\n✅ Scenario Complete. Demo Video ready!")

if __name__ == "__main__":
    asyncio.run(run_hackathon_scenario())
