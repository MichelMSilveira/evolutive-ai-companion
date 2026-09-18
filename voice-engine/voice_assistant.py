"""Local-first voice conversation engine.

Press and hold F8 to record. Speech recognition, language model inference,
and speech synthesis can all run locally. The conversation is saved locally.
"""

from __future__ import annotations

import json
import html
import asyncio
import tempfile
import re
import sys
import os
import queue
import sys
import time
import unicodedata
from pathlib import Path

import keyboard
import numpy as np
import requests
import sounddevice as sd
from faster_whisper import WhisperModel
import edge_tts
import pygame
import mss
import mss.tools
try:
    from colorama import just_fix_windows_console
    just_fix_windows_console()
except ImportError:
    pass


ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "core"))
from memory_store import MemoryStore
from orchestrator import NovaOrchestrator
from vision_bridge import analyze as analyze_screen
CONFIG_PATH = ROOT / "config.json"
KNOWLEDGE_PATH = ROOT / "knowledge.json"
HISTORY_PATH = ROOT / "conversation.json"
CONSOLE_LOG = ROOT.parent / "desktop-pet" / "nova-console.log"

class LocalLog:
    def write(self, text):
        try:
            with CONSOLE_LOG.open("a", encoding="utf-8") as handle:
                handle.write(text)
        except OSError:
            pass
    def flush(self):
        pass
MEMORY_PATH = ROOT.parent / "data" / "nova-memory.db"
PET_STATE_PATH = ROOT.parent / "desktop-pet" / "nova-state.json"
CAPTION_STATE_PATH = ROOT.parent / "desktop-pet" / "caption-live.json"
STOP_REQUEST_PATH = ROOT.parent / "desktop-pet" / "nova-stop.json"
CAPTION_SYNC_FACTOR = 1.35
CAPTION_LEAD_MS = 200
SCREEN_CAPTURE_PATH = Path(tempfile.gettempdir()) / "nova-current-screen.png"
VISUAL_REQUEST_WORDS = (
    "tela", "screen", "enxerg", "enxerga", "vendo", "veja", "olha", "olhe", "visual",
    "imagem", "na tela do blender", "o que está acontecendo", "o que esta acontecendo", "o que aparece",
    "what do you see", "what is on the screen", "look at the screen",
)
VISUAL_CONFIRMATION_WORDS = (
    "confirma", "confirmar", "verifica", "verificar", "deu certo", "funcionou",
    "foi criado", "foi criada", "foi adicionado", "foi adicionada", "apareceu",
    "esta na tela", "está na tela", "criei", "adicionei", "coloquei", "consegui",
    "did it work", "was it created", "is it there", "i created", "i added",
)
RECOVERY_WORDS = (
    "nao deu certo", "não deu certo", "nao funcionou", "não funcionou",
    "deu errado", "nao consigo", "não consigo", "nao consegui", "não consegui",
    "nao esta funcionando", "não está funcionando", "nao esta acontecendo", "não está acontecendo",
    "nao entendi", "não entendi",
    "nao compreendi", "não compreendi", "nao apareceu", "não apareceu",
    "nao criou", "não criou", "nao fez", "não fez", "continua igual",
    "voce nao entendeu", "você não entendeu", "voce esta repetindo", "você está repetindo",
    "isso nao resolve", "isso não resolve", "it did not work", "it didn't work",
    "i don't understand", "i do not understand", "it is still the same",
)
INSTRUCTION_WORDS = (
    "como faco", "como faço", "como fazer", "o que eu faco", "o que eu faço",
    "qual o passo", "qual e o passo", "qual é o passo", "me ensina",
    "me mostra como", "how do i", "how can i", "what is the next step",
)

def is_visual_request(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in VISUAL_REQUEST_WORDS)


def is_visual_confirmation_request(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in VISUAL_CONFIRMATION_WORDS)


def is_recovery_request(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in RECOVERY_WORDS)


def is_instruction_request(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in INSTRUCTION_WORDS)

