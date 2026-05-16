# backend/services/mock_sensor_stream.py
import asyncio
from datetime import datetime
from backend.models.signal import RawSignal, SignalLocation, NormalizedSignal
from backend.utils.signal_normalizer import normalize_signal

class MockSensorStreamService:
    def __init__(self):
        self.sensors = [
            {"id": "sen_w1", "type": "water_level", "location": {"lat": 33.682, "lng": 73.047, "area": "G-10"}},
            {"id": "sen_t1", "type": "temperature", "location": {"lat": 33.72, "lng": 73.05, "area": "F-7"}},
        ]

    async def trigger_sensor_breach(self, sensor_id: str, value: float, threshold: float, crisis_hint: str) -> NormalizedSignal:
        """Simulates a critical IoT sensor breach."""
        sensor = next(s for s in self.sensors if s["id"] == sensor_id)
        
        raw = RawSignal(
            source_type="sensor",
            source_name=f"{sensor['type']}_sensor_{sensor['id']}",
            raw_content=f"Critical alert: {sensor['type']} at {value} (threshold {threshold}). BREACH DETECTED.",
            location=SignalLocation(
                lat=sensor["location"]["lat"],
                lng=sensor["location"]["lng"],
                area_name=sensor["location"]["area"],
                precision="high"
            ),
            crisis_type_hint=crisis_hint,
            timestamp=datetime.utcnow()
        )
        # Sensor data is highly credible and urgent
        return normalize_signal(raw)

mock_sensor_stream = MockSensorStreamService()
