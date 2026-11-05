import json
from pathlib import Path


CAS_INDEX_PATH = (
    Path(__file__).resolve().parent.parent
    / "emergency"
    / "first-aid"
    / "cas.json"
)


def get_all_case() -> str:
    print("[BOT] Appel : get_all_case", flush=True)
    """Retourne le numéro, le nom et les requêtes de chaque cas sous forme de texte."""
    with CAS_INDEX_PATH.open(encoding="utf-8") as cas_file:
        index = json.load(cas_file)

    lines = []
    for niveau in index["niveaux"]:
        for cas in niveau["cas"]:
            detail_path = CAS_INDEX_PATH.parent / f"{cas['numero']}.json"
            with detail_path.open(encoding="utf-8") as detail_file:
                requetes = json.load(detail_file).get("requetes", [])
            lines.append(
                f"{cas['numero']} - {cas['titre']} - requetes : {' | '.join(requetes)}"
            )
    return "\n".join(lines)


def get_cas_gestes(numero: int) -> str:
    print("[BOT] Appel : get_cas_gestes", flush=True)
    """Retourne les gestes du cas demandé, un geste par ligne."""
    cas_path = CAS_INDEX_PATH.parent / f"{numero}.json"
    with cas_path.open(encoding="utf-8") as cas_file:
        cas = json.load(cas_file)

    return "\n".join(cas["gestes"])
