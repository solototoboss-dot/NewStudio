---
name: veille
description: Lance la veille du jour du Studio d'actu IA. Collecte les news, les note sur 10 et garde le top 3. À utiliser quand je tape /veille ou que je demande la veille du jour.
---

# Veille du jour

Suis ces étapes dans l'ordre, depuis la racine du projet.

1. Collecte les news : `.venv/Scripts/python veille/lire_flux.py`
2. Prépare la liste à noter : `.venv/Scripts/python veille/a_noter.py`
   La liste est écrite dans `data/a_noter.json`. Si elle est vide, dis-le et arrête-toi.
3. Lis `data/a_noter.json` et note chaque news de 0 à 10 avec ces critères :
   - **Nouveauté** : une vraie annonce (modèle, outil, fonction, chiffre) vaut plus qu'un article de fond, un tutoriel ou une publicité.
   - **Impact** : combien de personnes ou d'entreprises sont concernées.
   - **Intérêt vidéo** : est-ce qu'un public français qui suit l'IA voudrait la voir expliquée en 60 secondes ?
   - **Doublons** : si plusieurs news parlent de la même annonce, garde la note sur la plus complète (de préférence la source officielle) et mets 0 aux autres, avec la raison « doublon de #id ».
   Juge seulement à partir du titre et du résumé fournis : n'invente aucune information.
4. Écris tes notes dans `data/scores.json`, avec exactement ce format (une entrée par news, raison en une ligne courte) :
   `[{"id": 12, "score": 8, "raison": "Nouveau modèle open source, gros impact"}]`
5. Enregistre-les : `.venv/Scripts/python veille/enregistrer_scores.py`
6. Montre-moi le top 3 affiché : rang, note, titre, source, raison et lien. S'il n'y en a aucun, dis qu'aucune news ne mérite une vidéo aujourd'hui.
