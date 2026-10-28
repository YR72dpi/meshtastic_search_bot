import requests
import os 
import math
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from opening_hours import OpeningHours

CITY = os.getenv("CITY", "Paris")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# La politique d'usage de Nominatim impose un User-Agent identifiable
OSM_USER_AGENT = "meshtastic-search-bot/1.0 (ton@email.fr)"
TIMEZONE = ZoneInfo(os.getenv("TZ_NAME", "Europe/Paris"))

def _distance_m(lat1, lon1, lat2, lon2) -> float:
    """Distance en mètres entre deux points (Haversine)."""
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _is_open(result: dict):
    """True/False d'après le tag opening_hours, None si absent ou illisible."""
    hours = (result.get("extratags") or {}).get("opening_hours")
    if not hours:
        return None
    try:
        now = datetime.now(TIMEZONE).replace(tzinfo=None)
        return OpeningHours(hours).is_open(now)
    except Exception as e:
        print(f"[OSM] opening_hours illisible ({hours!r}): {e}", flush=True)
        return None


def _pick_best(results: list, position=None) -> tuple[dict, bool]:
    """Choisit le meilleur résultat : ouvert (ou horaires inconnus) en priorité,
    le plus proche de la position si elle est connue.
    Retourne (résultat, tous_fermés)."""
    for r in results:
        r["is_open"] = _is_open(r)
        if position:
            r["distance_m"] = round(
                _distance_m(position[0], position[1], float(r["lat"]), float(r["lon"]))
            )

    def rank(candidates):
        return min(candidates, key=lambda r: r["distance_m"]) if position else candidates[0]

    eligible = [r for r in results if r["is_open"] is not False]
    if eligible:
        return rank(eligible), False
    return rank(results), True


def _nominatim(params: dict) -> list:
    response = requests.get(
        NOMINATIM_URL,
        params={
            "format": "jsonv2",
            "extratags": 1,
            "addressdetails": 1,
            "accept-language": "fr",
            **params,
        },
        headers={"User-Agent": OSM_USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def search_place_data(name: str, position=None, radii_m=(100, 250, 500, 1000, 5000, 20000)) -> dict:
    print("[BOT] Appel : search_place_data", flush=True)

    try:
        closed_fallback = {}
        if position:
            lat, lon = position
            for radius_m in radii_m:
                d_lat = radius_m / 111_320
                d_lon = radius_m / (111_320 * math.cos(math.radians(lat)))

                results = _nominatim({
                    "q": name,
                    "viewbox": f"{lon - d_lon},{lat + d_lat},{lon + d_lon},{lat - d_lat}",
                    "bounded": 1,   # restreint vraiment à la zone
                    "limit": 10,
                })
                print(f"[OSM] rayon {radius_m} m : {len(results)} résultat(s)", flush=True)

                if results:
                    best, all_closed = _pick_best(results, position)
                    if not all_closed:
                        return best
                    # tout est fermé ici : on cherche plus loin un lieu ouvert
                    if not closed_fallback:
                        closed_fallback = best

                time.sleep(1)  # potique Nominatim : 1 requête/seconde max

            if closed_fallback:
                return closed_fallback

        # Repli : pas de position, ou rien trouvé autour
        results = _nominatim({"q": f"{name}, {CITY}".strip(), "limit": 10})
        if not results:
            return {}
        return _pick_best(results)[0]

    except Exception as e:
        print(f"[OSM] Erreur: {e}", flush=True)
        return {}