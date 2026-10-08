import requests
import os 
import math

CITY = os.getenv("CITY", "Paris")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# La politique d'usage de Nominatim impose un User-Agent identifiable
OSM_USER_AGENT = "meshtastic-search-bot/1.0 (ton@email.fr)"

def _distance_m(lat1, lon1, lat2, lon2) -> float:
    """Distance en mètres entre deux points (Haversine)."""
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


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


def search_place_data(name: str, position=None, radii_m=(1000, 5000, 20000)) -> dict:
    print("[BOT] Appel : search_place_data", flush=True)

    try:
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
                    # le plus proche du nœud demandeur
                    best = min(
                        results,
                        key=lambda r: _distance_m(lat, lon, float(r["lat"]), float(r["lon"])),
                    )
                    best["distance_m"] = round(
                        _distance_m(lat, lon, float(best["lat"]), float(best["lon"]))
                    )
                    return best

                time.sleep(1)  # politique Nominatim : 1 requête/seconde max

        # Repli : pas de position, ou rien trouvé autour
        results = _nominatim({"q": f"{name}, {CITY}".strip(), "limit": 1})
        return results[0] if results else {}

    except Exception as e:
        print(f"[OSM] Erreur: {e}", flush=True)
        return {}