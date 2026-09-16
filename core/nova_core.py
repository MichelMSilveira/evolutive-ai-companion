"""Core rules for Nova's persistent, user-owned evolution."""
from __future__ import annotations

import json
from pathlib import Path

ATTRIBUTES = ("intelligence", "creativity", "energy", "sociability", "curiosity")
NEEDS = ("hunger", "rest", "fun", "attention")

def new_state() -> dict:
    return {
        "schema": 1,
        "name": "Nova",
        "form": "base-cat",
        "level": 1,
        "xp": 0,
        "attributes": {key: 1 for key in ATTRIBUTES},
        "needs": {key: 80 for key in NEEDS},
        "memory": [],
        "history": []
    }

def load_state(path: Path) -> dict:
    if not path.exists():
        return new_state()
    state = new_state()
    state.update(json.loads(path.read_text(encoding="utf-8")))
    state["attributes"] = {**new_state()["attributes"], **state.get("attributes", {})}
    state["needs"] = {**new_state()["needs"], **state.get("needs", {})}
    return state

def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def apply_event(state: dict, event: str, amount: int = 1, note: str = "") -> dict:
    effects = {
        "conversation": {"xp": 10, "sociability": 1, "attention": 3},
        "study": {"xp": 15, "intelligence": 1, "curiosity": 1},
        "creative-work": {"xp": 12, "creativity": 1, "fun": 2},
        "care": {"xp": 5, "energy": 1, "hunger": 8, "attention": 8},
        "rest": {"rest": 15, "energy": 1},
    }
    for key, value in effects.get(event, {}).items():
        if key == "xp":
            state["xp"] += value * amount
        elif key in state["attributes"]:
            state["attributes"][key] = min(5, state["attributes"][key] + value * amount)
        elif key in state["needs"]:
            state["needs"][key] = min(100, state["needs"][key] + value * amount)
    state["level"] = 1 + state["xp"] // 100
    if state["level"] >= 5:
        state["form"] = "evolved-cat"
    state["history"].append({"event": event, "amount": amount, "note": note})
    state["history"] = state["history"][-50:]
    return state
