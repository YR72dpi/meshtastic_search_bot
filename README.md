# meshtastic_search_bot

## Installation

### 1. Configurer les variables d'environnement

Copier le fichier d'exemple et adapter les valeurs dans `.env` :

```bash
cp .env.example .env
```

La variable `SEARXNG_URL` doit pointer vers l'API de recherche SearXNG utilisée par le bot :

```dotenv
SEARXNG_URL="http://127.0.0.1:8080/search"
```

Si SearXNG est installé sur un autre serveur, remplacer `127.0.0.1` par son adresse IP ou son nom de domaine.

### 2. Démarrer et arrêter les services

```bash
docker compose up -d valkey core
docker compose down
```

### 3. Activer le format JSON de SearXNG

Éditer le fichier `core-config/settings.yml` et ajouter `json` à la liste des formats de recherche :

```yaml
search:
	formats:
		- html
		- json
```

Le bot utilise ce format pour récupérer les résultats de recherche avant d'envoyer le contexte au LLM.

Pour reconstruire le bot après une modification du code :

```bash
docker compose up -d --build
```