def capture_current_screen() -> Path:
    """Capture the primary monitor locally for an explicit visual question."""
    with mss.mss() as capture:
        monitor = capture.monitors[1] if len(capture.monitors) > 1 else capture.monitors[0]
        shot = capture.grab(monitor)
        mss.tools.to_png(shot.rgb, shot.size, output=str(SCREEN_CAPTURE_PATH))
    return SCREEN_CAPTURE_PATH

def get_current_visual_observation(question: str) -> str:
    image_path = capture_current_screen()
    return analyze_screen(str(image_path), question=question)

def write_caption(text: str, index: int = -1, active: bool = False, boundaries: list | None = None, started_at: float | None = None) -> None:
    CAPTION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CAPTION_STATE_PATH.write_text(json.dumps({"text": text, "index": index, "active": active, "boundaries": boundaries or [], "started_at": started_at}, ensure_ascii=False), encoding="utf-8")


def stop_requested(since: float | None = None) -> bool:
    """Read the desktop stop button without coupling the two processes."""
    try:
        requested_at = float(json.loads(STOP_REQUEST_PATH.read_text(encoding="utf-8")).get("requested_at", 0))
        return since is None or requested_at > since
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False

async def synthesize_with_boundaries(text: str, voice: str, output: Path) -> list[dict]:
    communication = edge_tts.Communicate(text, voice, rate="-4%", pitch="+0Hz")
    audio = bytearray()
    boundaries = []
    async for chunk in communication.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            offset = chunk.get("offset", 0)
            if hasattr(offset, "total_seconds"):
                offset = offset.total_seconds() * 1000
            else:
                offset = float(offset) / 10000
            boundaries.append({"offset_ms": offset, "text": chunk.get("text", "")})
    output.write_bytes(audio)
    return boundaries

def update_pet_from_text(text: str) -> str:
    """Classify a voluntary check-in; Nova Core owns all state changes."""
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
    return event
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
COLORS = {"user": "\033[96m", "you-en": "\033[94m", "en": "\033[92m", "pt": "\033[97m", "reset": "\033[0m"}


