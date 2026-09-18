# Local Voice Assistant

A small, finished portfolio engine for local voice conversation practice.

## Pipeline

Microphone → offline Vosk speech recognition → Ollama local model → text output + Windows voice output.

The assistant keeps a short local conversation history and uses a configurable system prompt so personality stays stable when the language changes later.

## Language switching

Nova starts in Brazilian Portuguese (`response_language: "pt"`). During the conversation, say one of these commands:

- `falar em português`
- `falar em inglês`
- `modo bilíngue`
- `modo automático`

The language changes only the response and speech language; it does not replace Nova's personality, memories or operating mode.

## Setup

1. Start Ollama and make sure the model in `config.json` is available.
2. Install Python dependencies:

   `python -m pip install -r requirements.txt`

3. Download the small English Vosk model from the official Vosk models page and extract it as:

   `models/vosk-model-small-en-us-0.15`

4. Run:

   `python voice_assistant.py`

5. Hold **+** while speaking, then release it. Press **-** to select an area of the screen for vision. The transcript is written to the local Nova log and the assistant replies with text and audio.

## Portfolio scope

This is a local proof of concept, not a production product. It intentionally avoids accounts, payments, cloud storage, and exposed API keys. Future extensions can add language switching, a remote provider adapter, better speech recognition, and a small desktop interface without changing the conversation engine.
