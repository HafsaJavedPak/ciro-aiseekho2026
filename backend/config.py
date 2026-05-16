# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # App identity
    APP_NAME: str = "CIRO - Crisis Intelligence & Response Orchestrator"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # OpenWeatherMap
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    
    # Google AI Studio (Gemini)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Firebase
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Demo city (Islamabad)
    DEMO_CITY_LAT: float = float(os.getenv("DEMO_CITY_LAT", "33.6844"))
    DEMO_CITY_LNG: float = float(os.getenv("DEMO_CITY_LNG", "73.0479"))
    DEMO_CITY_NAME: str = os.getenv("DEMO_CITY_NAME", "Islamabad")
    
    # Signal pipeline
    SIGNAL_CONFIDENCE_THRESHOLD: float = 0.40   # Below this → flag for verification
    SIGNAL_CLUSTER_RADIUS_KM: float = 1.5        # Signals within 1.5km = same incident
    SIGNAL_DEDUP_WINDOW_MIN: int = 30            # Ignore duplicate signals within 30 min
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


# Single instance — import this everywhere
settings = Settings()
