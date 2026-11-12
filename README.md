# 📡 Meshtastic Search Bot

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

A lightweight **Meshtastic Internet assistant**. Nodes on a Meshtastic network can ask questions, look up places, and receive short answers tailored for LoRa radio constraints.

The bot listens on a dedicated channel and offers three data sources:

* 🔎 **Web search**: an LLM builds an optimized query, [SearXNG](https://github.com/searxng/searxng) searches the web, and the LLM summarizes the results.
* 🗺️ **OpenStreetMap**: name, address and GPS position of a place, through Nominatim, prioritizing results close to the requesting node when its GPS position is known.
* 🚑 **First aid**: the bot can suggest a relevant emergency case from a dataset published by [Avant les secours / Odersa](https://avantlessecours.odersa.org/), then return the associated steps in a numbered list.

For the internal design, algorithms and technologies, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

# ✨ Features

* 📡 Listens to a dedicated Meshtastic channel
* 💬 Simple commands: `/help`, `/osm`, `/georisque`, `/gps`, `/hamrelay`, `/search`, `/emergency`, `/github`
* 🔎 Web search through a self-hostable SearXNG instance
* 🤖 LLM for query generation, place-name extraction and answer synthesis, with automatic fallback (Vireonix first, local Ollama otherwise)
* 🗺️ Structured place info from OpenStreetMap (name, address, GPS, phone, opening hours)
* 🚑 Emergency guidance from the local "Avant les secours" dataset, matching the closest first-aid case to a user request
* ⚠️ Commune-level risk information from the French Géorisques API
* 🟢 `/osm` prefers places that are currently open (from the OSM `opening_hours` tag, in the `TZ_NAME` time zone); places without opening hours are kept, and if every match is known to be closed the closest one is returned and flagged `(fermé)`
* 📍 Distance-aware `/osm` search: uses the sender's GPS position (when known) and expands the search radius (1 km → 5 km → 20 km) until a match is found, keeping the closest result
* 🧭 `/gps` returns the sender's coordinates and a nearby address (reverse geocoding via Nominatim)
* 🏙️ Configurable local city added to searches
* 🕐 Local date and time available in prompts
* ✂️ Answers limited to 180 characters
* ↩️ Replies are linked to the original message (`replyId`) when the library supports it
* 🔄 Automatic reconnection after a connection loss
* 🐳 Fully Docker Compose based

---

# 💬 Commands

| Command | Description | Example |
| --- | --- | --- |
| `/help` | 📖 Lists the commands and the configured city | `/help` |
| `/osm [place]` | 🗺️ OpenStreetMap info: name, address, GPS | `/osm Moby's café` |
| `/georisque` | ⚠️ Lists commune risks with status `Risque Existant` or `Risque Existant - modéré` (cached 7 days in memory, configurable via `GEORISQUES_CACHE_TTL` in seconds) | `/georisque` |
| `/gps` | 🧭 Your GPS coordinates (`Long` / `Lat`) and the nearest address (reverse geocoding) | `/gps` |
| `/hamrelay` | 📻 Amateur radio repeaters (F5ZFF Mont-Saint-Aignan, F5ZMK Deville-les-Rouen; static text, hard-coded in `bot.py`) | `/hamrelay` |
| `/translate` | 🌍 Translates a text between two languages | `/translate fr en bonjour` |
| `/search [question]` | 🔎 Web search summarized by the LLM | `/search latest Raspberry Pi model` |
| `/emergency [situation]` | 🚑 Finds the closest emergency case and returns its numbered steps (first aid) | `/emergency saignement abondant` |
| `/github` | 🐙 Link to the repository | `/github` |
| *any other text* | 🔎 Handled like `/search` | `weather in Rouen today?` |

An unknown command returns `❓ Commande inconnue. Tape /help`.

## Example: `/osm`

```text
/osm Moby's café
```

```text
📍 Moby's café
🏠 38, Boulevard de l'Yser, 76000
🧭 49.44860, 1.09928
📞 +33 2 32 10 66 56
```

The `🕒` (opening hours) and `📞` (phone) lines only appear when the data exists in OpenStreetMap.

## Example: `/gps`

```text
/gps
```

```text
Long : 1.09930
Lat : 49.44320
🏠 2 Place du Général de Gaulle, 76000 Rouen
```

Coordinates are rounded to 5 decimals (about 1 m). The `🏠` line is omitted if the reverse geocoding fails. If the node's position is unknown, the bot replies `Bot cannot get your GPS coordonate`.

## Example: `/search`

```text
/search latest Raspberry Pi 5 model
```

```text
Le Raspberry Pi 5 existe notamment en versions 2, 4, 8 et 16 Go de RAM.
```

## Example: `/emergency`

```text
/emergency saignement abondant
```

```text
1. Comprimer directement la plaie
2. Se protéger les mains
3. Allonger la victime
4. Alerter sans lâcher
5. Ne jamais relâcher la compression
```

The emergency module compares the user request to a local index of cases and returns the closest match. The dataset is downloaded once at startup by `emergency/download_aid.py` from `https://avantlessecours.odersa.org/` and stored under `emergency/first-aid/`.

---

# 🚀 Installation Guide

## Requirements

* Docker and Docker Compose
* A Meshtastic node reachable over TCP (usually port `4403`)
* A running SearXNG instance with JSON output enabled
* Docker Compose starts Ollama and downloads the configured fallback model
* A dedicated Meshtastic channel for the bot
* Internet access to Nominatim (`nominatim.openstreetmap.org`) for `/osm` and `/gps`
* Internet access to Géorisques (`georisques.gouv.fr`) for `/georisque`
* Optional: internet access to Vireonix (`vireonix.ai`) as the preferred LLM backend

## 1. Clone the repository

```bash
git clone https://github.com/YR72dpi/meshtastic_search_bot.git
cd meshtastic_search_bot
```

## 2. Configure environment variables

```bash
cp .env.example .env
```

Example `.env`:

```dotenv
MESHTASTIC_HOST=192.168.1.161
MESHTASTIC_PORT=4403

CHANNEL_INDEX=2
CHANNEL_NAME=search

SEARXNG_URL=http://core:8080/search

# First choice: Vireonix if available, otherwise fallback to Ollama
VIREONIX_URL=https://vireonix.ai/v1/chat/completions
VIREONIX_API_KEY=
VIREONIX_MODEL=auto
VIREONIX_TIMEOUT=180

OLLAMA_URL=http://ollama:11434/api/chat
OLLAMA_MODEL=qwen3:1.7b
OLLAMA_TIMEOUT=180

CITY=Rouen, France
TZ_NAME=Europe/Paris
GITHUB_URL=https://github.com/YR72dpi/meshtastic_search_bot

RECONNECT_DELAY_SECONDS=10
```

### Environment variables

| Variable | Description | Default / example |
| --- | --- | --- |
| `MESHTASTIC_HOST` | Meshtastic TCP host | `192.168.1.161` |
| `MESHTASTIC_PORT` | Meshtastic TCP port | `4403` |
| `CHANNEL_INDEX` | Channel index monitored by the bot (**required**) | `2` |
| `CHANNEL_NAME` | Human-readable channel name (logs only) | `search` |
| `SEARXNG_URL` | SearXNG search endpoint | `http://core:8080/search` |
| `VIREONIX_URL` | Vireonix API endpoint used as the preferred LLM backend | `https://vireonix.ai/v1/chat/completions` |
| `VIREONIX_API_KEY` | API key for Vireonix (optional for the public API) | empty |
| `VIREONIX_MODEL` | Model name for Vireonix | `auto` |
| `VIREONIX_TIMEOUT` | Vireonix request timeout in seconds | `180` |
| `OLLAMA_URL` | Ollama chat API endpoint (fallback) | `http://ollama:11434/api/chat` |
| `OLLAMA_MODEL` | Model used for fallback LLM requests | `qwen3:1.7b` |
| `OLLAMA_TIMEOUT` | Ollama request timeout in seconds | `180` |
| `CITY` | Local city added to searches and OSM lookups | `Paris, France` |
| `TZ_NAME` | Time zone used for date and time in prompts | `Europe/Paris` |
| `GITHUB_URL` | Link returned by `/github` | repository URL |
| `RECONNECT_DELAY_SECONDS` | Delay before reconnecting | `10` |
| `SEND_DELAY_SECONDS` | Pause between the parts of a split answer | `5` |

> **Important:** `CHANNEL_INDEX` must match the real Meshtastic channel index. The bot replies on the channel the message was received on.
>
> **LLM fallback:** the router in [`tool/llm.py`](tool/llm.py) tries Vireonix first and automatically falls back to Ollama when Vireonix is unavailable, returns an error after its retries, or returns an empty result. See [ARCHITECTURE.md](ARCHITECTURE.md#3-la-couche-llm).

## 3. Configure SearXNG

The bot expects SearXNG to return **JSON**. In `core-config/settings.yml`:

```yaml
search:
  formats:
    - html
    - json
```

The bot then calls:

```text
GET /search?q=<query>&format=json
```

If SearXNG and the bot share a Docker Compose project, no host port is needed:

```dotenv
SEARXNG_URL=http://core:8080/search
```

`core` is the Compose service name.

## 4. Start the bot

```bash
docker compose up -d          # start
docker compose logs -f        # follow logs
docker compose down           # stop
```

After any change to the Python code or the prompts, rebuild:

```bash
docker compose up -d --build
```

## 5. Troubleshooting

### `ModuleNotFoundError: No module named 'tool'`

The container runs an outdated image, or the folder is missing from it. Check the Dockerfile copies `tool/` and rebuild:

```bash
docker compose build --no-cache && docker compose up
```

Also check `.dockerignore` and any `volumes:` entry that mounts over `/app`.

### `FileNotFoundError` on a prompt

Prompts are read from `/app/prompt`. Check the Dockerfile has `COPY prompt/ ./prompt` and that the file exists:

```bash
docker compose run --rm --entrypoint sh <service> -c "ls -la /app/prompt"
```

### `ZoneInfoNotFoundError`

The slim image may lack time zone data. Add `tzdata` to `requirements.txt` and rebuild.

### SearXNG returns no results

Check that JSON output is enabled (see [SearXNG](#3-configure-searxng)) and test the endpoint from inside the Docker network.

### The bot receives messages but ignores them

Compare `CHANNEL_INDEX` with the channel shown in the logs:

```text
[RX] channel=2 question=...
```

### `/osm` says the place was not found

Try a more precise name, or use `/search`. Nominatim only knows what is mapped in OpenStreetMap.

### Meshtastic connection fails

```bash
nc -zv <MESHTASTIC_HOST> 4403
```

### Vireonix returns `502` or `429`

This is expected occasionally. The bot retries Vireonix once more on `429` and `5xx`, then switches to Ollama. Check the `[LLM]` lines in the logs to see which provider answered.

---

# ⚠️ Limits and Warnings

## TCP connection

As things stand, because of the TCP connection, the node will not be accessible from a client application.

You have to stop the docker service to get the connection back.

## Message size

A Meshtastic text message is limited to roughly **230 bytes**, and each emoji counts for about 4 bytes. Answers are capped at 200 characters, so keep `/osm` output short.

## Nominatim usage policy

Please respect the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/):

* Send an identifiable `User-Agent` (for example `meshtastic-search-bot/1.0 (you@example.com)`).
* Do not exceed one request per second. The bot waits 1 second between radius attempts.

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL 1.0.

## LLM fallback

* Vireonix is a third-party public service: its availability and rate limits are outside this project's control.
* When Vireonix is used, prompts (including the user's question and the search results) are sent to `vireonix.ai`.
* The Ollama fallback runs locally, but its answer quality depends on the small configured model (`qwen3:1.7b` by default).
* The retry delays are short. A long Vireonix outage causes a slower reply before Ollama answers.

## Privacy

The search side can be fully self-hosted:

```text
Meshtastic → Your bot → Your SearXNG → Search engines
```

The bot uses no database and no user accounts. Note that `/gps` sends the sender's coordinates and `/osm` sends the place name and city to the public Nominatim service, and `/georisque` sends the configured city to the public Géorisques API.

## First-aid data

The `/emergency` command is a convenience tool, not a substitute for emergency services. Always call the local emergency number in a real emergency.

---

# 📝 Logging

Each stage of the pipeline is logged:

```text
[RX] channel=2 question=/osm Moby's café
[SEARCH] Question de !abcdef: /osm Moby's café
[BOT] Appel : answer_question
[BOT] Appel : osm_lookup
[BOT] Appel : extract_place_name
[BOT] Appel : search_place_data
[TX] Réponse envoyée sur channel=2 (search) en réponse à l'id 123456
```

---

# 📜 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

See the [LICENSE](LICENSE) file for the full license text. In short, GPLv3 lets you use,
study, modify and redistribute this software, provided that any distributed derivative
work is also released under the GPLv3 and keeps its source code available.

---

## 🤝 Contributing

Contributions are welcome. Please open an issue or a pull request on [GitHub](https://github.com/YR72dpi/meshtastic_search_bot).
