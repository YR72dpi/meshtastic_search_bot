import os
import threading
import time
import requests

from pubsub import pub
from meshtastic.tcp_interface import TCPInterface

from vireonix import call_vireonix


MESHTASTIC_HOST = os.getenv("MESHTASTIC_HOST")
MESHTASTIC_PORT = int(os.getenv("MESHTASTIC_PORT", "4403"))

SEARCH_CHANNEL_INDEX = int(os.getenv("CHANNEL_INDEX"))
SEARCH_CHANNEL_NAME = os.getenv("CHANNEL_NAME")

SEARXNG_URL = os.getenv("SEARXNG_URL")
LOCAL_CONTEXT = os.getenv("LOCAL_CONTEXT", "")

MAX_RESPONSE_LENGTH = 200
SEARCH_RESULTS_LIMIT = 3

def answer_question(question: str) -> str:
    """Pipeline complet : question -> requête de recherche -> résultats -> réponse."""

    print(f"[BOT] Appel : answer_question")

    search_query = build_search_query(question)
    context = search_searxng(search_query)
    return generate_answer(question, context)

def search_searxng(query: str) -> str:
    """Interroge SearXNG et renvoie le contenu concaténé des 3 meilleurs résultats."""

    print(f"[BOT] Appel : search_searxng")

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
        print(f"[SEARXNG] {"".join(contents)}",flush=True)
        return "\n\n".join(contents)
    except Exception as e:
        print(f"[SEARXNG] Erreur: {e}", flush=True)
        return ""

def build_search_query(question: str) -> str:
    """Demande au LLM de reformuler la question en requête de recherche web.

    Si le LLM ne répond pas, on retombe sur la question brute + le contexte local.
    """

    print(f"[BOT] Appel : build_search_query")

    prompt = f"""Formule une requête de recherche web courte et efficace permettant \
de trouver des informations pour répondre à la question suivante.

Règles :
- Réponds uniquement avec la requête de recherche, sans explication.
- Intègre le contexte local si pertinent.

Contexte local : {LOCAL_CONTEXT}

Question : {question}
"""
    try:
        result = call_vireonix(prompt)
        return result
    except Exception as e:
        print(f"[VIREONIX] Erreur formulation requête: {e}", flush=True)
        return f"{question} {LOCAL_CONTEXT}".strip()

def generate_answer(question: str, context: str) -> str:
    """Demande au LLM de répondre à la question à partir du contexte de recherche.

    Si le LLM ne répond pas, on renvoie un extrait du contexte à la place.
    """

    print(f"[BOT] Appel : generate_answer")

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
        return call_vireonix(prompt)[:MAX_RESPONSE_LENGTH]
    except Exception as e:
        print(f"[VIREONIX] Erreur: {e}", flush=True)
        return f"LLM inaccéssible {excerpt_ending_with_period(context)}"

def excerpt_ending_with_period(text: str, max_length: int = 200) -> str:
    """Tronque `text` à `max_length` caractères, en coupant au dernier point trouvé."""

    print(f"[BOT] Appel : excerpt_ending_with_period")

    excerpt = text[:max_length]
    last_dot = excerpt.rfind(".")
    if last_dot != -1:
        excerpt = excerpt[:last_dot + 1]
    return excerpt

def on_receive(packet, interface):

    print(f"[BOT] Appel : on_receive")
    
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
        answer = answer_question(question)
        
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

    print(f"[BOT] Appel : on_connection")

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

connection_lost = threading.Event()

def on_connection_lost(interface, topic=pub.AUTO_TOPIC):
    print("[MESHTASTIC] Connexion perdue.", flush=True)
    connection_lost.set()

pub.subscribe(
    on_receive,
    "meshtastic.receive.text"
)
pub.subscribe(
    on_connection,
    "meshtastic.connection.established"
)
pub.subscribe(
    on_connection_lost,
    "meshtastic.connection.lost"
)

RECONNECT_DELAY_SECONDS = int(os.getenv("RECONNECT_DELAY_SECONDS", "10"))

def connect() -> TCPInterface:
    print(
        f"Connexion à {MESHTASTIC_HOST}:{MESHTASTIC_PORT}...",
        flush=True
    )
    connection_lost.clear()
    interface = TCPInterface(
        hostname=MESHTASTIC_HOST,
        portNumber=MESHTASTIC_PORT
    )
    print(
        f"Bot démarré — écoute de "
        f"[{SEARCH_CHANNEL_INDEX}] {SEARCH_CHANNEL_NAME}",
        flush=True
    )
    return interface

interface = connect()

try:
    while True:
        try:
            time.sleep(5)
            # L'interface meshtastic ferme son thread de lecture en cas
            # d'erreur réseau (pipe cassé, reset...) sans lever ici :
            # on détecte donc la déconnexion via le callback pubsub.
            if connection_lost.is_set():
                raise ConnectionError("Connexion meshtastic perdue")
        except Exception as e:
            print(
                f"[MESHTASTIC] Connexion perdue ({e}), "
                f"reconnexion dans {RECONNECT_DELAY_SECONDS}s...",
                flush=True
            )
            try:
                interface.close()
            except Exception:
                pass
            time.sleep(RECONNECT_DELAY_SECONDS)
            try:
                interface = connect()
            except Exception as reconnect_error:
                print(
                    f"[MESHTASTIC] Échec de reconnexion: {reconnect_error}",
                    flush=True
                )

except KeyboardInterrupt:
    print("Arrêt du bot.", flush=True)
    interface.close()
