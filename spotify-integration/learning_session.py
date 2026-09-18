from __future__ import annotations

from spotify_adapter import SpotifyAdapter


def create_activity(level: str = "beginner") -> dict:
    """Create a portfolio-demo activity without requiring Spotify login."""
    item = SpotifyAdapter().learning_queue(level)[0]
    return {
        "source": item,
        "instruction": "Listen for one minute and write down three words you recognize.",
        "follow_up": "Tell Nova what you understood, in English or Portuguese.",
    }
