import re
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import datetime

MAX_RESPONSE_LENGTH = 150
PROMPTS_DIR = "./prompt"
TIMEZONE = ZoneInfo(os.getenv("TZ_NAME", "Europe/Paris"))

_PLACEHOLDER = re.compile(r"\[(\w+)\]")
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

def excerpt_ending_with_period(text: str, max_length: int = MAX_RESPONSE_LENGTH) -> str:
    print(f"[BOT] Appel : excerpt_ending_with_period")

    excerpt = text[:max_length]
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

    text = (Path(PROMPTS_DIR) / f"{name}.md").read_text(encoding="utf-8")
    variables = {
        "city": os.getenv("CITY"), 
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