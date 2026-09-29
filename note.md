# commande 

/help : donne les commande disponible
/horaire [lieu] : Donnée open street map
/adresse [lieu] : Donnée open street map
[Votre demande] : Données SearXNG

# algo

/horaire & /adresse
- extraire le nom exacte
    - searnxg : recherche du texte où le nom apparait
        - nom + city
    - llm : isole le nom

Si NONE
- searxng avec la question posé

Si nom isolé
- osm (avec ville)
- formulation de la reponse avec llm (données le json de osm)

general
    llm generate search + searnxg + genere la reponse

# orga
    fichier main.py
    fichier vireonix
    fichier osm
    fichier searnxg
    fichier de prompt
    env : Nom de la ville
