import requests
import os 

CITY = os.getenv("CITY")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# La politique d'usage de Nominatim impose un User-Agent identifiable
OSM_USER_AGENT = "meshtastic-search-bot/1.0 (ton@email.fr)"


def search_place_data(name: str) -> str:
    print("[BOT] Appel : search_place_data", flush=True)

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": f"{name}, {CITY}".strip(),
                "format": "jsonv2",
                "extratags": 1,
                "limit": 1,
            },
            headers={"User-Agent": OSM_USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            return ""

        place = results[0]
        
        return place
    except Exception as e:
        print(f"[OSM] Erreur: {e}", flush=True)
        return ""