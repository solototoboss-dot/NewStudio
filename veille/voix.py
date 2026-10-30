# Transforme chaque script de la base en voix avec Edge TTS (gratuit, sans clé).
# Pour chaque script : un fichier MP3 dans data/audio/, sa vraie durée, la vitesse gardée
# et le minutage de chaque mot (script_<id>_mots.json), qui sert aux sous-titres.
# Un script qui a déjà son audio est sauté : relancer le programme ne recrée rien.

import asyncio  # edge-tts travaille en "asynchrone" : on attend la voix sans bloquer
import json  # pour écrire le minutage des mots
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

# Edge TTS compte le temps en "ticks" de 100 nanosecondes : 10 millions par seconde
TICKS_PAR_SECONDE = 10_000_000

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


async def creer_audio(texte, fichier_audio, vitesse):
    """Écrit la voix dans le fichier MP3 et renvoie la liste des mots avec leur début et leur fin."""
    communication = edge_tts.Communicate(texte, VOIX, rate=vitesse, boundary="WordBoundary")
    mots = []
    with open(fichier_audio, "wb") as fichier:
        # Edge TTS envoie des morceaux : soit du son, soit l'annonce d'un mot prononcé
        async for morceau in communication.stream():
            if morceau["type"] == "audio":
                fichier.write(morceau["data"])
            elif morceau["type"] == "WordBoundary":
                debut = morceau["offset"] / TICKS_PAR_SECONDE
                fin = (morceau["offset"] + morceau["duration"]) / TICKS_PAR_SECONDE
                mots.append({"mot": morceau["text"], "debut": round(debut, 3), "fin": round(fin, 3)})
    return mots


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
    """Crée l'audio, règle la vitesse si besoin et renvoie (durée, vitesse gardée, mots)."""
    vitesse = "+0%"
    mots = asyncio.run(creer_audio(texte, fichier_audio, vitesse))
    duree = mesurer_duree(fichier_audio)
    if dans_la_cible(duree):
        return duree, vitesse, mots

    # Hors cible : on change un peu la vitesse à chaque essai. Le texte, lui, ne change jamais.
    essais = VITESSES_PLUS_LENTES if duree < DUREE_MIN else VITESSES_PLUS_RAPIDES
    for vitesse in essais:
        mots = asyncio.run(creer_audio(texte, fichier_audio, vitesse))
        duree = mesurer_duree(fichier_audio)
        if dans_la_cible(duree):
            break
    return duree, vitesse, mots  # si rien ne suffit, on garde le dernier essai, le plus proche


def main():
    base.creer_base()
    DOSSIER_AUDIO.mkdir(parents=True, exist_ok=True)

    scripts = base.scripts_sans_voix()
    print(f"{len(scripts)} script(s) à mettre en voix")

    for script_id, news_id, numero, texte in scripts:
        fichier_audio = DOSSIER_AUDIO / f"script_{script_id}.mp3"
        try:
            duree, vitesse, mots = voix_du_script(texte, fichier_audio)
        except Exception as erreur:  # pas d'internet, ffprobe absent...
            print(f"Script {script_id} : échec de la voix ({erreur})")
            continue
        # Le minutage des mots servira aux sous-titres
        with open(DOSSIER_AUDIO / f"script_{script_id}_mots.json", "w", encoding="utf-8") as fichier:
            json.dump(mots, fichier, ensure_ascii=False, indent=2)
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
