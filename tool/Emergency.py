import json
from pathlib import Path


CAS_INDEX_PATH = (
    Path(__file__).resolve().parent.parent
    / "emergency"
    / "first-aid"
    / "cas.json"
)


def get_all_case() -> str:
    """Retourne le numéro et le nom de chaque cas sous forme de texte."""
    with CAS_INDEX_PATH.open(encoding="utf-8") as cas_file:
        index = json.load(cas_file)

    return "\n".join(
        f"{cas['numero']} - {cas['titre']}"
        for niveau in index["niveaux"]
        for cas in niveau["cas"]
    )


def get_cas_gestes(numero: int) -> str:
    """Retourne les gestes du cas demandé, un geste par ligne."""
    cas_path = CAS_INDEX_PATH.parent / f"{numero}.json"
    with cas_path.open(encoding="utf-8") as cas_file:
        cas = json.load(cas_file)

    return "\n".join(cas["gestes"])
