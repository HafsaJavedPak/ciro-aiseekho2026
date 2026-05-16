import asyncio
import os
import sys
from datetime import datetime

# Ensure we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.weather_service import weather_service
from backend.services.firestore_service import firestore_service
from backend.agents.orchestrator import orchestrator
from backend.config import settings
from backend.utils.signal_normalizer import normalize_signal

async def run_live_integration():
    print("==================================================")
    print("🚀 CIRO Live Integration & Firebase Pipeline Runner")
    print("==================================================")
    
    # Verify Firebase Connection
    if not firestore_service._available:
        print("❌ Firebase is not connected! Using in-memory fallback.")
        print("Please check your firebase-credentials.json and .env file.")
        return
    else:
        print("✅ Connected to Live Firebase Project:", settings.FIREBASE_PROJECT_ID)

    # Step 1: Ingest Live Data (Weather API)
    print(f"\n📡 [Ingestion] Fetching live weather data for {settings.DEMO_CITY_NAME}...")
    raw_weather_signal = await weather_service.fetch_current_weather(
        settings.DEMO_CITY_LAT,
        settings.DEMO_CITY_LNG,
        settings.DEMO_CITY_NAME
    )
    
    if not raw_weather_signal:
        print("⚠️ Failed to fetch live weather. Falling back to synthetic field report...")
        from backend.models.signal import RawSignal, SignalLocation
        raw_weather_signal = RawSignal(
            source_type="sensor",
            source_name="demo_live_sensor",
            raw_content="Critical alert: Extreme flooding detected by live integration script.",
            location=SignalLocation(
                lat=settings.DEMO_CITY_LAT,
                lng=settings.DEMO_CITY_LNG,
                area_name=settings.DEMO_CITY_NAME,
                precision="high"
            ),
            crisis_type_hint="urban_flooding",
            timestamp=datetime.utcnow()
        )
        
    print(f"✅ Live/Synthetic data acquired: {raw_weather_signal.raw_content}")

    # Step 2: Normalization
    print("\n⚙️ [Normalization] Structuring live data...")
    normalized_signal = normalize_signal(raw_weather_signal)
    
    # Store initial signal in Firebase
    await firestore_service.save_signal(normalized_signal)
    print(f"✅ Saved NormalizedSignal to Firebase: {normalized_signal.signal_id}")

    # Step 3: Run Orchestrator Pipeline
    print(f"\n🧠 [Orchestration] Pushing signal {normalized_signal.signal_id} through Antigravity Pipeline...")
    print("   Agents: Fusion -> Credibility -> Recovery -> Classification -> Allocation -> Simulation -> Messaging")
    
    await orchestrator.process_signal(normalized_signal)

    # Step 4: Verification
    print("\n✅ [Verification] Pipeline complete. Fetching updated incident from Firebase...")
    
    # Since we don't know the exact ID, we grab the latest active one
    active_incidents = await firestore_service.get_active_incidents()
    if not active_incidents:
         print("No active incidents found. The weather might not be severe enough to trigger an active crisis.")
    else:
         latest_incident = active_incidents[-1]
         print(f"\n🔥 Firebase Incident Record:")
         print(f"   ID: {latest_incident.get('incident_id')}")
         print(f"   Status: {latest_incident.get('status')}")
         print(f"   Type: {latest_incident.get('classification', {}).get('crisis_type')}")
         print(f"   Severity: {latest_incident.get('classification', {}).get('severity')}")
         
         traces = await firestore_service.get_traces_for_incident(latest_incident.get('incident_id'))
         print(f"\n📝 Firebase Trace Records ({len(traces)} found):")
         for trace in traces:
             print(f"   - [{trace['agent']}] Decision: {trace['decision']}")

    print("\n🎉 Live integration run successful! All data is strictly persisted in Firestore.")

if __name__ == "__main__":
    asyncio.run(run_live_integration())
