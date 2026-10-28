# Monte la vidéo finale de chaque script avec FFmpeg, sans CapCut ni abonnement :
# les photos (plein écran, zoom lent), la voix, et nos sous-titres animés incrustés.
# Résultat : une vidéo verticale 1080 x 1920 prête pour TikTok, Reels et Shorts.

import json  # pour lire la liste des images d'un script
import subprocess  # pour lancer FFmpeg
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
DOSSIER_VIDEOS = RACINE / "data" / "videos"
DOSSIER_POLICES = "assets/polices"  # la police Montserrat des sous-titres

LARGEUR, HAUTEUR, IMAGES_PAR_SECONDE = 1080, 1920, 30
ZOOM_FIN = 1.08  # chaque photo grossit de 8 % pendant qu'elle est à l'écran
COULEUR_FOND = "0x1a1a2e"  # bleu nuit, si un script n'a pas de photo

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def filtre_photo(numero, nb_images):
    """Filtre FFmpeg d'une photo : elle remplit l'écran vertical puis zoome doucement vers le centre."""
    # On agrandit d'abord la photo (x1,5) pour que le zoom reste fluide, sans tremblements
    grand_l, grand_h = LARGEUR * 3 // 2, HAUTEUR * 3 // 2
    return (f"[{numero}:v]scale={grand_l}:{grand_h}:force_original_aspect_ratio=increase,"
            f"crop={grand_l}:{grand_h},"
            f"zoompan=z='1+{ZOOM_FIN - 1}*on/{nb_images}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={nb_images}:s={LARGEUR}x{HAUTEUR}:fps={IMAGES_PAR_SECONDE},setsar=1[p{numero}]")


def commande_ffmpeg(audio, duree, sous_titres, images, sortie):
    """Prépare la commande FFmpeg qui assemble photos, voix et sous-titres."""
    commande = ["ffmpeg", "-y", "-v", "error"]
    if images:
        for image in images:
            commande += ["-i", image]  # une seule image par entrée : zoompan fabrique les images suivantes
        # Chaque photo reste le même temps à l'écran, dans l'ordre du texte
        nb_images = int(duree * IMAGES_PAR_SECONDE / len(images)) + 1
        filtres = [filtre_photo(i, nb_images) for i in range(len(images))]
        filtres.append("".join(f"[p{i}]" for i in range(len(images)))
                       + f"concat=n={len(images)}:v=1:a=0[photos]")
    else:
        commande += ["-f", "lavfi", "-i", f"color=c={COULEUR_FOND}:s={LARGEUR}x{HAUTEUR}:r={IMAGES_PAR_SECONDE}"]
        filtres = ["[0:v]null[photos]"]
    entree_voix = len(images) if images else 1
    commande += ["-i", audio]

    # Les sous-titres sont incrustés par-dessus les photos, avec la police du projet
    chemin_ass = sous_titres.replace("\\", "/")
    filtres.append(f"[photos]ass={chemin_ass}:fontsdir={DOSSIER_POLICES}[video]")

    commande += [
        "-filter_complex", ";".join(filtres),
        "-map", "[video]", "-map", f"{entree_voix}:a",
        "-t", f"{duree + 0.3:.2f}",  # la vidéo s'arrête juste après le dernier mot
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",  # la vidéo démarre vite quand on la regarde en ligne
        sortie,
    ]
    return commande


def main():
    base.creer_base()
    DOSSIER_VIDEOS.mkdir(parents=True, exist_ok=True)
    scripts = base.scripts_a_monter()
    if not scripts:
        print("Aucun script n'attend sa vidéo. Lance d'abord voix.py puis sous_titres.py.")
        return

    for script_id, audio, duree, sous_titres, visuels in scripts:
        images = [chemin.replace("\\", "/") for chemin in json.loads(visuels or "[]")]
        sortie = f"data/videos/script_{script_id}.mp4"
        print(f"Script {script_id} : montage de {duree:.0f} s avec {len(images)} photo(s)...")
        # FFmpeg est lancé depuis la racine du projet : les chemins relatifs évitent les soucis de « C: »
        resultat = subprocess.run(commande_ffmpeg(audio, duree, sous_titres, images, sortie),
                                  cwd=RACINE, capture_output=True, text=True)
        if resultat.returncode != 0:
            print(f"   Échec du montage : {resultat.stderr.strip()[-300:]}")
            continue
        base.enregistrer_video(script_id, sortie)
        print(f"   Vidéo prête : {sortie}")

    print("\nVidéos dans data/videos/")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
