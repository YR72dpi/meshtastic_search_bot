import re
from pathlib import Path
from zoneinfo import ZoneInfo
import os
from datetime import datetime

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompt"
TIMEZONE = ZoneInfo(os.getenv("TZ_NAME", "Europe/Paris"))
MAX_MESSAGE_LENGTH = 180

_PLACEHOLDER = re.compile(r"\[(\w+)\]")
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def parse_command(text: str) -> tuple[str, str]:
    print("[BOT] Appel : parse_command", flush=True)
    """'/osm café Moby' -> ('/osm', 'café Moby'). Sans commande -> ('', text)."""
    text = text.strip()
    if not text.startswith("/"):
        return "", text
    command, _, args = text.partition(" ")
    return command.lower(), args.strip()


def split_message(message: str) -> list[str]:
    """Découpe un message en morceaux sans couper les mots si possible."""
    print("[BOT] Appel : split_message", flush=True)

    if not message:
        return []

    parts = []
    remaining = message

    while remaining:
        if len(remaining.encode("utf-8")) <= MAX_MESSAGE_LENGTH:
            parts.append(remaining)
            break

        candidate = remaining[:MAX_MESSAGE_LENGTH]
        newline_index = candidate.rfind("\n")
        if newline_index > 0:
            boundary = newline_index + 1
        else:
            space_index = candidate.rfind(" ")
            if space_index > 0:
                boundary = space_index + 1
            else:
                boundary = MAX_MESSAGE_LENGTH

        chunk = remaining[:boundary].rstrip()
        if not chunk:
            chunk = remaining[:MAX_MESSAGE_LENGTH].rstrip()
            boundary = MAX_MESSAGE_LENGTH

        while len(chunk.encode("utf-8")) > MAX_MESSAGE_LENGTH and " " in chunk:
            space_index = chunk.rfind(" ")
            if space_index <= 0:
                break
            chunk = chunk[:space_index].rstrip()
            boundary = len(chunk)

        if not chunk:
            chunk = remaining[:MAX_MESSAGE_LENGTH].rstrip()
            boundary = MAX_MESSAGE_LENGTH

        parts.append(chunk)
        remaining = remaining[boundary:].lstrip()

    return parts

def excerpt_ending_with_period(text: str) -> str:
    print(f"[BOT] Appel : excerpt_ending_with_period")

    excerpt = text[:200]
    last_dot = excerpt.rfind(".")
    if last_dot != -1:
        excerpt = excerpt[:last_dot + 1]
    return excerpt

def time_variables() -> dict:
    print(f"[BOT] Appel : time_variables")
    now = datetime.now(TIMEZONE)
    return {
        "day": JOURS[now.weekday()],
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M"),
    }


def load_prompt(name: str, **values) -> str:
    print(f"[BOT] Appel : load_prompt")

    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    variables = {
        "city": os.getenv("CITY", "Paris"), 
        **time_variables(), 
        **values
    }

    def replace(match):
        key = match.group(1)
        if key not in variables:
            print(f"[PROMPT] Variable inconnue dans {name}: {{{{{key}}}}}", flush=True)
            return match.group(0)
        return str(variables[key])

    return _PLACEHOLDER.sub(replace, text).strip()