import os
import requests

VIREONIX_URL = os.getenv(
    "VIREONIX_URL",
    "https://vireonix.ai/v1/chat/completions"
)


def call_vireonix(prompt: str) -> str:
    print(f"[BOT] Appel : call_vireonix")
    print(f"[BOT] Appel : {prompt}", flush=True)
    """Envoie un prompt à Vireonix et renvoie sa réponse. Lève une exception si l'appel échoue."""
    response = requests.post(
        VIREONIX_URL,
        headers={
            "Content-Type": "application/json"
        },
        json={
            "model": "auto",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        },
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    result = data["choices"][0]["message"]["content"].strip()
    print(f"[VIREONIX] Résultat : {result}", flush=True)
    return result
