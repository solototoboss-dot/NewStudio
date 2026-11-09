# Décisions (mode autonome)

- Plusieurs fichiers créés sans demander (benchmark.py, docs/BENCHMARK.md, PROGRESS/DECISIONS/BLOCKED) : la consigne « mode autonome » l'autorise explicitement.
- Benchmark sans rendu vidéo ni appel ElevenLabs : on mesure ce que le studio a déjà produit, pour ne dépenser aucun crédit.
- Base ouverte en lecture seule par benchmark.py : un benchmark ne doit jamais modifier les données.
- Dossier du projet passé en argument : le worktree n'a pas de data/, les vraies données sont dans le dossier principal.
- docs/BENCHMARK.md est commité (titres de news publics, aucune clé) : c'est la preuve chiffrée du portfolio.
- Accroche : nouveau champ écrit par /scripts plutôt que l'angle ; repli sur la 1re phrase raccourcie pour les anciens scripts.
- Sujet sensible repéré par une liste de mots dans les réglages (simple, modifiable par /retour) ; « enfant(s) » retiré car trop large.
- Tests avec unittest (inclus dans Python) plutôt que pytest : rien à installer.
- Accroches des scripts 2, 4, 7 et 10 écrites à la main dans la base (copie avant : data/studio.avant_accroche.db).
- Lien (jonction) data/ du worktree vers le data/ principal, pour remonter les vidéos depuis cette branche ; ignoré par git.
