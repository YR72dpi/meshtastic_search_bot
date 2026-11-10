import os

CITY = os.getenv("CITY", "Paris, France")

COMMAND_HELP = {
    "help": {
        "title": "/help",
        "usage": "/help",
        "description": "Affiche l’aide générale",
    },
    "help_command": {
            "title": "/help [commande]",
            "usage": "/help [commande]",
            "description": "Affiche la documentation d’une commande spécifique.",
        },
    "gps": {
        "title": "/gps",
        "usage": "/gps",
        "description": "Renvoie les coordonnées GPS de l’expéditeur si elles sont disponibles.",
    },
    "georisque": {
        "title": "/georisque",
        "usage": "/georisque",
        "description": "Renvoie les risques géologiques de la zone locale.",
    },
    "geo": {
        "title": "/geo",
        "usage": "/geo",
        "description": "Alias de /georisque.",
    },
    "osm": {
        "title": "/osm",
        "usage": "/osm [lieu]",
        "description": "Cherche un lieu sur OpenStreetMap et renvoie son nom, son adresse et son GPS.",
    },
    "search": {
        "title": "/search",
        "usage": "/search [question]",
        "description": "Fait une recherche web puis résume la réponse avec le modèle LLM.",
    },
    "emergency": {
        "title": "/emergency",
        "usage": "/emergency [situation]",
        "description": "Cherche un cas de premiers secours correspondant à la situation donnée.",
    },
    "github": {
        "title": "/github",
        "usage": "/github",
        "description": "Affiche le dépôt GitHub du bot.",
    },
    "hamrelay": {
        "title": "/hamrelay",
        "usage": "/hamrelay",
        "description": "Affiche les fréquences relais HAM configurées.",
    },
    "ham": {
        "title": "/ham",
        "usage": "/ham",
        "description": "Alias de /hamrelay.",
    },
    "translate": {
        "title": "/translate",
        "usage": "/translate [langue_source] [langue_cible] [texte]",
        "description": "Traduit un texte entre deux langues. Exemple: /translate fr en bonjour.",
    },
}


def normalize_command(raw: str) -> str:
    if raw is None:
        return "help"
    text = raw.strip().lower().lstrip("/")
    aliases = {
        "georisque": "georisque",
        "hamrelay": "hamrelay",
        "github": "github",
        "gps": "gps",
        "osm": "osm",
        "search": "search",
        "emergency": "emergency",
        "help": "help",
        "translate": "translate",
    }
    return aliases.get(text, text)


def current_help(position=None) -> str:
    position_status = "detectee" if position else "inconnue"

    commandes = ' '.join([command["title"] for command in COMMAND_HELP.values()])

    return (
        f"{CITY}\n"
        f"Position {position_status}\n\n"
        f"Commandes :\n"
        f"{commandes}"
    )


def command_help(command: str) -> str:
    normalized = normalize_command(command or "")

    if normalized == "all":
        commands = "\n".join(
            f"{info['title']} — {info['usage']} — {info['description']}"
            for info in COMMAND_HELP.values()
        )
        return f"Commandes disponibles :\n{commands}"

    info = COMMAND_HELP.get(normalized)
    if not info:
        return (
            f"Commande inconnue : {command}\n"
            "Essaye /help ou /help all pour voir les commandes disponibles."
        )

    return (
        f"{info['title']}\n"
        f"Usage : {info['usage']}\n"
        f"Description : {info['description']}"
    )
