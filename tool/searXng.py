import os
import requests

SEARXNG_URL = os.getenv("SEARXNG_URL")
SEARCH_RESULTS_LIMIT = 3

def search_searxng(query: str) -> str:
    print(f"[BOT] Appel : search_searxng")

    try:
        response = requests.get(
            SEARXNG_URL,
            params={
                "q": query,
                "format": "json"
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        # Tri par score décroissant (SearXNG renvoie déjà souvent ce tri).
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        contents = [
            r["content"]
            for r in results[:SEARCH_RESULTS_LIMIT]
            if r.get("content")
        ]
        print(f"[SEARXNG] {"".join(contents)}",flush=True)
        return "\n\n".join(contents)
    except Exception as e:
        print(f"[SEARXNG] Erreur: {e}", flush=True)
        return ""