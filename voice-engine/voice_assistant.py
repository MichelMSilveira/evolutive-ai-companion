"""Local-first voice conversation engine.

Press and hold F8 to record. Speech recognition, language model inference,
and speech synthesis can all run locally. The conversation is saved locally.
"""

from __future__ import annotations

import json
import os
import queue
import sys
import time
from pathlib import Path

import keyboard
import pyttsx3
import requests
import sounddevice as sd
from vosk import KaldiRecognizer, Model


ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
KNOWLEDGE_PATH = ROOT / "knowledge.json"
HISTORY_PATH = ROOT / "conversation.json"
PET_STATE_PATH = ROOT.parent / "desktop-pet" / "nova-state.json"

def update_pet_from_text(text: str) -> str:
    """Apply a voluntary daily check-in without inspecting anything beyond the spoken text."""
    lowered = text.lower()
    event = "conversation"
    if any(word in lowered for word in ("exercise", "bike", "walk", "workout", "exercício", "caminhada", "academia")):
        event = "exercise"
    elif any(word in lowered for word in ("sleep", "rest", "dormi", "descans", "sono")):
        event = "rest"
    elif any(word in lowered for word in ("study", "learn", "estudei", "estudar", "aprendi")):
        event = "study"
    elif any(word in lowered for word in ("eat", "food", "comi", "comida", "refeição")):
        event = "meal"
    elif any(word in lowered for word in ("game", "play", "joguei", "brinquei", "lazer")):
        event = "play"
    state = {"name": "Nova", "level": 1, "xp": 0, "mood": "happy", "events": [], "needs": {"energy": 80, "rest": 80, "hunger": 80, "attention": 80}}
    if PET_STATE_PATH.exists():
        try:
            state.update(json.loads(PET_STATE_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    rewards = {"conversation": 3, "study": 15, "exercise": 12, "rest": 8, "meal": 4, "play": 8}
    state["xp"] += rewards[event]
    state["level"] = 1 + state["xp"] // 100
    state["mood"] = {"exercise": "energetic", "study": "focused", "rest": "resting", "meal": "content", "play": "playful"}.get(event, "happy")
    needs = state.setdefault("needs", {"energy": 80, "rest": 80, "hunger": 80, "attention": 80})
    changes = {"exercise": {"energy": -8, "rest": -5}, "study": {"energy": -3, "attention": 2}, "rest": {"energy": 12, "rest": 15}, "meal": {"hunger": 15, "energy": 3}, "play": {"energy": -2, "attention": 5}, "conversation": {"attention": 4}}
    for key, delta in changes.get(event, {}).items():
        needs[key] = max(0, min(100, needs.get(key, 80) + delta))
    state.setdefault("events", []).append({"type": event, "text": text, "timestamp": time.time()})
    state["events"] = state["events"][-50:]
    PET_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return event
MODEL_PATH = ROOT / "models" / "vosk-model-small-en-us-0.15"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


def load_config() -> dict:
    default = {
        "model": "qwen2.5-coder:1.5b",
        "language": "English",
        "hotkey": "f8",
        "system_prompt": (
            "You are a patient, practical English conversation coach. "
            "Keep replies short and natural. Ask one question at a time. "
            "Correct only important mistakes after the user finishes speaking."
        ),
    }
    if CONFIG_PATH.exists():
        default.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    return default


def load_history() -> list[dict]:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    return []

def load_knowledge() -> dict:
    return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8")) if KNOWLEDGE_PATH.exists() else {}


def save_history(history: list[dict]) -> None:
    HISTORY_PATH.write_text(json.dumps(history[-20:], ensure_ascii=False, indent=2), encoding="utf-8")

def reward_pet() -> None:
    state = {"name": "Nova", "level": 1, "xp": 0, "mood": "happy"}
    if PET_STATE_PATH.exists():
        try:
            state.update(json.loads(PET_STATE_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    state["xp"] += 10
    state["level"] = 1 + state["xp"] // 100
    state["mood"] = "excited"
    PET_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def record_until_release(hotkey: str) -> bytes:
    audio_queue: queue.Queue[bytes] = queue.Queue()

    def callback(indata, _frames, _time, status):
        if status:
            print(f"Audio: {status}", file=sys.stderr)
        audio_queue.put(bytes(indata))

    chunks: list[bytes] = []
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=callback):
        print("Listening... release F8 when finished.")
        while keyboard.is_pressed(hotkey):
            try:
                chunks.append(audio_queue.get(timeout=0.2))
            except queue.Empty:
                pass
    return b"".join(chunks)


def transcribe(audio: bytes, model: Model) -> str:
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.AcceptWaveform(audio)
    result = json.loads(recognizer.FinalResult())
    return result.get("text", "").strip()


def ask_ollama(config: dict, history: list[dict], user_text: str, event: str = "conversation", knowledge: dict | None = None) -> str:
    messages = [{"role": "system", "content": config["system_prompt"]}]
    guidance = {"study": "Respond as a supportive study companion and celebrate learning.", "exercise": "Respond warmly and encourage sustainable movement without medical advice.", "rest": "Respond warmly and support healthy rest and balance.", "meal": "Respond without judging food or body; gently encourage balance.", "play": "Respond playfully and support a healthy balance between work and leisure.", "conversation": "Respond naturally and keep the conversation going."}
    messages.append({"role": "system", "content": guidance.get(event, guidance["conversation"])})
    if knowledge:
        messages.append({"role": "system", "content": "Use these starter English-Portuguese examples when useful: " + json.dumps(knowledge, ensure_ascii=False)})
    messages.extend(history[-8:])
    messages.append({"role": "system", "content": "FINAL FORMAT RULE: Reply in exactly two lines. First line must start with PT: and be Brazilian Portuguese. Second line must start with EN: and be simple English. Do not answer with English only."})
    messages.append({"role": "user", "content": user_text})
    response = requests.post(OLLAMA_URL, json={"model": config["model"], "messages": messages, "stream": False}, timeout=120)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def speak(text: str, engine: pyttsx3.Engine, voices: dict[str, str]) -> None:
    for line in text.splitlines():
        if not line.strip():
            continue
        is_pt = line.strip().lower().startswith("pt:")
        engine.setProperty("voice", voices["pt"] if is_pt else voices["en"])
        engine.say(line.removeprefix("PT:").strip())
    engine.runAndWait()


def main() -> None:
    config = load_config()
    knowledge = load_knowledge()
    history = load_history()
    if not MODEL_PATH.exists():
        print(f"Missing offline speech model: {MODEL_PATH}")
        print("Download the Vosk English model listed in README.md and extract it there.")
        raise SystemExit(1)

    print("Loading local speech model...")
    speech_model = Model(str(MODEL_PATH))
    speaker = pyttsx3.init()
    voices = {"en": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0", "pt": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_PT-BR_MARIA_11.0"}
    print(f"Local assistant ready. Hold {config['hotkey'].upper()} to talk; press Ctrl+C to exit.")

    while True:
        keyboard.wait(config["hotkey"])
        time.sleep(0.15)
        audio = record_until_release(config["hotkey"])
        text = transcribe(audio, speech_model)
        if not text:
            print("I didn't catch that. Try again.")
            continue
        print(f"You: {text}")
        event = update_pet_from_text(text)
        print(f"Nova registered: {event}")
        try:
            answer = ask_ollama(config, history, text, event, knowledge)
        except requests.RequestException as exc:
            print(f"Ollama is unavailable: {exc}")
            continue
        print(f"Assistant: {answer}\n")
        speak(answer, speaker, voices)
        reward_pet()
        history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": answer}])
        save_history(history)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nConversation ended.")
