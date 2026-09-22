import os
import time
import requests

from pubsub import pub
from meshtastic.tcp_interface import TCPInterface


MESHTASTIC_HOST = os.getenv("MESHTASTIC_HOST", "192.168.1.161")
MESHTASTIC_PORT = int(os.getenv("MESHTASTIC_PORT", "4403"))

SEARCH_CHANNEL_INDEX = 2
SEARCH_CHANNEL_NAME = "search"

VIREONIX_URL = "https://vireonix.ai/v1/chat/completions"

MAX_RESPONSE_LENGTH = 200


def ask_vireonix(question: str) -> str:
    prompt = f"""Réponds en français à la question suivante.

Règles :
- Réponds directement à la question.
- Sois précis et concis.
- Maximum 200 caractères.
- N'invente aucune information.

Question :
{question}
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
