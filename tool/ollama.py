import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")


def call_ollama(prompt: str) -> str:
    print("[BOT] Appel : call_ollama", flush=True)
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()["message"]["content"].strip()
    print(f"[OLLAMA] Résultat : {result}", flush=True)
    return result
