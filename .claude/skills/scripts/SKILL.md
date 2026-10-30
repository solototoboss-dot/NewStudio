---
name: scripts
description: Écrit les scripts vidéo du Studio d'actu IA. Pour chaque news confirmée par /veille, 3 scripts de 45 à 60 secondes, 2 styles de montage et des idées d'images. À utiliser quand je tape /scripts ou que je demande les scripts du jour.
---

# Scripts du jour

Suis ces étapes dans l'ordre, depuis la racine du projet.

1. Prépare la liste : `.venv/Scripts/python veille/enregistrer_scripts.py preparer`
   La liste est écrite dans `data/a_scripter.json`. Si elle est vide, dis qu'aucune news confirmée n'attend de script (il faut d'abord lancer /veille) et arrête-toi.
2. Lis `data/a_scripter.json`. Pour chaque news, écris **3 scripts** en français, chacun avec un angle différent :
   - **n°1 : l'annonce.** Ce qui vient de se passer, simplement.
   - **n°2 : l'explication.** Comment ça marche ou pourquoi c'est important.
   - **n°3 : l'impact.** Ce que ça change pour le public, ou la question que ça pose.
3. Règles d'écriture de chaque script :
   - **Durée** : entre 115 et 145 mots, soit 45 à 60 secondes lus à voix haute.
   - **Accroche** : la première phrase doit donner envie de rester, en moins de 3 secondes.
   - **Fin** : une phrase de conclusion ou une question au public.
   - **Langue** : phrases courtes, écrites pour être dites. Écris les nombres et les sigles comme on les prononce (« GPT quatre o », « deux minutes »).
   - **Faits** : utilise seulement ce qui est dans le titre, le résumé et le champ `verification`. N'invente aucun chiffre ni aucune citation. Si la vérification émet une réserve (par exemple « en cours d'examen »), dis-la clairement dans le script.
   - **Sujets sensibles** (décès, santé, justice) : ton sobre et factuel, pas de sensationnalisme, parle d'accusations tant que rien n'est jugé. Ne donne jamais de conseil médical.
4. Donne à chaque script un **style de montage** parmi ces 2 :
   - `dynamique` : coupes toutes les 2 à 3 secondes, zooms, gros mots-clés à l'écran, musique rythmée.
   - `explicatif` : plans plus longs, schémas simples, voix posée, sous-titres sobres.
   Utilise les 2 styles pour chaque news (par exemple n°1 en dynamique, n°2 en explicatif). Pour un sujet sensible, choisis seulement `explicatif`.
5. Pour chaque script, propose **3 à 5 idées d'images**, dans l'ordre du texte. Chaque idée commence par 2 à 4 mots-clés de recherche **en anglais** pour la banque de photos Pixabay, puis « : », puis la description en français. Exemple : `robot hand computer mouse : Main de robot qui tient une souris`. Les mots-clés décrivent une photo réelle qui existe probablement (objets, lieux, gestes), jamais un logo ni une personne célèbre.
6. Écris tous les scripts dans `data/scripts.json`, avec exactement ce format (une entrée par script) :
   `[{"news_id": 327, "numero": 1, "angle": "L'annonce de Genie 4", "style": "dynamique", "texte": "...", "images": ["...", "..."]}]`
7. Enregistre-les : `.venv/Scripts/python veille/enregistrer_scripts.py`
   Le script affiche la durée estimée de chaque texte. Si un texte est marqué « hors de 45 à 60 s », dis-le-moi.
8. Montre-moi le résultat : pour chaque news, son titre puis ses 3 scripts (angle, style, durée estimée, texte complet et idées d'images). Rappelle les étapes suivantes : `veille/voix.py`, `veille/sous_titres.py`, `veille/visuels.py`, puis `veille/montage.py`.
