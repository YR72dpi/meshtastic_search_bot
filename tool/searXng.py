import os
import requests

SEARXNG_URL = os.getenv("SEARXNG_URL")
SEARCH_RESULTS_LIMIT = 5
MAX_RETRIES = 3


def search_searxng(query: str) -> str:
    print(f"[BOT] Appel : search_searxng")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                SEARXNG_URL,
                params={
                    "q": query,
                    "format": "json"
                },
                headers={
                    "User-Agent": "meshtastic-search-bot/1.0 (+https://github.com/YR72dpi/meshtastic_search_bot)"
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results") or []

            if not results:
                print(
                    f"[SEARXNG] Aucune réponse sur tentative {attempt}/{MAX_RETRIES}; nouvelle tentative...",
                    flush=True,
                )
                if attempt < MAX_RETRIES:
                    continue
                return ""

            # Tri par score décroissant (SearXNG renvoie déjà souvent ce tri).
            results.sort(key=lambda r: r.get("score", 0), reverse=True)
            contents = [
                r["content"]
                for r in results[:SEARCH_RESULTS_LIMIT]
                if r.get("content")
            ]

            if not contents:
                print(
                    f"[SEARXNG] Résultats reçus mais sans contenu exploitable sur tentative {attempt}/{MAX_RETRIES}; nouvelle tentative...",
                    flush=True,
                )
                if attempt < MAX_RETRIES:
                    continue
                return ""

            print(f"[SEARXNG] {''.join(contents)}", flush=True)
            return "\n\n".join(contents)

        except Exception as e:
            print(
                f"[SEARXNG] Erreur tentative {attempt}/{MAX_RETRIES}: {e}",
                flush=True,
            )
            if attempt >= MAX_RETRIES:
                return ""

    return ""