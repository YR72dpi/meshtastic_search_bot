import requests
import os 
import math

CITY = os.getenv("CITY", "Paris")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# La politique d'usage de Nominatim impose un User-Agent identifiable
OSM_USER_AGENT = "meshtastic-search-bot/1.0 (ton@email.fr)"


def search_place_data(name: str, position=None, radius_m: int = 1000) -> dict:
    print("[BOT] Appel : search_place_data", flush=True)

    params = {
        "q": f"{name}, {CITY}".strip(),
        "format": "jsonv2",
        "extratags": 1,
        "addressdetails": 1,
        "accept-language": "fr",
        "limit": 1,
    }

    if position:
        lat, lon = position
        # 1° de latitude ≈ 111 320 m ; la longitude dépend de la latitude
        d_lat = radius_m / 111_320
        d_lon = radius_m / (111_320 * math.cos(math.radians(lat)))

        params["q"] = name
        params["viewbox"] = (
            f"{lon - d_lon},{lat + d_lat},"
            f"{lon + d_lon},{lat - d_lat}"
        )
        params["bounded"] = 0

    try:
        print(f"[OSM] params : {params}", flush=True)
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers={"User-Agent": OSM_USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()
        return results[0] if results else {}
    except Exception as e:
        print(f"[OSM] Erreur: {e}", flush=True)
        return {}