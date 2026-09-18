"""Explainable tarot-inspired archetypes for Nova's personality layer."""
from __future__ import annotations

ARCHETYPES = {
    "magician": {"name": "O Mago", "focus": "criatividade e iniciativa", "attribute": "creativity"},
    "hermit": {"name": "O Eremita", "focus": "estudo e reflexão", "attribute": "intelligence"},
    "strength": {"name": "A Força", "focus": "energia e disciplina", "attribute": "energy"},
    "star": {"name": "A Estrela", "focus": "esperança e curiosidade", "attribute": "curiosity"},
    "world": {"name": "O Mundo", "focus": "conexão e realização", "attribute": "sociability"},
}


def dominant_archetype(state: dict) -> dict:
    attributes = state.get("attributes", {})
    key, value = max(attributes.items(), key=lambda pair: pair[1])
    for archetype in ARCHETYPES.values():
        if archetype["attribute"] == key:
            return {**archetype, "score": value}
    return {"name": "O Louco", "focus": "exploração", "score": value}


def advice(state: dict) -> str:
    archetype = dominant_archetype(state)
    return f"{archetype['name']} guia Nova em {archetype['focus']}. Próximo passo: transforme uma pequena intenção em uma ação concreta."
