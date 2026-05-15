# backend/utils/signal_normalizer.py
import re
from datetime import datetime
from backend.models.signal import RawSignal, NormalizedSignal, VelocityContext
from backend.config import settings


# --- Keyword dictionaries ---

CRISIS_KEYWORDS = {
    "urban_flooding": [
        "flood", "flooded", "flooding", "waterlogged", "inundated",
        "water level", "storm drain", "heavy rain", "submerged", "stalled cars"
    ],
    "fire": [
        "fire", "burning", "flames", "smoke", "blaze", "inferno",
        "firefighter", "evacuate", "ablaze"
    ],
    "heatwave": [
        "heat", "heatwave", "scorching", "temperature", "humid",
        "heat stroke", "dehydration", "hospital heat"
    ],
    "road_accident": [
        "accident", "crash", "collision", "pile-up", "vehicle",
        "blocked road", "ambulance called", "injured"
    ],
    "power_outage": [
        "power out", "blackout", "no electricity", "outage",
        "load shedding", "generator", "transformer blast"
    ],
    "infrastructure_failure": [
        "burst pipe", "water main", "sinkhole", "bridge", "collapse",
        "structural", "gas leak", "building crack"
    ],
}

URGENCY_KEYWORDS = {
    "high": [
        "emergency", "help", "trapped", "stuck", "danger", "urgent",
        "mayday", "critical", "sos", "dying", "injured", "hospital now"
    ],
    "medium": [
        "warning", "alert", "caution", "bad", "serious", "severe",
        "problem", "issue", "getting worse"
    ],
    "low": ["update", "fyi", "noticed", "seems like", "maybe", "possibly"],
}

SOURCE_BASE_CREDIBILITY = {
    "sensor": 0.95,
    "field_report": 0.90,
    "weather": 0.88,
    "citizen_report": 0.65,
    "social": 0.50,
}


def extract_keywords(text: str) -> list[str]:
    """Find all known crisis keywords present in the text."""
    text_lower = text.lower()
    found = []
    for crisis_type, keywords in CRISIS_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower and kw not in found:
                found.append(kw)
    return found


def detect_crisis_type_hint(text: str) -> str | None:
    """Vote on the most likely crisis type based on keyword density."""
    text_lower = text.lower()
    scores = {}
    for crisis_type, keywords in CRISIS_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[crisis_type] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


def compute_urgency_score(text: str) -> float:
    """Score 0–1 based on urgency language in the text."""
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in URGENCY_KEYWORDS["high"]):
        return 0.85
    if any(kw in text_lower for kw in URGENCY_KEYWORDS["medium"]):
        return 0.55
    if any(kw in text_lower for kw in URGENCY_KEYWORDS["low"]):
        return 0.25
    return 0.40  # Neutral — no strong urgency language


def compute_credibility_score(
    source_type: str,
    urgency_score: float,
    velocity_context: VelocityContext,
    has_contradiction: bool = False,
) -> float:
    """
    Weighted credibility formula from the architecture spec:
    
    credibility = source_weight * 0.35
               + geo_precision  * 0.20
               + urgency        * 0.20
               + (1 - contradiction) * 0.15
               + velocity       * 0.10
    
    Note: geo_precision is handled at normalization time from the source signal.
    """
    source_weight = SOURCE_BASE_CREDIBILITY.get(source_type, 0.50)
    
    velocity_score = min(velocity_context.mentions_last_5min / 20.0, 1.0)
    
    contradiction_penalty = 0.3 if has_contradiction else 0.0
    
    # Geo precision defaults to 0.7 (medium) — sensors are high (1.0), social is low (0.4)
    geo_precision_scores = {"sensor": 1.0, "weather": 0.9, "field_report": 0.8,
                            "citizen_report": 0.6, "social": 0.4}
    geo_score = geo_precision_scores.get(source_type, 0.6)
    
    score = (
        source_weight * 0.35 +
        geo_score * 0.20 +
        urgency_score * 0.20 +
        (1.0 - contradiction_penalty) * 0.15 +
        velocity_score * 0.10
    )
    
    return round(min(max(score, 0.0), 1.0), 3)


def normalize_signal(
    raw: RawSignal,
    velocity_context: VelocityContext | None = None,
    has_contradiction: bool = False,
) -> NormalizedSignal:
    """
    Main normalization function.
    Takes a RawSignal (any source) and returns a NormalizedSignal.
    This is the gate that all data must pass through before agents see it.
    """
    if velocity_context is None:
        velocity_context = VelocityContext()
    
    keywords = extract_keywords(raw.raw_content)
    crisis_hint = raw.crisis_type_hint or detect_crisis_type_hint(raw.raw_content)
    urgency = compute_urgency_score(raw.raw_content)
    credibility = compute_credibility_score(
        raw.source_type, urgency, velocity_context, has_contradiction
    )
    
    return NormalizedSignal(
        source_type=raw.source_type,
        source_name=raw.source_name,
        raw_content=raw.raw_content,
        extracted_keywords=keywords,
        crisis_type_hint=crisis_hint,
        location=raw.location,
        timestamp=raw.timestamp,
        urgency_score=urgency,
        credibility_score=credibility,
        velocity_context=velocity_context,
        processed=False,
    )
