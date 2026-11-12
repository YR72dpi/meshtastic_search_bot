import os
from typing import Any

import requests

VIREONIX_URL = os.getenv("VIREONIX_URL", "https://vireonix.ai/v1/chat/completions").rstrip("/")
VIREONIX_API_KEY = os.getenv("VIREONIX_API_KEY", "")
VIREONIX_MODEL = os.getenv("VIREONIX_MODEL", "auto")
VIREONIX_TIMEOUT = int(os.getenv("VIREONIX_TIMEOUT", "180"))


def _extract_content(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""

    if isinstance(payload.get("choices"), list):
        for choice in payload["choices"]:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message") or {}
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    return "".join(
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict)
                    )
            text = choice.get("text")
            if isinstance(text, str) and text.strip():
                return text

    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content

    content = payload.get("content")
    if isinstance(content, str) and content.strip():
        return content

    return ""


def call_vireonix(prompt: str) -> str:
    """Appel au service Vireonix selon l'API OpenAI-compatible publique."""
    if not VIREONIX_URL:
        raise RuntimeError("Vireonix non configuré (VIREONIX_URL vide)")

    headers = {"Content-Type": "application/json"}
    # La doc Vireonix indique qu'aucune clé n'est requise pour l'usage public.
    if VIREONIX_API_KEY:
        headers["Authorization"] = f"Bearer {VIREONIX_API_KEY}"

    payload = {
        "model": VIREONIX_MODEL or "auto",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }

    print("[BOT] Appel : call_vireonix", flush=True)
    response = requests.post(VIREONIX_URL, headers=headers, json=payload, timeout=VIREONIX_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    result = _extract_content(data).strip()
    if not result:
        raise ValueError("Réponse Vireonix vide ou non exploitable")

    print(f"[VIREONIX] Résultat : {result}", flush=True)
    return result
