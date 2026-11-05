import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))


def call_ollama(prompt: str) -> str:
    print("[BOT] Appel : call_ollama", flush=True)
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            # Évite la longue phase de réflexion de Qwen 3 et garde le modèle chargé
            "think": False,
            "keep_alive": "30m",
        },
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()["message"]["content"].strip()
    print(f"[OLLAMA] Résultat : {result}", flush=True)
    return result
