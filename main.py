import threading
import time
from pubsub import pub
from meshtastic.tcp_interface import TCPInterface
import os
from bot import answer_question

MESHTASTIC_HOST = os.getenv("MESHTASTIC_HOST")
MESHTASTIC_PORT = int(os.getenv("MESHTASTIC_PORT", "4403"))
SEARCH_CHANNEL_INDEX = int(os.getenv("CHANNEL_INDEX"))
SEARCH_CHANNEL_NAME = os.getenv("CHANNEL_NAME")
CITY = os.getenv("CITY", "Paris, France")

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
        # ID du message auquel on répond
        original_packet_id = packet.get("id")

        print(
            f"[SEARCH] Question de {sender}: {question}",
            flush=True
        )

        answer = answer_question(question)

        try:
            interface.sendText(
                answer,
                channelIndex=received_channel,
                replyId=original_packet_id
            )
        except TypeError:
            # Ancienne version de la lib sans replyId : envoi classique
            print("[TX] replyId non supporté, envoi sans réponse liée", flush=True)
            interface.sendText(
                answer,
                channelIndex=received_channel
            )

        print(
            f"[TX] Réponse envoyée sur "
            f"channel={received_channel} ({SEARCH_CHANNEL_NAME}) "
            f"en réponse à l'id {original_packet_id}",
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
        f"[{SEARCH_CHANNEL_INDEX}] {SEARCH_CHANNEL_NAME}\n"
        f"[CONFIG] Ville : {CITY}",
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
