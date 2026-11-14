update:
	git pull origin main
	sudo docker compose build meshtastic-llm-bot --no-cache
	sudo docker compose up meshtastic-llm-bot -d
	