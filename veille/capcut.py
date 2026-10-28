# Prépare un projet CapCut par script, avec la bibliothèque open source pyCapCut.
# Le projet contient la voix et un fond vertical 1080 x 1920. Ensuite, dans CapCut :
# ouvrir le projet, cliquer sur « Sous-titres automatiques », choisir un style, exporter.
# CapCut n'a pas d'API officielle : l'export reste manuel.

import os  # pour trouver le dossier de CapCut dans AppData
import re  # pour fabriquer un nom de projet sans caractères spéciaux
import subprocess  # pour lancer FFmpeg qui crée l'image de fond
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import pycapcut as cc  # la bibliothèque qui écrit les projets CapCut

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
FICHIER_FOND = RACINE / "data" / "fond_capcut.png"  # fond provisoire, remplacé par les visuels en semaine 7
COULEUR_FOND = "0x1a1a2e"  # bleu nuit

# Le dossier où CapCut range ses projets sur Windows
DOSSIER_CAPCUT = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def creer_fond():
    """Crée une fois pour toutes l'image de fond verticale avec FFmpeg."""
    if not FICHIER_FOND.exists():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                        "-i", f"color=c={COULEUR_FOND}:s=1080x1920", "-frames:v", "1", str(FICHIER_FOND)],
                       check=True)


def nom_projet(script_id, angle):
    """Fabrique un nom de projet lisible dans CapCut, ex. « Studio 1 - L'annonce de GPT-6.1 Terra »."""
    angle = re.sub(r'[\\/:*?"<>|]', "", angle)[:40].strip()  # caractères interdits dans un nom de dossier
    return f"Studio {script_id} - {angle}"


def creer_projet(dossier, nom, fichier_audio, duree):
    """Écrit un projet CapCut vertical avec la voix et le fond, de la durée de la voix."""
    projet = dossier.create_draft(nom, 1080, 1920, allow_replace=True)
    projet.add_track(cc.TrackType.video)
    projet.add_track(cc.TrackType.audio)

    # La voix d'abord : sa vraie durée (en microsecondes) fixe la durée de la vidéo
    voix = cc.AudioMaterial(str(fichier_audio))
    projet.add_segment(cc.AudioSegment(voix, cc.Timerange(0, voix.duration)))
    projet.add_segment(cc.VideoSegment(str(FICHIER_FOND), cc.Timerange(0, voix.duration)))
    projet.save()


def main():
    base.creer_base()
    if not DOSSIER_CAPCUT.exists():
        print(f"Dossier des projets CapCut introuvable : {DOSSIER_CAPCUT}")
        print("Ouvre CapCut une première fois, puis relance ce script.")
        return

    scripts = base.scripts_sans_capcut()
    if not scripts:
        print("Aucun script n'attend son projet CapCut. Lance d'abord veille/voix.py.")
        return

    creer_fond()
    dossier = cc.DraftFolder(str(DOSSIER_CAPCUT))
    for script_id, news_id, numero, angle, audio, duree in scripts:
        nom = nom_projet(script_id, angle)
        try:
            creer_projet(dossier, nom, (RACINE / audio).resolve(), duree)
        except Exception as erreur:
            print(f"Script {script_id} : projet CapCut non créé ({erreur})")
            continue
        base.enregistrer_capcut(script_id, nom)
        print(f"Projet CapCut prêt : « {nom} » ({duree:.0f} s)")

    print("\nDans CapCut : ouvre chaque projet, clique sur Texte > Sous-titres automatiques,")
    print("choisis un style, puis exporte la vidéo.")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
