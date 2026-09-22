import os
import time
import requests

from pubsub import pub
from meshtastic.tcp_interface import TCPInterface


MESHTASTIC_HOST = os.getenv("MESHTASTIC_HOST")
MESHTASTIC_PORT = int(os.getenv("MESHTASTIC_PORT", "4403"))

SEARCH_CHANNEL_INDEX = int(os.getenv("CHANNEL_INDEX"))
SEARCH_CHANNEL_NAME = os.getenv("CHANNEL_NAME")

VIREONIX_URL = os.getenv(
    "VIREONIX_URL",
    "https://vireonix.ai/v1/chat/completions"
)

SEARXNG_URL = os.getenv("SEARXNG_URL")

MAX_RESPONSE_LENGTH = 200
SEARCH_RESULTS_LIMIT = 3


def search_searxng(query: str) -> str:
    """Interroge SearXNG et renvoie le contenu concaténé des 3 meilleurs résultats."""
    try:
        response = requests.get(
            SEARXNG_URL,
            params={
                "q": query,
                "format": "json"
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        # Tri par score décroissant (SearXNG renvoie déjà souvent ce tri).
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        contents = [
            r["content"]
            for r in results[:SEARCH_RESULTS_LIMIT]
            if r.get("content")
        ]
        print(f"[SEARXNG] {contents}",flush=True)
        return "\n\n".join(contents)
    except Exception as e:
        print(f"[SEARXNG] Erreur: {e}", flush=True)
        return ""


def ask_vireonix(question: str) -> str:
    context = search_searxng(question)
    context_block = (
        f"Contexte (résultats de recherche) :\n{context}\n\n"
        if context
        else ""
    )
    prompt = f"""Réponds en français à la question suivante.

Règles :
- Réponds directement à la question.
- Sois précis et concis.
- Maximum 150 caractères.
- N'invente aucune information.
- Utilise le contexte fourni si présent si besoins.

{context_block}

Question : {question}
"""
    
    try:
        response = requests.post(
            VIREONIX_URL,
            headers={
                "Content-Type": "application/json"
            },
            json={
                "model": "auto",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()
        return answer[:MAX_RESPONSE_LENGTH]

    except Exception as e:
        print(f"[VIREONIX] Erreur: {e}", flush=True)
        return "Erreur lors de la requête LLM."


def on_receive(packet, interface):
    try:
        decoded = packet.get("decoded", {})
        # Seulement les messages texte
        if decoded.get("portnum") != "TEXT_MESSAGE_APP":
            return
        question = decoded.get("text")
        if not question:
            return
        # IMPORTANT :
        # On récupère le vrai channel du paquet reçu.
        received_channel = packet.get("channel", 0)
        print(
            f"[RX] channel={received_channel} "
            f"question={question}",
            flush=True
        )
        # On ne répond QUE sur le channel 2 / search
        if received_channel != SEARCH_CHANNEL_INDEX:
            print(
                f"[RX] Ignoré : channel {received_channel} "
                f"(attendu {SEARCH_CHANNEL_INDEX})",
                flush=True
            )
            return
        sender = packet.get("fromId", "unknown")
        print(
            f"[SEARCH] Question de {sender}: {question}",
            flush=True
        )
        # Appel LLM
        answer = ask_vireonix(question)
        print(
            f"[LLM] {answer}",
            flush=True
        )
        # BROADCAST :
        # aucune destinationId => broadcast
        # channelIndex = channel réellement reçu
        interface.sendText(
            answer,
            channelIndex=received_channel
        )
        print(
            f"[TX] Réponse envoyée sur "
            f"channel={received_channel} ({SEARCH_CHANNEL_NAME})",
            flush=True
        )
    except Exception as e:
        print(f"[BOT] Erreur: {e}", flush=True)


def on_connection(interface, topic=pub.AUTO_TOPIC):
    print(
        f"[MESHTASTIC] Connecté à "
        f"{MESHTASTIC_HOST}:{MESHTASTIC_PORT}",
        flush=True
    )

    print("[MESHTASTIC] Channels locaux :", flush=True)
    try:
        for index, channel in enumerate(interface.localNode.channels):
            print(
                f"  [{index}] {channel.settings.name}",
                flush=True
            )
    except Exception as e:
        print(
            f"[MESHTASTIC] Impossible de lire les channels: {e}",
            flush=True
        )

pub.subscribe(
    on_receive,
    "meshtastic.receive.text"
)
pub.subscribe(
    on_connection,
    "meshtastic.connection.established"
)

print(
    f"Connexion à {MESHTASTIC_HOST}:{MESHTASTIC_PORT}...",
    flush=True
)

interface = TCPInterface(
    hostname=MESHTASTIC_HOST,
    portNumber=MESHTASTIC_PORT
)

print(
    f"Bot démarré — écoute de "
    f"[{SEARCH_CHANNEL_INDEX}] {SEARCH_CHANNEL_NAME}",
    flush=True
)

try:
    while True:
        time.sleep(60)

except KeyboardInterrupt:
    print("Arrêt du bot.", flush=True)
    interface.close()
