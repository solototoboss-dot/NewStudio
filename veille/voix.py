# Transforme chaque script de la base en voix avec Edge TTS (gratuit, sans clé).
# Pour chaque script : un fichier MP3 dans data/audio/, sa vraie durée et la vitesse gardée.
# Un script qui a déjà son audio est sauté : relancer le programme ne recrée rien.

import asyncio  # edge-tts travaille en "asynchrone" : on attend la voix sans bloquer
import subprocess  # pour lancer ffprobe, qui mesure la durée d'un fichier audio
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import edge_tts  # la voix de Microsoft Edge

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
DOSSIER_AUDIO = RACINE / "data" / "audio"

VOIX = "fr-FR-HenriNeural"
DUREE_MIN, DUREE_MAX = 45, 60  # durée visée, en secondes

# Les vitesses à essayer quand l'audio est trop court (plus lent) ou trop long (plus rapide).
# On s'arrête à 10 % : au-delà, la voix risque de sonner bizarrement.
VITESSES_PLUS_LENTES = ["-2%", "-4%", "-6%", "-8%", "-10%"]
VITESSES_PLUS_RAPIDES = ["+2%", "+4%", "+6%", "+8%", "+10%"]

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


async def creer_audio(texte, fichier_audio, vitesse):
    """Demande la voix à Edge TTS et l'écrit dans le fichier MP3."""
    communication = edge_tts.Communicate(texte, VOIX, rate=vitesse)
    await communication.save(str(fichier_audio))


def mesurer_duree(fichier_audio):
    """Renvoie la vraie durée du fichier audio en secondes, mesurée par ffprobe."""
    resultat = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(fichier_audio)],
        capture_output=True, text=True, check=True,
    )
    return round(float(resultat.stdout), 2)


def dans_la_cible(duree):
    """Dit si une durée est bien entre 45 et 60 secondes."""
    return DUREE_MIN <= duree <= DUREE_MAX


def voix_du_script(texte, fichier_audio):
    """Crée l'audio, règle la vitesse si besoin et renvoie (durée, vitesse gardée)."""
    vitesse = "+0%"
    asyncio.run(creer_audio(texte, fichier_audio, vitesse))
    duree = mesurer_duree(fichier_audio)
    if dans_la_cible(duree):
        return duree, vitesse

    # Hors cible : on change un peu la vitesse à chaque essai. Le texte, lui, ne change jamais.
    essais = VITESSES_PLUS_LENTES if duree < DUREE_MIN else VITESSES_PLUS_RAPIDES
    for vitesse in essais:
        asyncio.run(creer_audio(texte, fichier_audio, vitesse))
        duree = mesurer_duree(fichier_audio)
        if dans_la_cible(duree):
            break
    return duree, vitesse  # si rien ne suffit, on garde le dernier essai, le plus proche


def main():
    base.creer_base()
    DOSSIER_AUDIO.mkdir(parents=True, exist_ok=True)

    scripts = base.scripts_sans_voix()
    print(f"{len(scripts)} script(s) à mettre en voix")

    for script_id, news_id, numero, texte in scripts:
        fichier_audio = DOSSIER_AUDIO / f"script_{script_id}.mp3"
        try:
            duree, vitesse = voix_du_script(texte, fichier_audio)
        except Exception as erreur:  # pas d'internet, ffprobe absent...
            print(f"Script {script_id} : échec de la voix ({erreur})")
            continue
        chemin = fichier_audio.relative_to(RACINE).as_posix()
        base.enregistrer_voix(script_id, chemin, duree, f"edge:{VOIX}", vitesse)
        print(f"Script {script_id} (news #{news_id}, n°{numero}) : {duree:.1f} s à {vitesse}")

    # Le bilan de tous les audios, y compris ceux qui existaient déjà
    print("\nscript | fichier | durée | vitesse | cible")
    for script_id, audio, duree, vitesse in base.scripts_avec_voix():
        etat = "OK" if base.audio_present(audio) and dans_la_cible(duree) else "HORS CIBLE"
        print(f"{script_id} | {audio} | {duree:.1f} s | {vitesse} | {etat}")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