def normalize_language_mode(value: str | None) -> str:
    """Normalize the response language without changing Nova's personality."""
    normalized = (value or "pt").strip().casefold()
    aliases = {
        "pt-br": "pt",
        "pt_br": "pt",
        "português": "pt",
        "portugues": "pt",
        "en-us": "en",
        "en_us": "en",
        "english": "en",
        "inglês": "en",
        "ingles": "en",
        "both": "bilingual",
        "bilíngue": "bilingual",
        "bilingue": "bilingual",
        "automatic": "auto",
        "automático": "auto",
        "automatico": "auto",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in {"pt", "en", "bilingual", "auto"} else "pt"


def folded(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )


def detect_language_command(text: str) -> str | None:
    """Return a requested response language, if the user explicitly asked for one."""
    value = folded(text)
    bilingual_markers = (
        "modo bilingue", "modo bilingue", "falar nos dois idiomas",
        "responder nos dois idiomas", "portugues e ingles", "english and portuguese",
        "both languages", "bilingual mode",
    )
    if any(marker in value for marker in bilingual_markers):
        return "bilingual"

    portuguese_markers = (
        "falar em portugues", "responder em portugues", "mudar para portugues",
        "trocar para portugues", "modo portugues", "portugues por favor",
        "speak portuguese", "respond in portuguese", "switch to portuguese",
    )
    if any(marker in value for marker in portuguese_markers):
        return "pt"

    english_markers = (
        "falar em ingles", "responder em ingles", "mudar para ingles",
        "trocar para ingles", "modo ingles", "ingles por favor",
        "speak english", "respond in english", "switch to english",
    )
    if any(marker in value for marker in english_markers):
        return "en"

    automatic_markers = (
        "modo automatico", "acompanhe meu idioma", "responda no meu idioma",
        "follow my language", "automatic language", "auto language",
    )
    if any(marker in value for marker in automatic_markers):
        return "auto"
    return None


def language_instruction(language_mode: str) -> str:
    if language_mode == "pt":
        return "LANGUAGE RULE: Reply only in Brazilian Portuguese. Do not include English translations or YOU-EN/EN labels."
    if language_mode == "en":
        return "LANGUAGE RULE: Reply only in natural English. Do not include Portuguese translations or YOU-PT/PT labels."
    if language_mode == "bilingual":
        return "LANGUAGE RULE: Reply in exactly four short lines: YOU-EN (corrected English), YOU-PT (Brazilian Portuguese translation), EN (answer in English), PT (Brazilian Portuguese translation)."
    return "LANGUAGE RULE: Reply in the same language the user is currently using. If unclear, use Brazilian Portuguese. Do not translate unless asked."

def colored(kind: str, text: str) -> str:
    # ANSI colors work in modern Windows Terminal and remain readable elsewhere.
    color = COLORS.get(kind, "")
    return f"{color}{text}{COLORS['reset']}"

def ordered_response(text: str) -> list[tuple[str, str]]:
    """Normalize model output into the portfolio learning format."""
    found = re.findall(r"(YOU-EN|YOU-PT|EN|PT):\s*(.*?)(?=\s+(?:YOU-EN|YOU-PT|EN|PT):|$)", text, flags=re.IGNORECASE | re.DOTALL)
    values = {}
    for tag, value in found:
        values.setdefault(tag.upper(), value.strip())
    return [(tag, values[tag]) for tag in ("YOU-EN", "YOU-PT", "EN", "PT") if values.get(tag)]


def response_for_language(text: str, language_mode: str) -> str:
    """Keep a model that ignores the format rule from leaking another language."""
    chunks = ordered_response(text)
    if not chunks or language_mode not in {"pt", "en"}:
        return text
    allowed = ("YOU-PT", "PT") if language_mode == "pt" else ("YOU-EN", "EN")
    filtered = "\n".join(f"{tag}: {line}" for tag, line in chunks if tag in allowed)
    if filtered:
        return filtered
    fallback = "Não consegui formular uma resposta em português agora." if language_mode == "pt" else "I could not formulate an answer in English right now."
    return f"{'PT' if language_mode == 'pt' else 'EN'}: {fallback}"


def visual_confirmation_is_positive(observation: str | None) -> bool:
    return "confirmacao visual: sim" in folded(observation or "")


def guard_modelista_response(text: str, visual_observation: str | None, language_mode: str) -> str:
    """Prevent the model from claiming execution without a positive visual check."""
    if visual_confirmation_is_positive(visual_observation):
        return text
    normalized = folded(text)
    claim_markers = (
        "vamos criar", "vou criar", "iremos criar", "criamos", "criei",
        "foi criado", "foi criada", "esta criado", "esta criada",
        "esta na tela", "voce pode ver que", "agora, a esfera",
    )
    if not any(marker in normalized for marker in claim_markers):
        return text

    safe_text = text
    safe_text = re.sub(
        r"(?i)(?:agora,?\s*)?(?:a|o|um|uma)\s+[^.!?\n]{0,80}\s+est[aá]\s+(?:criad[oa]|na tela|pront[oa]|concluíd[oa]|feito[oa])[^.!?\n]*[.!?]?",
        "Ainda não executei nem confirmei essa criação.",
        safe_text,
    )
    safe_text = re.sub(
        r"(?i)\b(?:vamos|vou|iremos)\s+(?:criar|adicionar|selecionar|alterar|abrir|iniciar)\b",
        "posso apenas orientar como executar",
        safe_text,
    )
    safe_text = re.sub(
        r"(?i)\b(?:já\s+)?(?:criamos|adicionamos|selecionamos|alteramos|abrimos|iniciamos)\b",
        "ainda não executei essa etapa",
        safe_text,
    )
    safe_text = re.sub(
        r"(?i)\bvocê pode ver que [^.!?\n]*(?:está|esta) na tela[^.!?\n]*[.!?]?",
        "a tela ainda precisa ser verificada visualmente.",
        safe_text,
    )
    safe_text = re.sub(r"(?im)^(?:YOU-EN|YOU-PT|EN|PT):\s*", "", safe_text).strip()
    tag = "PT" if language_mode in ("pt", "auto", "bilingual") else "EN"
    notice = (
        "Ainda não executei nem confirmei nenhuma criação; estou apenas orientando. "
        "Escolha uma opção e autorize antes de qualquer execução."
        if tag == "PT" else
        "I have not executed or confirmed any creation; I am only giving guidance. "
        "Choose an option and authorize it before any execution."
    )
    return f"{tag}: {notice} {safe_text}"


def load_config() -> dict:
    default = {
        "model": "qwen2.5-coder:1.5b",
        "language": "English",
        "response_language": "pt",
        "transcription_language": "pt",
        "hotkey": "f8",
        "system_prompt": (
            "You are Nova, a patient and practical local companion. "
            "Keep your personality, identity and memory stable when the conversation language changes. "
            "Answer the user's actual question first; do not merely translate or rephrase it. "
            "If the transcription is unclear, identify the uncertain phrase honestly and ask one focused clarification. "
            "Keep replies short and natural. Ask one question at a time. "
            "Never write code, modify a file, operate Blender, or execute a technical action without explicit permission in the current conversation."
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
    PET_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PET_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def voice_hotkey_is_pressed(hotkey: str) -> bool:
    if hotkey == "add":
        return keyboard.is_pressed("add")
    return keyboard.is_pressed("shift") and keyboard.is_pressed("=")

def wait_for_voice_hotkey(hotkeys: tuple[str, ...]) -> str:
    while True:
        for hotkey in hotkeys:
            if voice_hotkey_is_pressed(hotkey):
                return hotkey
        time.sleep(0.02)

def record_until_release(hotkey: str) -> bytes:
    audio_queue: queue.Queue[bytes] = queue.Queue()

    def callback(indata, _frames, _time, status):
        if status:
            print(f"Audio: {status}", file=sys.stderr)
        audio_queue.put(bytes(indata))

    chunks: list[bytes] = []
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=callback):
        print("Listening... release F8 when finished.")
        while voice_hotkey_is_pressed(hotkey):
            try:
                chunks.append(audio_queue.get(timeout=0.2))
            except queue.Empty:
                pass
    return b"".join(chunks)


def transcribe(audio: bytes, model: WhisperModel, language: str | None = "pt") -> str:
    samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    options = {"task": "transcribe", "vad_filter": True, "beam_size": 5}
    if language in ("pt", "en"):
        options["language"] = language
        options["initial_prompt"] = "Conversa natural em português brasileiro." if language == "pt" else "Natural English conversation."
    segments, _info = model.transcribe(samples, **options)
    return " ".join(segment.text.strip() for segment in segments).strip()


def ask_ollama(config: dict, history: list[dict], user_text: str, event: str = "conversation", knowledge: dict | None = None, memories: list[dict] | None = None, mode: str = "professional", visual_observation: str | None = None, language_mode: str = "pt", recovery_mode: bool = False) -> str:
    messages = [{"role": "system", "content": config["system_prompt"]}]
    guidance = {"study": "Respond as a supportive study companion and celebrate learning.", "exercise": "Respond warmly and encourage sustainable movement without medical advice.", "rest": "Respond warmly and support healthy rest and balance.", "meal": "Respond without judging food or body; gently encourage balance.", "play": "Respond playfully and support a healthy balance between work and leisure.", "conversation": "Respond naturally and keep the conversation going."}
    messages.append({"role": "system", "content": guidance.get(event, guidance["conversation"])})
    mode_guidance = {"professional": "Focus on work, programming, automation, languages and digital products.", "personal": "Be warm and conversational about daily life, hobbies, music, family and feelings. Do not force work topics.", "study": "Act as a patient English coach with short gentle corrections.", "modelista": "MODO MODELISTA: atue como orientadora de modelagem 3D no Blender. Quando o usuário perguntar como fazer algo, primeiro apresente: objetivo entendido, opções possíveis, opção recomendada, passos iniciais e a confirmação necessária. Explique o caminho em passos curtos, citando menus e atalhos. Fale sempre no futuro orientativo: 'você pode', 'o próximo passo seria' ou 'se você autorizar'. Nunca diga 'criei', 'criamos', 'está criado', 'está na tela' ou equivalente sem EVIDÊNCIA VISUAL ATUAL com confirmação positiva. Se o usuário disser que não funcionou, não entendeu ou pedir novamente como fazer, abandone o raciocínio anterior e faça um diagnóstico curto antes de orientar. Não escreva código, não altere arquivos, não opere o Blender e não execute nenhuma ação técnica sem uma autorização explícita do usuário nesta conversa. Uma pergunta ou pedido de explicação não é autorização para executar. Depois de apresentar as opções, aguarde a escolha ou confirmação do usuário. Peça confirmação adicional antes de qualquer ação destrutiva."}
    messages.append({"role": "system", "content": mode_guidance.get(mode, mode_guidance["professional"])})
    if knowledge:
        messages.append({"role": "system", "content": "Use these starter English-Portuguese examples when useful: " + json.dumps(knowledge, ensure_ascii=False)})
    if memories:
        messages.append({"role": "system", "content": "User-approved memories (use only when relevant): " + json.dumps([m["content"] for m in memories], ensure_ascii=False)})
    if visual_observation:
        messages.append({"role": "system", "content": "EVIDÊNCIA VISUAL ATUAL, NÃO INCLUA FATOS ALÉM DELA. Use-a para confirmar somente o que estiver visível:\n" + visual_observation})
    elif is_visual_request(user_text) or is_visual_confirmation_request(user_text):
        messages.append({"role": "system", "content": "NÃO HÁ EVIDÊNCIA VISUAL ATUAL. Você não está vendo a tela e não pode confirmar criação, seleção, alteração ou sucesso de nenhuma etapa. Diga isso claramente e peça uma verificação visual, sem adivinhar."})
    # When the user says the plan failed or asks again how to do it, the old
    # assistant reasoning is a liability. Start the diagnosis without it.
    messages.extend([] if recovery_mode else history[-8:])
    if recovery_mode:
        messages.append({"role": "system", "content": "CORREÇÃO DE ROTA: o usuário informou que a tentativa anterior falhou, ficou confusa ou não respondeu ao que foi perguntado. Abandone o plano anterior sem defendê-lo. Responda primeiro reconhecendo o problema, depois use a evidência visual atual se houver, e ofereça somente um próximo passo verificável. Não diga que algo foi feito."})
    if is_instruction_request(user_text):
        messages.append({"role": "system", "content": "PEDIDO ATUAL DE INSTRUÇÃO: responda exatamente como fazer a tarefa. Não continue uma ação anterior, não assuma que qualquer etapa foi concluída e não transforme a orientação em execução. Liste no máximo duas opções, recomende uma e termine pedindo autorização antes de qualquer ação."})
    messages.append({"role": "system", "content": language_instruction(language_mode)})
    messages.append({"role": "system", "content": "The conversation history may contain another language. Follow the current LANGUAGE RULE instead of copying the old language format."})
    messages.append({"role": "user", "content": user_text})
    response = requests.post(OLLAMA_URL, json={"model": config["model"], "messages": messages, "stream": False}, timeout=120)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def speak(text: str, voices: dict[str, str], mode: str = "professional", language_mode: str = "pt", cancel_since: float | None = None) -> None:
    """Use natural neural voices; Ollama and memory remain local."""
    chunks = re.findall(r"(YOU-EN|YOU-PT|PT|EN):\s*(.*?)(?=\s+(?:YOU-EN|YOU-PT|PT|EN):|$)", text, flags=re.IGNORECASE | re.DOTALL)
    lines = [(tag, content.strip()) for tag, content in chunks]
    if language_mode == "pt":
        lines = [(tag, content) for tag, content in lines if tag.upper() in ("PT", "YOU-PT")]
    elif language_mode == "en":
        lines = [(tag, content) for tag, content in lines if tag.upper() in ("EN", "YOU-EN")]
    if not lines:
        fallback_tag = "PT" if language_mode in ("pt", "auto") else "EN"
        lines = [(fallback_tag, line.strip()) for line in text.splitlines() if line.strip()]
    for tag, line in lines:
        if stop_requested(cancel_since):
            write_caption("", -1, False)
            return
        if not line:
            continue
        is_portuguese = tag.upper() in ("PT", "YOU-PT") or (tag.upper() not in ("EN", "YOU-EN") and language_mode in ("pt", "auto"))
        voice = "pt-BR-FranciscaNeural" if is_portuguese else "en-US-JennyNeural"
        clean_line = line
        words = clean_line.split()
        write_caption(clean_line, 0, True)
        output = Path(tempfile.gettempdir()) / f"nova_{time.time_ns()}.mp3"
        try:
            boundaries = asyncio.run(synthesize_with_boundaries(clean_line, voice, output))
        except Exception as exc:
            print(f"Word timing unavailable; using safe fallback: {exc}")
            boundaries = []
            asyncio.run(edge_tts.Communicate(clean_line, voice, rate="-4%", pitch="+0Hz").save(str(output)))
        pygame.mixer.init()
        pygame.mixer.music.load(str(output))
        pygame.mixer.music.play()
        started = time.monotonic()
        started_wall = time.time()
        while pygame.mixer.music.get_busy():
            if stop_requested(cancel_since):
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                output.unlink(missing_ok=True)
                write_caption("", -1, False)
                print("Nova interrupted by user.")
                return
            if boundaries:
                playback_ms = max(0, pygame.mixer.music.get_pos() + CAPTION_LEAD_MS)
                index = max((i for i, item in enumerate(boundaries) if item.get("offset_ms", 0) <= playback_ms), default=0)
                write_caption(clean_line, index, True)
            else:
                word_interval = max(0.22, len(clean_line) / 55 / max(1, len(words))) * 1.35
                index = min(len(words) - 1, int((time.monotonic() - started) / word_interval)) if words else -1
                write_caption(clean_line, index, True)
            time.sleep(0.05)
        pygame.mixer.quit()
        output.unlink(missing_ok=True)
        write_caption(clean_line, -1, False)


def main() -> None:
    sys.stdout = LocalLog()
    sys.stderr = sys.stdout
    config = load_config()
    knowledge = load_knowledge()
    history = load_history()
    orchestrator = NovaOrchestrator(PET_STATE_PATH, MEMORY_PATH, config.get("system_prompt", "You are Nova, a helpful local companion."))
    print(f"Loading local Whisper model ({config.get('whisper_model', 'base')})...")
    speech_model = WhisperModel(config.get("whisper_model", "base"), device="cpu", compute_type="int8")
    voices = {"en": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0", "pt": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_PT-BR_MARIA_11.0"}
    voice_hotkeys = tuple(config.get("voice_hotkeys", [config.get("hotkey", "shift+=")]))
    print("Local assistant ready. Hold + to talk; press Ctrl+C to exit.")
    conversation_mode = "modelista"
    language_mode = normalize_language_mode(config.get("response_language", "pt"))
    input_language = normalize_language_mode(config.get("transcription_language", language_mode))
    print(f"Nova language: {language_mode}")
    print(f"Nova transcription: {input_language}")

    while True:
        hotkey = wait_for_voice_hotkey(voice_hotkeys)
        time.sleep(0.15)
        try:
            audio = record_until_release(hotkey)
        except Exception as exc:
            print(f"Microphone error: {type(exc).__name__}: {exc}")
            print("Returning to listening mode. Check the microphone and try again.")
            continue
        try:
            text = transcribe(audio, speech_model, input_language if input_language in {"pt", "en"} else None)
        except Exception as exc:
            print(f"Speech recognition error: {type(exc).__name__}: {exc}")
            print("Returning to listening mode. Try a shorter phrase.")
            continue
        if not text:
            print("I didn't catch that. Try again.")
            continue
        print(colored("user", f"You: {text}"))
        lowered = text.lower()
        requested_language = detect_language_command(text)
        if requested_language:
            language_mode = requested_language
            if requested_language in {"pt", "en"}:
                input_language = requested_language
            elif requested_language == "auto":
                input_language = "auto"
            print(f"Nova language: {language_mode}")
        if "modo pessoal" in lowered:
            conversation_mode = "personal"
            print("Nova mode: personal")
        elif "modo profissional" in lowered:
            conversation_mode = "professional"
            print("Nova mode: professional")
        elif "modo estudo" in lowered or "modo de estudo" in lowered:
            conversation_mode = "study"
            print("Nova mode: study")
        elif "modo modelista" in lowered or "modo modelagem" in lowered or "modelista 3d" in lowered or "modo blender" in lowered:
            conversation_mode = "modelista"
            print("Nova mode: modelista")
        try:
            event = update_pet_from_text(text)
            core_event = {"exercise": "care", "meal": "care", "play": "creative-work"}.get(event, event)
            orchestrator.evolve(core_event, text)
        except Exception as exc:
            print(f"Pet state warning: {type(exc).__name__}: {exc}")
            event = "conversation"
        print(f"Nova registered: {event}")
        remember = any(marker in text.lower() for marker in ("lembre que", "remember that", "my name is", "meu nome é"))
        if remember:
            orchestrator.remember(text, category="profile")
            print("Nova memory: saved with your spoken consent")
        # Read through the shared orchestration boundary; evolution migration
        # stays separate until the legacy pet state has a compatibility test.
        memories = orchestrator.context_for(text)["memories"]
        visual_observation = None
        recovery_mode = conversation_mode == "modelista" and is_recovery_request(text)
        if recovery_mode:
            print("Nova recovery: descartando o raciocínio anterior e diagnosticando o estado atual.")
        if is_visual_request(text) or (conversation_mode == "modelista" and (is_visual_confirmation_request(text) or recovery_mode)):
            print("Nova vision: capturando a tela atual...")
            try:
                visual_observation = get_current_visual_observation(text)
                print(f"Nova vision: evidência recebida: {visual_observation}")
            except Exception as exc:
                print(f"Nova vision unavailable: {type(exc).__name__}: {exc}")
        try:
            turn_started_at = time.time()
            answer = ask_ollama(config, history, text, event, knowledge, memories, conversation_mode, visual_observation, language_mode, recovery_mode)
            if stop_requested(turn_started_at):
                print("Nova response interrupted by user.")
                continue
            if conversation_mode == "modelista":
                answer = guard_modelista_response(answer, visual_observation, language_mode)
            answer = response_for_language(answer, language_mode)
        except Exception as exc:
            print(f"Assistant response error: {type(exc).__name__}: {exc}")
            print("Returning to listening mode.")
            continue
        chunks = ordered_response(answer)
        if chunks:
            for tag, line in chunks:
                kind = tag.lower()
                print(colored(kind, f"{tag.upper()}: {line.strip()}"))
        else:
            print(colored("en", f"Assistant: {answer}"))
        try:
            speak(answer, voices, conversation_mode, language_mode, cancel_since=turn_started_at)
        except Exception as exc:
            print(f"Audio output unavailable: {exc}")
            print("Continuing without audio. Returning to listening mode.")
        history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": answer}])
        save_history(history)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nConversation ended.")
