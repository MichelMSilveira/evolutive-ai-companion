"""Provider contract used by the orchestration layer."""
from __future__ import annotations
from typing import Protocol

class AIProvider(Protocol):
    def respond(self, messages: list[dict[str, str]]) -> str:
        """Return an answer without changing Nova's state."""

def build_prompt(messages: list[dict[str, str]], personality: str) -> list[dict[str, str]]:
    """Keep identity separate from language and conversation history."""
    return [{"role": "system", "content": personality}, *messages]
