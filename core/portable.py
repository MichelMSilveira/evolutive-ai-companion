"""Portable character packages that never include private memories by default."""
from __future__ import annotations

import json
from pathlib import Path
from nova_core import load_state


def export_character(state_path: Path, destination: Path) -> None:
    state = load_state(Path(state_path))
    package = {
        "package": "nova-character",
        "version": 1,
        "character": {
            "name": state["name"],
            "form": state["form"],
            "level": state["level"],
            "xp": state["xp"],
            "attributes": state["attributes"],
            "mood": state.get("mood", "happy"),
        },
        "privacy": {"memories_included": False, "history_included": False},
    }
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")


def import_character(source: Path, state_path: Path) -> dict:
    package = json.loads(Path(source).read_text(encoding="utf-8"))
    if package.get("package") != "nova-character":
        raise ValueError("Unsupported Nova package")
    character = package.get("character", {})
    state = load_state(Path(state_path))
    for key in ("name", "form", "level", "xp", "attributes", "mood"):
        if key in character:
            state[key] = character[key]
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    Path(state_path).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state
