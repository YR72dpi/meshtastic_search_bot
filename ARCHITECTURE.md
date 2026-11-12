# Architecture et fonctionnement

Ce document décrit le fonctionnement interne du bot Meshtastic Search Bot, avec l’accent sur le système LLM et le mécanisme de bascule Vireonix → Ollama.

## 1. Vue d’ensemble

Le bot reçoit des messages texte sur un canal Meshtastic dédié, interprète les commandes, récupère des données externes (SearXNG, OpenStreetMap, Géorisques), puis renvoie une réponse courte adaptée au réseau LoRa.

Les composants principaux sont :

- Meshtastic : réception / envoi des messages
- Bot Python : logique applicative
- SearXNG : recherche web
- OpenStreetMap / Nominatim : géolocalisation
- LLM router : point d’entrée unique pour toutes les générations de texte
- Ollama : fallback local
- Vireonix : fournisseur prioritaire, si disponible

## 2. La couche LLM

Le point d’entrée unique est :

- `tool/llm.py`

La fonction `call_llm(prompt)` centralise tous les appels LLM du projet.

Le flux est le suivant :

1. Le bot appelle `call_llm(...)`
2. Le routeur tente Vireonix en premier
3. Si Vireonix échoue (erreur réseau, timeout, `429`, `5xx`, réponse vide ou invalide), le routeur retente une fois ou deux selon la logique de retry
4. S’il continue à échouer, le routeur bascule sur Ollama
5. Si Ollama fonctionne, la réponse est renvoyée
6. Si les deux fournisseurs échouent, une erreur explicite remonte vers l’appelant

Le but est d’éviter de dupliquer la logique de fallback dans chaque fonction du projet.

### Fichiers concernés

```text
tool/
├── llm.py                  # routeur global public
├── llm_providers/
│   ├── __init__.py         # imports et orchestration
│   ├── vireonix.py         # client Vireonix
│   └── ollama.py           # client Ollama
```

## 3. Pourquoi ce design ?

Le code a été structuré pour que les fonctions métier ne sachent pas lequel des LLM est utilisé.

Par exemple, un module qui synthétise une réponse ou extrait un nom de lieu n’a pas besoin d’écrire :

- `call_ollama(...)`
- ou `call_vireonix(...)`

Il appelle simplement :

- `call_llm(prompt)`

Cela permet de garder :

- une seule logique de fallback
- un point de contrôle central pour logs et diagnostics
- un comportement cohérent sur toute l’application

## 4. Le fonctionnement exact du fallback

La logique de fallback est :

```python
for provider in ["vireonix", "ollama"]:
    try:
        response = call_provider(provider, prompt)
        if response is valid:
            return response
    except Exception:
        log failure
        continue

raise RuntimeError("All LLM providers failed")
```

### Cas reconnus comme “échec”

Le routeur considère comme invalide une réponse qui est :

- vide
- `None`
- `"none"`, `"null"`, etc.
- non exploitable par le code

Du côté Vireonix, le client applique aussi une logique de retry sur les erreurs de type :

- `429`
- `500`, `502`, `503`, `504`
- `error.type` correspondant à `rate_limit_exceeded`, `server_error`, `internal_error`

En pratique, la règle est :

- 2 tentatives maximum pour Vireonix
- backoff exponentiel très court
- puis bascule vers Ollama

## 5. Les commandes qui utilisent le LLM

Les fonctions du bot qui passent par le routeur sont typiquement :

- `extract_place_name(...)`
- `build_search_query(...)`
- `generate_answer(...)`
- `translate(...)`

Elles utilisent la même méthode : `call_llm(...)`.

Cela garantit qu’un échec d’un provider ne casse pas le flux complet du bot.

## 6. Flux de recherche web

Pour `/search` ou pour une requête libre :

1. le bot reçoit un message texte
2. le routeur LLM reformule la requête ou génère une réponse synthétique selon le besoin
3. SearXNG récupère les résultats web
4. le bot construit une réponse concise pour Meshtastic

### Exemple de séquence

```text
Meshtastic message
    ↓
Bot receives text
    ↓
call_llm(prompt)
    ↓
Vireonix ? -> retry / fallback
    ↓
Ollama if needed
    ↓
SearXNG query / answer generation
    ↓
Meshtastic reply
```

## 7. Flux `/osm`

Pour `/osm`, le bot :

1. cherche un lieu via OpenStreetMap / Nominatim
2. si nécessaire, lance une recherche web pour retrouver le bon nom du lieu
3. appelle le LLM pour extraire le vrai nom propre depuis les résultats SearXNG
4. refait une recherche OSM plus précise
5. formatte le résultat avec nom, adresse et coordonnées

Le LLM est donc utilisé ici pour nettoyer une recherche de lieu, pas pour formater l’adresse finale.

## 8. Flux `/gps`

`/gps` ne dépend pas du LLM :

- le bot lit la position GPS du nœud
- appelle Nominatim en reverse geocoding
- renvoie `Long`, `Lat` et éventuellement l’adresse

## 9. Gestion des erreurs

Le projet est volontairement tolérant aux pannes externes :

- si le fournisseur principal est lent, il bascule
- si la réponse est invalide, il bascule
- si les deux échouent, le bot renvoie un message dégradé plutôt que de planter complètement

C’est particulièrement important pour un système qui doit rester robuste sur un réseau radio LoRa, où la fiabilité et la tolérance aux erreurs sont plus importantes qu’une génération “parfaite” du premier coup.

## 10. Résumé

Le système est construit autour d’un principe simple :

- le bot n’appelle pas directement des LLMs dans le code métier
- il appelle un routeur unique
- ce routeur choisit automatiquement le meilleur backend disponible
- Vireonix est le fournisseur prioritaire
- Ollama est le secours local fiable

C’est le bon compromis pour avoir un système qui reste utile même quand un service externe tombe en panne.
