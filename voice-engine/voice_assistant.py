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
HISTORY_PATH = ROOT / "conversation.json"
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


def save_history(history: list[dict]) -> None:
    HISTORY_PATH.write_text(json.dumps(history[-20:], ensure_ascii=False, indent=2), encoding="utf-8")


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


def ask_ollama(config: dict, history: list[dict], user_text: str) -> str:
    messages = [{"role": "system", "content": config["system_prompt"]}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": user_text})
    response = requests.post(OLLAMA_URL, json={"model": config["model"], "messages": messages, "stream": False}, timeout=120)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def speak(text: str, engine: pyttsx3.Engine) -> None:
    engine.say(text)
    engine.runAndWait()


def main() -> None:
    config = load_config()
    history = load_history()
    if not MODEL_PATH.exists():
        print(f"Missing offline speech model: {MODEL_PATH}")
        print("Download the Vosk English model listed in README.md and extract it there.")
        raise SystemExit(1)

    print("Loading local speech model...")
    speech_model = Model(str(MODEL_PATH))
    speaker = pyttsx3.init()
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
        try:
            answer = ask_ollama(config, history, text)
        except requests.RequestException as exc:
            print(f"Ollama is unavailable: {exc}")
            continue
        print(f"Assistant: {answer}\n")
        speak(answer, speaker)
        history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": answer}])
        save_history(history)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nConversation ended.")
