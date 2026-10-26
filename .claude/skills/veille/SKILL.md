---
name: veille
description: Lance la veille du jour du Studio d'actu IA. Collecte les news, les note sur 10, garde le top 3 et le fait vérifier. À utiliser quand je tape /veille ou que je demande la veille du jour.
---

# Veille du jour

Suis ces étapes dans l'ordre, depuis la racine du projet.

1. Collecte les news : `.venv/Scripts/python veille/lire_flux.py`
2. Prépare la liste à noter : `.venv/Scripts/python veille/a_noter.py`
   La liste est écrite dans `data/a_noter.json`. Si elle est vide, passe directement à l'étape 6.
3. Lis `data/a_noter.json` et note chaque news de 0 à 10 avec ces critères :
   - **Nouveauté** : une vraie annonce (modèle, outil, fonction, chiffre) vaut plus qu'un article de fond, un tutoriel ou une publicité.
   - **Impact** : combien de personnes ou d'entreprises sont concernées.
   - **Intérêt vidéo** : est-ce qu'un public français qui suit l'IA voudrait la voir expliquée en 60 secondes ?
   - **Doublons** : si plusieurs news parlent de la même annonce, garde la note sur la plus complète (de préférence la source officielle) et mets 0 aux autres, avec la raison « doublon de #id ».
   Juge seulement à partir du titre et du résumé fournis : n'invente aucune information.
4. Écris tes notes dans `data/scores.json`, avec exactement ce format (une entrée par news, raison en une ligne courte) :
   `[{"id": 12, "score": 8, "raison": "Nouveau modèle open source, gros impact"}]`
5. Enregistre-les : `.venv/Scripts/python veille/enregistrer_scores.py`
   Le script écrit le top à vérifier dans `data/a_verifier.json`.
6. Lis `data/a_verifier.json`. S'il est vide, dis qu'aucune news ne mérite une vidéo aujourd'hui et arrête-toi. Sinon, lance un sous-agent `verificateur` par news, tous en même temps, en donnant à chacun l'id, le titre, la source et le lien.
7. Rassemble leurs réponses JSON dans une liste, écris-la dans `data/verifications.json`, puis lance : `.venv/Scripts/python veille/enregistrer_verifications.py`
8. Montre-moi le résultat final : pour chaque news, la note, le titre, le verdict, l'explication et les liens de preuve. Rappelle que seules les news confirmées passeront à l'étape des scripts.
