import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

FIRST_AID_DIR = Path(__file__).resolve().parent.parent / "emergency" / "first-aid"
INDEX_PATH = FIRST_AID_DIR / "cas.json"

MIN_WORD_LENGTH = 4
# Racinisation par préfixe : "etouffe" et "etouffement" -> "etouff"
STEM_LENGTH = 6
# Champs des fichiers de cas indexés : les plus porteurs de sens
INDEXED_FIELDS = ("titre", "titreCourt", "requetes", "gestes")

_WORD = re.compile(r"\w+")


# ---------------------------------------------------------------------------
# Lecture des fichiers de cas
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _case_numbers() -> list[int]:
    index = _load_json(INDEX_PATH)
    return [cas["numero"] for niveau in index["niveaux"] for cas in niveau["cas"]]


def _case_text(case: dict) -> str:
    """Texte indexé d'un cas : concaténation des champs INDEXED_FIELDS."""
    parts = []
    for field in INDEXED_FIELDS:
        value = case.get(field, "")
        parts.extend(value if isinstance(value, list) else [value])
    return " ".join(parts)


# ---------------------------------------------------------------------------
# TF-IDF
# ---------------------------------------------------------------------------

def tokenize(text: str) -> list[str]:
    """Mots en minuscules, sans accents, de plus de deux caractères, racinisés."""
    normalized = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(c for c in normalized if not unicodedata.combining(c))
    return [w[:STEM_LENGTH] for w in _WORD.findall(ascii_text) if len(w) >= MIN_WORD_LENGTH]


def _term_frequency(words: list[str]) -> dict[str, float]:
    counts = Counter(words)
    total = len(words) or 1
    return {word: count / total for word, count in counts.items()}


def _norm(vector: dict[str, float]) -> float:
    return math.sqrt(sum(value * value for value in vector.values()))


@lru_cache(maxsize=1)
def _build_index() -> tuple[dict[int, dict[str, float]], dict[str, float]]:
    """Retourne (vecteurs TF-IDF par cas, IDF par mot)."""
    print("[EMERGENCY] Construction de l'index TF-IDF", flush=True)

    documents = {
        numero: tokenize(_case_text(_load_json(FIRST_AID_DIR / f"{numero}.json")))
        for numero in _case_numbers()
    }

    doc_count = len(documents)
    doc_freq = Counter(word for words in documents.values() for word in set(words))
    idf = {
        word: math.log((1 + doc_count) / (1 + freq)) + 1
        for word, freq in doc_freq.items()
    }

    vectors = {
        numero: {w: tf * idf[w] for w, tf in _term_frequency(words).items()}
        for numero, words in documents.items()
    }
    return vectors, idf


def find_case(query: str) -> int | None:
    """Numéro du cas le plus proche de la requête (similarité cosinus), ou None."""
    vectors, idf = _build_index()

    words = [w for w in tokenize(query) if w in idf]
    if not words:
        return None
    query_vector = {w: tf * idf[w] for w, tf in _term_frequency(words).items()}
    query_norm = _norm(query_vector)

    best_case, best_score = None, 0.0
    for numero, vector in vectors.items():
        dot = sum(weight * vector.get(word, 0.0) for word, weight in query_vector.items())
        score = dot / (query_norm * _norm(vector)) if dot else 0.0
        if score > best_score:
            best_case, best_score = numero, score

    print(f"[EMERGENCY] Cas {best_case} (score {best_score:.3f})", flush=True)
    return best_case


# ---------------------------------------------------------------------------
# Réponse
# ---------------------------------------------------------------------------

def get_cas_gestes(numero: int) -> str:
    """Retourne les gestes du cas demandé, un geste par ligne."""
    return "\n".join(_load_json(FIRST_AID_DIR / f"{numero}.json")["gestes"])
