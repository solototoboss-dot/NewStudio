# Benchmark du studio

Mesuré le 09/11/2026 par `veille/benchmark.py`, sur les données réelles du studio (aucune API payante appelée).

## Entonnoir de la chaîne

| Étape | Nombre |
|---|---:|
| News collectées (flux RSS) | 180 |
| News notées par Claude | 28 |
| News vérifiées | 6 |
|   dont confirmées | 4 |
|   dont incertaines | 2 |
|   dont fausses | 0 |
| Scripts écrits | 12 |
| Scripts avec voix | 12 |
| Scripts avec photos | 12 |
| Vidéos montées | 4 |
| Vidéos OK au contrôle | 4 |
| Vidéos à revoir | 0 |
| Vidéos bloquées | 0 |

## Voix

| Moteur | Scripts | Caractères | Minutes de voix | Coût estimé |
|---|---:|---:|---:|---:|
| edge:fr-FR-HenriNeural | 12 | 9179 | 9.2 | gratuit |

Coût ElevenLabs estimé au prix du plan Creator (22 $ pour 100 000 caractères).

## Qualité des vidéos (mesurée par FFmpeg)

| Script | Format | Durée | Écart avec la voix | Volume | Crête | Photos | Poids | Contrôle |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 2 | 1080x1920 à 30 i/s | 46.9 s | +0.4 s | -14.4 LUFS | -1.4 dBFS | 4 | 18 Mo | ok |
| 4 | 1080x1920 à 30 i/s | 46.2 s | +0.3 s | -14.3 LUFS | -1.5 dBFS | 5 | 26 Mo | ok |
| 7 | 1080x1920 à 30 i/s | 46.0 s | +0.4 s | -14.3 LUFS | -1.4 dBFS | 5 | 30 Mo | ok |
| 10 | 1080x1920 à 30 i/s | 46.2 s | +0.3 s | -14.4 LUFS | -1.4 dBFS | 4 | 20 Mo | ok |

Volume moyen : -14.4 LUFS (cible des réseaux : -14 LUFS ±2,5).

## Temps de production

| Matin | Vidéos HyperFrames | Minutes | Minutes par vidéo |
|---|---:|---:|---:|
| 2026-11-09 | 3 | 12 | 4.0 |

Repères mesurés pendant le développement : montage FFmpeg seul environ 1 min 45 par vidéo, HyperFrames environ 4 min (rendu dans Chrome, plus riche : sous-titres animés, emojis, sons).

## Boucle d'amélioration

- Retours donnés avec /retour : 0
- Règles de montage apprises (reglages_montage.json) : 2
