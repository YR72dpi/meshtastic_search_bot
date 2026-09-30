import os

from datetime import datetime
from tool.vireonix import call_vireonix
from tool.searXng import search_searxng
from tool.utils import *
from tool.OpenStreetMap import search_place_data

MESHTASTIC_HOST = os.getenv("MESHTASTIC_HOST")
MESHTASTIC_PORT = int(os.getenv("MESHTASTIC_PORT", "4403"))
SEARCH_CHANNEL_INDEX = int(os.getenv("CHANNEL_INDEX"))
SEARCH_CHANNEL_NAME = os.getenv("CHANNEL_NAME")
CITY = os.getenv("CITY", "Paris, France")

def extract_place_name(question: str) -> str:
    print(f"[BOT] Appel : extract_place_name")

    prompt = load_prompt("extract_place_name", question=question)
    
    try:
        name = call_vireonix(prompt).strip().strip('"')
        return "" if name.upper() == "NONE" else name
    except Exception as e:
        print(f"[OSM] Erreur extraction du lieu: {e}", flush=True)
        return ""

def build_search_query(question: str) -> str:
    print(f"[BOT] Appel : build_search_query")

    prompt = load_prompt("generate_search_query_for_searXng", question=question)

    try:
        result = call_vireonix(prompt)
        print(f"[BOT] Result : {result}", flush=True)
        return result
    except Exception as e:
        print(f"[VIREONIX] Erreur formulation requête: {e}", flush=True)
        return f"{question}".strip()

def generate_answer(question: str, context: str, dataSrc = "searxng") -> str:
    print("[BOT] Appel : generate_answer")

    if dataSrc != "osm" and dataSrc != "searxng" :
        dataSrc = "searxng"

    if dataSrc == "osm" :
        promptPattern = "generate_answer_from_osm_data"
    
    if dataSrc == "searxng":
        promptPattern = "generate_answer_from_searxng"
                                        
    prompt = load_prompt(
        promptPattern, 
        question=question,
        context=context
        )
    
    try:
        return call_vireonix(prompt)[:MAX_RESPONSE_LENGTH]
    except Exception as e:
        print(f"[VIREONIX] Erreur: {e}", flush=True)
        return f"LLM inaccéssible {excerpt_ending_with_period(context)}"

def basic_search(question: str) -> str:
    print("[BOT] Appel : basic_search")
    searchQuery = build_search_query(question)
    searchResult = search_searxng(searchQuery)
    answer = generate_answer(question, searchResult)
    return answer

def answer_question(question: str) -> str:
    print("[BOT] Appel : answer_question")

    if question == "/help":
        return f"""
/help : donne les commande disponible
/hours [lieu] : Donnée open street map
/location [lieu] : Donnée open street map
[Votre demande] : Données SearXNG
"""

    if question.startswith("/hours"):
        place_name_user = question.replace("/hours", "").strip()
        if not place_name_user:
            return "Command Error"
        search_place = search_searxng(place_name_user + ", " + CITY)
        clean_place_name = extract_place_name(search_place)

        if not clean_place_name:
            return basic_search("Horaire " + place_name_user + ", " + CITY)

        osmData = search_place_data(clean_place_name + ", " + CITY)

        if not osmData:
            return basic_search("Horaire " + clean_place_name + ", " + CITY)

        answer = generate_answer("Horaire " + clean_place_name, osmData, "osm")
        return answer

    if question.startswith("/location"):
        place_name_user = question.replace("/location", "").strip()
        if not place_name_user:
            return "Command Error"
        search_place = search_searxng(place_name_user + ", " + CITY)
        clean_place_name = extract_place_name(search_place)

        if not clean_place_name:
            return basic_search("Adresse (si possible coordonnée GPS) " + place_name_user + ", " + CITY)

        osmData = search_place_data(clean_place_name + ", " + CITY)

        if not osmData :
            return basic_search("Adresse (si possible coordonnée GPS) " + clean_place_name + ", " + CITY)

        answer = generate_answer("Adresse (si possible coordonnée GPS) " + clean_place_name, osmData, "osm")
        return answer
    
    # if nothing, just a question
    return basic_search(question)