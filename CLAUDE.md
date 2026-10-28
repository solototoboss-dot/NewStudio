# Studio d'actu IA

Studio qui repère chaque jour l'actualité de l'IA, la vérifie et la transforme en vidéos courtes.
Projet de portfolio pour décrocher une alternance en IA.

## Règles

- Je débute : explique chaque ajout en 3 lignes simples.
- Code Python simple, commentaires en français.
- Ne lis jamais le fichier .env et n'affiche jamais mes clés.
- Demande-moi avant de créer plusieurs fichiers.

## Où on en est

- Fait : semaines 1 à 3 (dépôt GitHub, veille RSS, base SQLite sans doublons, skill /veille qui note les news et garde le top 3) et l'agent vérificateur de la semaine 4 (preuve par le flux RSS officiel + une source indépendante), et la skill /scripts des jours 26 et 27 (3 scripts de 45 à 60 secondes par news confirmée, 2 styles de montage, des idées d'images, table scripts dans la base), et la voix de la semaine 5 (veille/voix.py : un MP3 par script avec ElevenLabs eleven_v4, voix française Nicolas et balises d'émotion, Edge TTS fr-FR-HenriNeural en secours, plus le minutage de chaque mot dans data/audio/ ; la clé ELEVENLABS_API_KEY est dans .env ; la voix Nicolas demande le plan Starter, prévu le 2 novembre 2026, d'ici là c'est Edge TTS), et les sous-titres de la semaine 6 (veille/sous_titres.py : un fichier .ass par script, groupes de mots avec le mot dit en couleur, réglages selon le style dynamique ou explicatif).
- Prochaine étape : semaine 7, les visuels (à partir des idées d'images de chaque script) et le montage FFmpeg (voix + images + sous-titres en vidéo verticale 1080x1920).
- Ensuite : semaine 8 (contrôle qualité et tâche planifiée du matin), semaines 9 et 10 (benchmark et portfolio).
- Mets à jour cette section à chaque étape terminée.
