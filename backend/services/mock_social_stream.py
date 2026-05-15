# backend/services/mock_social_stream.py
import json
import asyncio
from pathlib import Path
from datetime import datetime
from backend.models.signal import RawSignal, SignalLocation, NormalizedSignal
from backend.utils.signal_normalizer import normalize_signal


def _load_posts() -> list[dict]:
    data_path = Path(__file__).parent.parent / "data" / "mock_social_posts.json"
    with open(data_path) as f:
        return json.load(f)


def _post_to_raw_signal(post: dict) -> RawSignal:
    """Convert a mock social post dict into a RawSignal."""
    return RawSignal(
        source_type="social",
        source_name="MockSocialFeed_v1",
        raw_content=post["content"],
        location=SignalLocation(
            lat=post["location"]["lat"],
            lng=post["location"]["lng"],
            area_name=post["location"]["area_name"],
            precision="medium",
        ),
        timestamp=datetime.utcnow(),
        crisis_type_hint=post.get("crisis_type"),
    )


class MockSocialStreamService:
    """
    Simulates a real-time social media feed.
    
    Two modes:
    - scenario: Stream only posts matching a given scenario_tag, with delays
    - continuous: Stream all posts in sequence, cycling indefinitely
    """

    def __init__(self):
        self._posts = _load_posts()

    def get_posts_for_scenario(self, scenario_tag: str) -> list[dict]:
        return [p for p in self._posts if p.get("scenario_tag") == scenario_tag]

    def get_all_posts(self) -> list[dict]:
        return self._posts

    async def stream_scenario(
        self,
        scenario_tag: str,
        callback  # async function(NormalizedSignal) → called for each post
    ):
        """
        Stream posts for a specific demo scenario, respecting delay_seconds.
        This gives you the cinematic demo effect — signals arrive over time.
        """
        posts = self.get_posts_for_scenario(scenario_tag)
        posts_sorted = sorted(posts, key=lambda p: p.get("delay_seconds", 0))
        
        last_delay = 0
        for post in posts_sorted:
            delay = post.get("delay_seconds", 0)
            wait = delay - last_delay
            if wait > 0:
                await asyncio.sleep(wait)
            last_delay = delay
            
            raw = _post_to_raw_signal(post)
            normalized = normalize_signal(raw)
            await callback(normalized)

    async def generate_continuous_stream(self, interval_seconds: float = 15.0):
        """
        Generator that yields NormalizedSignals indefinitely.
        Used for the live background feed (non-demo mode).
        """
        while True:
            for post in self._posts:
                raw = _post_to_raw_signal(post)
                yield normalize_signal(raw)
                await asyncio.sleep(interval_seconds)


# Module-level singleton
mock_social_stream = MockSocialStreamService()
