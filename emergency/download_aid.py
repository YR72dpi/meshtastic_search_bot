
import requests
import json
from pathlib import Path
from urllib.parse import urljoin

BASE_URL = "https://avantlessecours.odersa.org/"
INDEX_URL = urljoin(BASE_URL, "data/fr/cas.json")

OUTPUT_DIR = Path(__file__).resolve().parent / "first-aid"

session = requests.Session()
session.headers.update({
    "User-Agent": "FirstAidDataDownloader/1.0"
})


def download_json(url, destination):
    response = session.get(url, timeout=20)
    response.raise_for_status()

    # Vérification du JSON
    content = response.json()

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(content, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[OK] {destination}")
    return content


def main():
    # Téléchargement de l'index
    index_path = OUTPUT_DIR / "cas.json"
    data = download_json(INDEX_URL, index_path)

    downloaded = 0
    errors = 0

    # Parcours de tous les niveaux et cas
    for niveau in data.get("niveaux", []):
        for cas in niveau.get("cas", []):

            relative_path = cas.get("donnees")
            numero = cas.get("numero")

            if not relative_path:
                continue

            url = urljoin(BASE_URL, relative_path)
            destination = OUTPUT_DIR / f"{numero}.json"

            try:
                download_json(url, destination)
                downloaded += 1

            except (requests.RequestException, ValueError) as error:
                print(f"[ERREUR] {url}: {error}")
                errors += 1

    print("\n--- Bilan ---")
    print(f"Fichiers téléchargés : {downloaded + 1}")
    print(f"Erreurs : {errors}")
    print(f"Dossier : {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
