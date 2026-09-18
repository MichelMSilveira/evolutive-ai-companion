"""Provider-neutral Spotify learning adapter.

The mock mode is safe for demos and tests; OAuth can replace it later.
"""
from __future__ import annotations


class SpotifyAdapter:
    def __init__(self, connected: bool = False):
        self.connected = connected

    def status(self) -> dict:
        return {"connected": self.connected, "mode": "oauth" if self.connected else "mock"}

    def learning_queue(self, level: str = "beginner") -> list[dict]:
        catalog = {
            "beginner": [{"type": "podcast", "title": "Slow English Conversations", "level": "beginner"}],
            "intermediate": [{"type": "playlist", "title": "English for Work", "level": "intermediate"}],
            "advanced": [{"type": "podcast", "title": "Technology and Automation", "level": "advanced"}],
        }
        return catalog.get(level, catalog["beginner"])

    def disconnect(self) -> None:
        self.connected = False
