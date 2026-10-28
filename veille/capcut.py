# Prépare un projet CapCut par script, avec la bibliothèque open source pyCapCut.
# Le projet contient la voix et les photos Pexels du script (ou un fond uni s'il n'y en a pas
# encore), en vertical 1080 x 1920. Ensuite, dans CapCut :
# ouvrir le projet, cliquer sur « Sous-titres automatiques », choisir un style, exporter.
# CapCut n'a pas d'API officielle : l'export reste manuel.

import json  # pour lire la liste des images d'un script
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
ZOOM_FIN = 1.08  # chaque image grossit de 8 % pendant qu'elle est à l'écran

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


def segment_image(fichier, debut, duree):
    """Crée un morceau de vidéo avec une image qui remplit tout l'écran et zoome doucement (effet Ken Burns)."""
    image = cc.VideoMaterial(str(fichier))
    # CapCut place l'image « en entier » dans l'écran ; on l'agrandit pour qu'elle le remplisse sans bandes
    remplir = max(1080 / image.width, 1920 / image.height) / min(1080 / image.width, 1920 / image.height)
    segment = cc.VideoSegment(image, cc.Timerange(debut, duree))
    segment.add_keyframe(cc.KeyframeProperty.uniform_scale, 0, remplir)
    segment.add_keyframe(cc.KeyframeProperty.uniform_scale, duree, remplir * ZOOM_FIN)
    return segment


def creer_projet(dossier, nom, fichier_audio, images):
    """Écrit un projet CapCut vertical : la voix, et les images réparties sur toute sa durée."""
    projet = dossier.create_draft(nom, 1080, 1920, allow_replace=True)
    projet.add_track(cc.TrackType.video)
    projet.add_track(cc.TrackType.audio)

    # La voix d'abord : sa vraie durée (en microsecondes) fixe la durée de la vidéo
    voix = cc.AudioMaterial(str(fichier_audio))
    projet.add_segment(cc.AudioSegment(voix, cc.Timerange(0, voix.duration)))

    if not images:  # pas encore de visuels : le fond uni provisoire
        projet.add_segment(cc.VideoSegment(str(FICHIER_FOND), cc.Timerange(0, voix.duration)))
    else:
        # Chaque image dure le même temps, dans l'ordre des idées d'images (donc du texte)
        part = voix.duration // len(images)
        for i, image in enumerate(images):
            duree = part if i < len(images) - 1 else voix.duration - part * i  # la dernière finit pile avec la voix
            projet.add_segment(segment_image(image, part * i, duree))
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
    for script_id, news_id, numero, angle, audio, duree, visuels in scripts:
        nom = nom_projet(script_id, angle)
        images = [(RACINE / chemin).resolve() for chemin in json.loads(visuels or "[]")]
        try:
            creer_projet(dossier, nom, (RACINE / audio).resolve(), images)
        except Exception as erreur:
            print(f"Script {script_id} : projet CapCut non créé ({erreur})")
            continue
        base.enregistrer_capcut(script_id, nom)
        print(f"Projet CapCut prêt : « {nom} » ({duree:.0f} s, {len(images)} image(s))")

    print("\nDans CapCut : ouvre chaque projet, clique sur Texte > Sous-titres automatiques,")
    print("choisis un style, puis exporte la vidéo.")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
