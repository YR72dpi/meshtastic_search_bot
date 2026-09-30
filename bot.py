import os

from tool.vireonix import call_vireonix
from tool.searXng import search_searxng
from tool.OpenStreetMap import search_place_data
from tool.utils import load_prompt, excerpt_ending_with_period, MAX_RESPONSE_LENGTH

CITY = os.getenv("CITY", "Paris, France")

# ---------------------------------------------------------------------------
# Étapes LLM (Vireonix)
# ---------------------------------------------------------------------------

def extract_place_name(search_result: str) -> str:
    """Extrait le nom propre du lieu à partir d'un résultat de recherche."""
    print("[BOT] Appel : extract_place_name", flush=True)

    prompt = load_prompt("extract_place_name", question=search_result)
    try:
        name = call_vireonix(prompt).strip().strip('"')
        return "" if name.upper() == "NONE" else name
    except Exception as e:
        print(f"[OSM] Erreur extraction du lieu: {e}", flush=True)
        return ""


def build_search_query(question: str) -> str:
    """Reformule la question en requête de recherche optimisée pour SearXNG."""
    print("[BOT] Appel : build_search_query", flush=True)

    prompt = load_prompt("generate_search_query_for_searXng", question=question)
    try:
        query = call_vireonix(prompt).strip()
        print(f"[BOT] Requête reformulée : {query}", flush=True)
        return query or question.strip()
    except Exception as e:
        print(f"[VIREONIX] Erreur formulation requête: {e}", flush=True)
        return question.strip()


def generate_answer(question: str, context: str) -> str:
    """Synthétise une réponse courte à partir des résultats SearXNG."""
    print("[BOT] Appel : generate_answer", flush=True)

    prompt = load_prompt(
        "generate_answer_from_searnxg",
        question=question,
        context=context,
    )
    try:
        return call_vireonix(prompt)[:MAX_RESPONSE_LENGTH]
    except Exception as e:
        print(f"[VIREONIX] Erreur: {e}", flush=True)
        return f"LLM inaccessible. {excerpt_ending_with_period(context)}"


# ---------------------------------------------------------------------------
# /search : reformulation (LLM) -> SearXNG -> synthèse (LLM)
# ---------------------------------------------------------------------------

def basic_search(question: str) -> str:
    print("[BOT] Appel : basic_search", flush=True)

    search_query = build_search_query(question)
    search_result = search_searxng(search_query)
    return generate_answer(question, search_result)


# ---------------------------------------------------------------------------
# /osm : nom propre (SearXNG + LLM) -> OpenStreetMap -> message structuré
# ---------------------------------------------------------------------------

def format_address(osm: dict) -> str:
    """Adresse courte : préfère le détail 'address' s'il existe, sinon display_name."""
    details = osm.get("address")
    if isinstance(details, dict):
        street = " ".join(
            p for p in (details.get("house_number"), details.get("road")) if p
        )
        town = " ".join(
            p for p in (
                details.get("postcode"),
                details.get("city") or details.get("town") or details.get("village"),
            ) if p
        )
        short = ", ".join(p for p in (street, town) if p)
        if short:
            return short

    # display_name : "Nom, 38, Boulevard de l'Yser, Quartier, Ville, ..., 76000, France"
    parts = [p.strip() for p in osm.get("display_name", "").split(",")]
    if parts and parts[0] == osm.get("name"):
        parts = parts[1:]
    if not parts:
        return "Adresse inconnue"

    # numéro + rue si le premier morceau est un numéro
    street = ", ".join(parts[:2]) if parts[0][:1].isdigit() else parts[0]
    postcode = next((p for p in parts if p.isdigit() and len(p) == 5), "")
    return f"{street}, {postcode}".strip(", ") if postcode else street


def format_osm_message(osm: dict) -> str:
    """Message structuré : nom, adresse, position GPS (+ horaires/téléphone si dispo)."""
    name = osm.get("name") or "Lieu"
    lines = [
        f"📍 {name}",
        f"🏠 {format_address(osm)}",
        f"🧭 {float(osm['lat']):.5f}, {float(osm['lon']):.5f}",
    ]

    extra = osm.get("extratags") or {}
    if extra.get("opening_hours"):
        lines.append(f"🕒 {extra['opening_hours']}")
    if extra.get("phone"):
        lines.append(f"📞 {extra['phone']}")

    return "\n".join(lines)


def osm_lookup(place_name_user: str) -> str:
    print("[BOT] Appel : osm_lookup", flush=True)

    # 1. Trouver le vrai nom du lieu via SearXNG + LLM
    search_result = search_searxng(f"{place_name_user}, {CITY}")
    clean_place_name = extract_place_name(search_result)
    if not clean_place_name:
        print("[BOT] No clean_place_name, utilisation du nom saisi", flush=True)
        clean_place_name = place_name_user

    # 2. Interroger OpenStreetMap
    osm_data = search_place_data(f"{clean_place_name}, {CITY}")
    if isinstance(osm_data, list):
        osm_data = osm_data[0] if osm_data else None

    if not osm_data:
        print("[BOT] No osmData", flush=True)
        return f"❌ Lieu introuvable sur OSM : {clean_place_name}\nEssaie /search {place_name_user}"

    return format_osm_message(osm_data)


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------

def help_message() -> str:
    return (
        f"🏙️ Ville configurée : {CITY}\n\n"
        "🤖 Commandes :\n"
        "🗺️ /osm [lieu] : infos OpenStreetMap\n"
        "🔎 /search [question] : recherche web\n"
        "🐙 /github : lien du dépôt\n"
    )


def github_message() -> str:
    return f"🐙 YR72dpi/meshtastic_search_bot"


def parse_command(text: str) -> tuple[str, str]:
    """'/osm café Moby' -> ('/osm', 'café Moby'). Sans commande -> ('', text)."""
    text = text.strip()
    if not text.startswith("/"):
        return "", text
    command, _, args = text.partition(" ")
    return command.lower(), args.strip()


def answer_question(question: str) -> str:
    print("[BOT] Appel : answer_question", flush=True)

    command, args = parse_command(question)

    if command == "/help":
        return help_message()

    if command == "/github":
        return github_message()

    if command == "/osm":
        return osm_lookup(args) if args else "❌ Usage : /osm [lieu]"

    if command == "/search":
        return basic_search(args) if args else "❌ Usage : /search [question]"

    if command:
        return "❓ Commande inconnue. Tape /help"

    # Message sans commande : recherche web par défaut
    return basic_search(question)