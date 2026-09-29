# commande 

/help : donne les cmmande disponible
/horaire (demande) : demande l'horraire
/adresse (demande) : demande l'adresse
sinon general : demande generaliste

# algo

/horaire & /adresse
    - extraire le nom exacte
        - searnxg + llm
    - osm (avec ville)
    - formulation de la reponse avec llm (données le json de osm)

general
    llm generate search + searnxg + genere la reponse

# orga
    fichier de prompt
    env : Nom de la ville
