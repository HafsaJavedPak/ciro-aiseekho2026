# backend/services/weather_service.py
import httpx
from datetime import datetime
from backend.config import settings
from backend.models.signal import RawSignal, NormalizedSignal, SignalLocation
from backend.utils.signal_normalizer import normalize_signal


# Map OWM weather codes to our crisis types
OWM_CODE_TO_CRISIS = {
    range(200, 300): "urban_flooding",   # Thunderstorm
    range(300, 400): "urban_flooding",   # Drizzle → can still cause flooding
    range(500, 600): "urban_flooding",   # Rain
    range(600, 700): "unknown",          # Snow (unlikely in Islamabad)
    range(700, 800): "unknown",          # Atmosphere (fog, dust)
    range(900, 910): "heatwave",         # Extreme conditions
}

def _map_weather_code(code: int) -> str | None:
    for code_range, crisis_type in OWM_CODE_TO_CRISIS.items():
        if code in code_range:
            return crisis_type
    return None

def _rain_intensity_to_urgency(rain_mm_per_hour: float) -> float:
    """
    Convert rainfall intensity to urgency score.
    Light: <2.5mm/hr | Moderate: 2.5–7.6 | Heavy: 7.6–50 | Violent: >50
    """
    if rain_mm_per_hour > 50:
        return 0.95
    elif rain_mm_per_hour > 20:
        return 0.80
    elif rain_mm_per_hour > 7.6:
        return 0.65
    elif rain_mm_per_hour > 2.5:
        return 0.45
    return 0.20


class WeatherService:
    def __init__(self):
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.api_key = settings.OPENWEATHER_API_KEY
        self._cache: dict = {}  # Simple in-memory cache: params_key → (result, timestamp)
        self._cache_ttl_seconds = 300  # 5 minutes

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        _, cached_at = self._cache[key]
        age = (datetime.utcnow() - cached_at).total_seconds()
        return age < self._cache_ttl_seconds

    async def fetch_current_weather(
        self,
        lat: float,
        lng: float,
        area_name: str = "Unknown"
    ) -> NormalizedSignal | None:
        """
        Fetch current weather for a location and return as a NormalizedSignal.
        Returns None if the weather is not crisis-relevant (clear sky, light cloud).
        """
        cache_key = f"{lat:.3f}_{lng:.3f}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key][0]
        
        if not self.api_key:
            # Development fallback — return a mock weather signal
            return self._mock_weather_signal(lat, lng, area_name)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": lat,
                        "lon": lng,
                        "appid": self.api_key,
                        "units": "metric",
                    }
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            print(f"[WeatherService] HTTP error: {e}")
            return None
        except Exception as e:
            print(f"[WeatherService] Unexpected error: {e}")
            return None

        signal = self._parse_owm_response(data, area_name)
        
        # Cache even if None (to avoid hammering the API on failures)
        self._cache[cache_key] = (signal, datetime.utcnow())
        return signal

    def _parse_owm_response(self, data: dict, area_name: str) -> NormalizedSignal | None:
        """Convert OWM API response into a NormalizedSignal."""
        weather_code = data["weather"][0]["id"]
        weather_desc = data["weather"][0]["description"]
        temp_c = data["main"]["temp"]
        
        rain_1h = data.get("rain", {}).get("1h", 0.0)
        wind_speed = data["wind"]["speed"]
        
        # Only generate a signal if conditions are crisis-relevant
        is_crisis_relevant = (
            rain_1h > 2.5 or           # Moderate+ rain
            temp_c > 42 or             # Dangerous heat
            wind_speed > 15 or         # Strong wind
            weather_code < 700         # Any storm/rain/snow code
        )
        
        if not is_crisis_relevant:
            return None
        
        crisis_type = _map_weather_code(weather_code)
        if temp_c > 42:
            crisis_type = "heatwave"
        
        content = (
            f"Weather alert: {weather_desc}. "
            f"Temp: {temp_c}°C, Rain (1h): {rain_1h}mm, Wind: {wind_speed}m/s. "
            f"Location: {area_name}"
        )
        
        raw = RawSignal(
            source_type="weather",
            source_name="OpenWeatherMap",
            raw_content=content,
            location=SignalLocation(
                lat=data["coord"]["lat"],
                lng=data["coord"]["lon"],
                area_name=area_name,
                precision="high",
            ),
            crisis_type_hint=crisis_type,
        )
        
        return normalize_signal(raw)

    def _mock_weather_signal(self, lat: float, lng: float, area_name: str) -> NormalizedSignal:
        """Fallback for development when no API key is set."""
        raw = RawSignal(
            source_type="weather",
            source_name="OpenWeatherMap_MOCK",
            raw_content=f"Heavy rain alert: 35mm/hr, flooding risk HIGH. Location: {area_name}",
            location=SignalLocation(lat=lat, lng=lng, area_name=area_name, precision="high"),
            crisis_type_hint="urban_flooding",
        )
        return normalize_signal(raw)


# Singleton
weather_service = WeatherService()
