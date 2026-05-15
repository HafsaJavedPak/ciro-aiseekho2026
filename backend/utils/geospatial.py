# backend/utils/geospatial.py
import math
from typing import Tuple


def haversine_km(
    lat1: float, lng1: float,
    lat2: float, lng2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    Returns distance in kilometers.
    
    This is used for:
    - Signal clustering (are these signals about the same incident?)
    - Travel time estimation (how far is the nearest ambulance?)
    - Affected radius calculations
    """
    R = 6371.0  # Earth radius in km
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_population(lat: float, lng: float, radius_km: float) -> int:
    """
    Rough population estimate for an affected area.
    
    In production, this would use a population density raster.
    For the hackathon, we use a realistic density lookup by city zone.
    Islamabad average density: ~4,500 people/km²
    """
    ISLAMABAD_DENSITY_PER_KM2 = 4500
    area_km2 = math.pi * radius_km ** 2
    return int(area_km2 * ISLAMABAD_DENSITY_PER_KM2)


def is_within_cluster(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
    threshold_km: float = 1.5
) -> bool:
    """Returns True if two points are close enough to be the same incident."""
    return haversine_km(lat1, lng1, lat2, lng2) <= threshold_km


def estimate_travel_time_minutes(
    resource_lat: float, resource_lng: float,
    incident_lat: float, incident_lng: float,
    crisis_type: str = "unknown"
) -> float:
    """
    Estimate how long it takes a resource (ambulance, rescue team) to reach an incident.
    Uses a simple distance/speed model with a congestion adjustment.
    """
    distance_km = haversine_km(resource_lat, resource_lng, incident_lat, incident_lng)
    
    # Urban speed: 40 km/h base
    speed_kmh = 40.0
    
    # Congestion factor — flooding and accidents slow down all vehicles
    congestion_types = {"urban_flooding", "road_accident"}
    congestion_factor = 1.3 if crisis_type in congestion_types else 1.0
    
    travel_time_min = (distance_km / speed_kmh) * 60 * congestion_factor
    return round(travel_time_min, 1)
