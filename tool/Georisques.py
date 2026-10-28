import os
import time

import requests

CITY = os.getenv("CITY", "Paris, France")
GEORISQUES_URL = "https://www.georisques.gouv.fr/api/v1/resultats_rapport_risque"
GEORISQUES_USER_AGENT = "MeshtasticSearchBot/1.0"
# Durée du cache en secondes (défaut : 7 jours)
GEORISQUES_CACHE_TTL = int(os.getenv("GEORISQUES_CACHE_TTL", str(7 * 24 * 3600)))
GEORISQUES_STATUSES = {
    "Risque Existant",
    "Risque Existant - modéré",
}


_cache: dict[str, tuple[float, str]] = {}


def georisque_lookup() -> str:
    """Liste les risques communaux existants (résultat mis en cache)."""
    print("[BOT] Appel : georisque_lookup", flush=True)

    cached = _cache.get(CITY)
    if cached and time.monotonic() - cached[0] < GEORISQUES_CACHE_TTL:
        print("[GEORISQUES] Résultat servi depuis le cache.", flush=True)
        return cached[1]

    message, ok = _fetch_message()
    if ok:
        _cache[CITY] = (time.monotonic(), message)
    return message


def _fetch_message() -> tuple[str, bool]:
    """Interroge l'API ; retourne (message, succès)."""
    for attempt in range(2):
        try:
            response = requests.get(
                GEORISQUES_URL,
                params={"adresse": CITY},
                headers={
                    "accept": "application/json",
                    "User-Agent": GEORISQUES_USER_AGENT,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            break
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == 0:
                print(f"[GEORISQUES] Connexion interrompue, nouvel essai : {e}", flush=True)
                time.sleep(1)
                continue
            print(f"[GEORISQUES] Erreur de requête : {e}", flush=True)
            return "❌ Service Géorisques indisponible.", False
        except requests.RequestException as e:
            print(f"[GEORISQUES] Erreur de requête : {e}", flush=True)
            return "❌ Service Géorisques indisponible.", False
        except ValueError as e:
            print(f"[GEORISQUES] Réponse JSON invalide : {e}", flush=True)
            return "❌ Réponse Géorisques invalide.", False

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("commune"), dict)
        or not isinstance(data.get("risquesNaturels"), dict)
        or not isinstance(data.get("risquesTechnologiques"), dict)
    ):
        print("[GEORISQUES] Format de réponse invalide.", flush=True)
        return "❌ Réponse Géorisques invalide.", False

    risks = []
    for category in ("risquesNaturels", "risquesTechnologiques"):
        for risk in data[category].values():
            if (
                isinstance(risk, dict)
                and risk.get("libelleStatutCommune") in GEORISQUES_STATUSES
            ):
                label = risk.get("libelle")
                if isinstance(label, str):
                    risks.append(label)

    city = data["commune"].get("libelle", CITY)
    if not risks:
        return f"✅ Aucun risque communal recensé pour {city}.", True

    return f"⚠️ Risques à {city} :\n" + "\n".join(f"• {risk}" for risk in risks), True
