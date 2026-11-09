---
name: retour
description: Fait progresser le montage du Studio d'actu IA à partir de mon avis sur une vidéo. À utiliser quand je tape /retour, ou quand je donne mon avis sur une vidéo montée (« trop de sons », « sous-titres trop gros », « rien à changer »...).
---

# Retour sur une vidéo

Le but : à chaque vidéo, le studio apprend de mon avis et ne refait plus la même erreur. Suis ces étapes dans l'ordre, depuis la racine du projet.

1. **Quelle vidéo ?** Si je donne un numéro de script, prends-le. Sinon, prends la dernière vidéo de `data/videos/` (la plus récente, hors fichiers `_avant`) et dis-moi laquelle.
2. **Quel avis ?** Si je n'ai pas encore donné mon avis, demande-le en une phrase : « Qu'est-ce que je dois améliorer sur cette vidéo ? (ou « rien ») ».
3. **Relis la mémoire** avant de changer quoi que ce soit :
   - `.venv/Scripts/python veille/retours.py voir` (les derniers retours) ;
   - la liste `regles_apprises` de `veille/reglages_montage.json`.
   Si mon nouvel avis contredit une règle apprise, dis-le-moi et demande laquelle garder.
4. **Si mon avis est « rien »** (ou « parfait », « ça me va ») : enregistre-le avec
   `.venv/Scripts/python veille/retours.py ajouter <script> "rien" "vidéo validée telle quelle"`, dis que le montage actuel est gardé, et arrête-toi.
5. **Sinon, transforme l'avis en changements précis**, du plus simple au plus lourd :
   - **D'abord les réglages** : `veille/reglages_montage.json` (tailles, couleurs, nombre de mots, emojis, force du zoom, volume de chaque son, transitions, textes du badge et du bouton de fin...). Change les valeurs par petits pas (par exemple 10 à 20 %), pas d'un coup.
   - **Puis le code** si un réglage ne suffit pas : `veille/hyperframes.py` (nouvelle animation, nouvel effet). Ajoute alors un réglage dans le JSON pour pouvoir l'ajuster la prochaine fois. Code Python simple, commentaires en français.
   - **Hors montage** : si l'avis porte sur le texte, la voix ou les photos, modifie la bonne étape (`.claude/skills/scripts/SKILL.md`, `veille/voix.py` ou `veille/visuels.py`).
   - Un nouveau son : fabrique-le avec FFmpeg dans `assets/sons/` (jamais de son téléchargé sans licence claire).
6. **Retiens la leçon** : ajoute à `regles_apprises` une phrase courte et générale qui résume l'avis (exemple : « Pas plus d'un emoji toutes les 4 secondes. »). Si une règle existante dit le contraire, remplace-la au lieu d'en ajouter une.
7. **Enregistre le retour** : `.venv/Scripts/python veille/retours.py ajouter <script> "<mon avis>" "<ce qui a changé>"`.
8. **Remonte la vidéo** : `.venv/Scripts/python veille/hyperframes.py <script>` (environ 4 minutes, lance-le en arrière-plan). L'ancienne version est gardée dans `data/videos/script_<n>_avant.mp4`.
9. **Vérifie** avant de me montrer : prends 2 ou 3 images du MP4 aux moments concernés (`ffmpeg -ss <seconde> -i <video> -frames:v 1 image.png`) et regarde-les. Si le changement ne se voit pas ou casse autre chose, corrige et recommence.
10. **Montre-moi** : ce que tu as compris de mon avis, ce qui a changé (avant → après), le chemin de la nouvelle vidéo, puis redemande « Autre chose à améliorer ? (ou « rien ») ».
11. **Commite** les fichiers modifiés (jamais `data/`, jamais `.env`) avec un message du type `Montage : <résumé du retour>`.
