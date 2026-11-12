import os
import time
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


def _should_retry(status_code: int, payload: Any) -> bool:
    if status_code in {429, 500, 502, 503, 504}:
        return True
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            error_type = error.get("type")
            if error_type in {"rate_limit_exceeded", "server_error", "internal_error"}:
                return True
    return False


def call_vireonix(prompt: str) -> str:
    """Appel au service Vireonix selon l'API OpenAI-compatible publique, avec 2 tentatives et backoff."""
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

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            print(f"[BOT] Appel : call_vireonix (essai {attempt + 1}/2)", flush=True)
            response = requests.post(
                VIREONIX_URL,
                headers=headers,
                json=payload,
                timeout=VIREONIX_TIMEOUT,
            )

            try:
                data = response.json()
            except ValueError:
                data = {}

            if response.status_code == 200:
                result = _extract_content(data).strip()
                if not result:
                    raise ValueError("Réponse Vireonix vide ou non exploitable")
                print(f"[VIREONIX] Résultat : {result}", flush=True)
                return result

            if attempt < 1 and _should_retry(response.status_code, data):
                delay = 2 ** attempt
                print(
                    f"[VIREONIX] Retry après {delay}s (status={response.status_code}, error={data.get('error') if isinstance(data, dict) else data})",
                    flush=True,
                )
                time.sleep(delay)
                continue

            response.raise_for_status()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 1 and isinstance(exc, requests.HTTPError):
                # HTTPError peut masquer un 429 ou 5xx ; si la requête est retryable, on retente.
                status_code = exc.response.status_code if exc.response is not None else 0
                if status_code in {429, 500, 502, 503, 504}:
                    delay = 2 ** attempt
                    print(f"[VIREONIX] Retry après {delay}s (HTTP {status_code})", flush=True)
                    time.sleep(delay)
                    continue
            raise

    if last_error is not None:
        raise last_error

    raise RuntimeError("Réponse Vireonix vide ou non exploitable")
