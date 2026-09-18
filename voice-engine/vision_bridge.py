"""Local bridge from Nova screen selections to Ollama's vision model."""
import base64
import json
import os
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
PET_ROOT = ROOT.parent / "desktop-pet"
REQUEST = PET_ROOT / "vision-request.json"
RESPONSE = PET_ROOT / "vision-response.json"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
VISION_MODEL = os.environ.get("NOVA_VISION_MODEL", "qwen3.5:9b")

VISION_INSTRUCTIONS = (
    "Analise somente os pixels desta imagem. Responda em português, de forma objetiva e curta. "
    "Descreva apenas elementos que estejam realmente visíveis: aplicativo, objeto principal, "
    "estado aparente e textos legíveis. Não adivinhe o que está fora do recorte, não use o histórico "
    "da conversa como prova e não diga que uma ação ocorreu se não houver evidência visual dela. "
    "Não classifique um desenho como Pokémon ou outra franquia apenas pela aparência; quando o nome "
    "não estiver legível, use 'personagem animal estilizado'. "
    "Se não puder identificar algo, escreva 'não identificável'. Se a imagem for uma tela de computador, "
    "isso é uma observação válida e deve ser descrita normalmente. Quando a pergunta pedir confirmação, "
    "comece por 'CONFIRMAÇÃO VISUAL: SIM' somente se houver evidência clara na imagem; caso contrário, "
    "comece por 'CONFIRMAÇÃO VISUAL: NÃO'."
)

def sanitize_visual_answer(answer: str) -> str:
    """Remove classificações de franquia que o modelo pode inferir sem evidência textual."""
    return re.sub(
        r"(?i)\bpersonagem\s+(?:em\s+formato\s+de|com\s+apar[eê]ncia\s+de)\s+pok[eé]mon\b",
        "personagem animal estilizado",
        answer,
    )

def analyze(image_path: str, question: str | None = None) -> str:
    data = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    prompt = VISION_INSTRUCTIONS
    if question:
        prompt += f" Pergunta do usuário: {question}"
    payload = {
        "model": VISION_MODEL,
        "stream": False,
        "messages": [{
            "role": "user",
            "content": prompt,
            "images": [data],
        }],
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()
    answer = response.json().get("message", {}).get("content", "").strip()
    if not answer:
        raise RuntimeError("O modelo visual retornou uma resposta vazia.")
    return sanitize_visual_answer(answer)

def main() -> None:
    handled = None
    while True:
        try:
            if REQUEST.exists():
                request = json.loads(REQUEST.read_text(encoding="utf-8"))
                image_path = request.get("image")
                token = request.get("created_at")
                if image_path and token != handled and Path(image_path).exists():
                    answer = analyze(image_path)
                    RESPONSE.write_text(json.dumps({"answer": answer, "created_at": token}, ensure_ascii=False, indent=2), encoding="utf-8")
                    handled = token
                    print(f"Vision response: {answer}", flush=True)
        except Exception as exc:
            RESPONSE.write_text(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Vision error: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
