"""Application flow shared by voice, text and future desktop interfaces."""
from __future__ import annotations

from pathlib import Path
from memory_store import MemoryStore
from nova_core import apply_event, load_state, save_state
from providers import build_prompt
from tarot_archetypes import advice, dominant_archetype


class NovaOrchestrator:
    def __init__(self, state_path: Path, memory_path: Path, personality: str):
        self.state_path = Path(state_path)
        self.memories = MemoryStore(Path(memory_path))
        self.personality = personality

    def prepare(self, user_text: str, event: str = "conversation") -> dict:
        """Record the interaction and return an AI-ready, privacy-scoped context."""
        state = load_state(self.state_path)
        apply_event(state, event, note=user_text)
        save_state(self.state_path, state)
        relevant = self.memories.search(user_text, limit=5)
        return {
            "state": state,
            "archetype": dominant_archetype(state),
            "advice": advice(state),
            "memories": relevant,
            "messages": build_prompt(
                [{"role": "user", "content": user_text}], self.personality
            ),
        }

    def context_for(self, user_text: str) -> dict:
        """Return approved memories without changing evolution state."""
        return {"memories": self.memories.search(user_text, limit=5),
                "messages": build_prompt([], self.personality)}

    def evolve(self, event: str, note: str = "") -> dict:
        """Apply one interaction through the canonical evolution rules."""
        state = load_state(self.state_path)
        apply_event(state, event, note=note)
        state["mood"] = {"study": "focused", "rest": "resting", "creative-work": "creative"}.get(event, "happy")
        state["archetype"] = dominant_archetype(state)["name"]
        state["archetype_advice"] = advice(state)
        save_state(self.state_path, state)
        return state

    def remember(self, content: str, category: str = "profile") -> int:
        return self.memories.add(content, category=category, source="explicit-user-consent")

    def close(self) -> None:
        self.memories.close()
