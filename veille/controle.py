# Contrôle qualité : vérifie chaque vidéo montée avant de la publier.
# Format, durée, volume du son, écrans noirs, images figées, photos : tout est mesuré avec FFmpeg.
# Le verdict (ok ou à revoir) et la liste des problèmes sont rangés dans la base, table scripts.
#
# Lancement : python veille/controle.py        -> contrôle les vidéos pas encore contrôlées
#             python veille/controle.py 2 5    -> recontrôle les scripts 2 et 5

import hashlib  # pour repérer deux photos identiques
import json  # pour lire les listes de photos et de mots
import re  # pour lire les mesures dans le texte affiché par FFmpeg
import subprocess  # pour lancer FFmpeg et ffprobe
import sys  # pour lire les numéros de scripts donnés au lancement
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent

# Ce qu'attendent TikTok, Reels et Shorts
LARGEUR, HAUTEUR, IMAGES_PAR_SECONDE = 1080, 1920, 30
DUREE_MIN, DUREE_MAX = 40, 60  # en secondes : au-delà de 60 s, la vidéo n'est plus un Short partout
VOLUME_CIBLE, ECART_VOLUME = -14, 2.5  # en LUFS : le volume moyen des vidéos des réseaux, à ±2,5 près
CRETE_MAX = -1.0  # en dBFS : au-dessus, le son risque de saturer après la compression des plateformes
SILENCE_DEBUT_MAX = 0.8  # en secondes : la voix doit démarrer tout de suite
LARGEUR_PHOTO_MIN = 720  # en pixels : en dessous, la photo est floue en plein écran
PHOTOS_MIN = 3

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def mesurer_video(chemin):
    """Taille de l'image, images par seconde, durée et présence du son, lues par ffprobe."""
    sortie = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
         "-of", "json", str(chemin)], capture_output=True, text=True).stdout
    infos = json.loads(sortie or "{}")
    image = next((s for s in infos.get("streams", []) if s["codec_type"] == "video"), {})
    a_du_son = any(s["codec_type"] == "audio" for s in infos.get("streams", []))
    num, den = image.get("r_frame_rate", "0/1").split("/")
    return image.get("width"), image.get("height"), round(int(num) / int(den)), \
        float(infos.get("format", {}).get("duration", 0)), a_du_son


def mesurer_son(chemin):
    """Volume moyen (LUFS), crête (dBFS) et durée du silence au début, mesurés par FFmpeg."""
    texte = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(chemin), "-vn",
         "-af", "ebur128=peak=true,silencedetect=n=-45dB:d=0.3", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    volume = re.findall(r"I:\s+(-?[\d.]+) LUFS", texte)
    crete = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", texte)
    # Un silence qui commence à 0 et finit à t : la voix démarre au bout de t secondes
    debut = re.search(r"silence_start: 0(?:\.0+)?\s.*?silence_end: ([\d.]+)", texte, re.S)
    return (float(volume[-1]) if volume else None,
            float(crete[-1]) if crete and crete[-1] != "-inf" else None,
            float(debut.group(1)) if debut else 0.0)


def mesurer_image(chemin):
    """Écrans noirs de plus de 0,5 s et images figées de plus de 3 s."""
    texte = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(chemin), "-an",
         "-vf", "blackdetect=d=0.5:pix_th=0.10,freezedetect=n=0.003:d=3", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    noirs = re.findall(r"black_start:([\d.]+)", texte)
    figees = re.findall(r"freeze_start: ([\d.]+)", texte)
    return [float(t) for t in noirs], [float(t) for t in figees]


def taille_photo(chemin):
    """Largeur d'une photo, lue par ffprobe (pas besoin d'installer une bibliothèque d'images)."""
    sortie = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0",
                             str(chemin)], capture_output=True, text=True).stdout.strip()
    return int(sortie) if sortie.isdigit() else 0


def controler(script_id, video, duree_voix, visuels, audio):
    """Renvoie la liste des problèmes d'une vidéo : (gravité, explication). Vide si tout va bien."""
    problemes = []
    chemin = RACINE / video
    if not chemin.exists():
        return [("bloquant", f"vidéo introuvable : {video}")]

    largeur, hauteur, ips, duree, a_du_son = mesurer_video(chemin)
    if (largeur, hauteur) != (LARGEUR, HAUTEUR):
        problemes.append(("bloquant", f"format {largeur}x{hauteur} au lieu de {LARGEUR}x{HAUTEUR} (vertical)"))
    if ips != IMAGES_PAR_SECONDE:
        problemes.append(("a_revoir", f"{ips} images par seconde au lieu de {IMAGES_PAR_SECONDE}"))
    if not a_du_son:
        problemes.append(("bloquant", "la vidéo n'a pas de son"))
    if not DUREE_MIN <= duree <= DUREE_MAX:
        problemes.append(("a_revoir", f"durée {duree:.1f} s, hors de {DUREE_MIN} à {DUREE_MAX} s"))
    if duree_voix and abs(duree - (duree_voix + 0.3)) > 0.6:
        problemes.append(("bloquant", f"vidéo de {duree:.1f} s pour une voix de {duree_voix:.1f} s : fin coupée ou trop longue"))

    if a_du_son:
        volume, crete, silence_debut = mesurer_son(chemin)
        if volume is not None and abs(volume - VOLUME_CIBLE) > ECART_VOLUME:
            problemes.append(("a_revoir", f"volume moyen {volume:.1f} LUFS, les réseaux visent {VOLUME_CIBLE} LUFS"))
        if crete is not None and crete > CRETE_MAX:
            problemes.append(("a_revoir", f"crête du son à {crete:.1f} dBFS : risque de saturation"))
        if silence_debut > SILENCE_DEBUT_MAX:
            problemes.append(("a_revoir", f"{silence_debut:.1f} s de silence avant la voix : on perd le spectateur"))

    noirs, figees = mesurer_image(chemin)
    if noirs:
        problemes.append(("bloquant", "écran noir à " + ", ".join(f"{t:.1f} s" for t in noirs)))
    if figees:
        problemes.append(("a_revoir", "image figée à " + ", ".join(f"{t:.1f} s" for t in figees)))

    photos = [RACINE / p for p in json.loads(visuels or "[]")]
    if len(photos) < PHOTOS_MIN:
        problemes.append(("a_revoir", f"{len(photos)} photo(s) seulement, il en faut au moins {PHOTOS_MIN}"))
    empreintes = set()
    for photo in photos:
        if not photo.exists():
            problemes.append(("bloquant", f"photo introuvable : {photo.name}"))
            continue
        empreinte = hashlib.md5(photo.read_bytes()).hexdigest()
        if empreinte in empreintes:
            problemes.append(("a_revoir", f"photo en double : {photo.name}"))
        empreintes.add(empreinte)
        if taille_photo(photo) < LARGEUR_PHOTO_MIN:
            problemes.append(("a_revoir", f"photo trop petite, floue en plein écran : {photo.name}"))

    # Une balise d'émotion comme [excited] ne doit jamais apparaître dans les sous-titres
    fichier_mots = RACINE / audio.replace(".mp3", "_mots.json")
    if fichier_mots.exists():
        mots = json.loads(fichier_mots.read_text(encoding="utf-8"))
        balises = sorted({m["mot"] for m in mots if "[" in m["mot"] or "]" in m["mot"]})
        if balises:
            problemes.append(("bloquant", "balise d'émotion visible dans les sous-titres : " + ", ".join(balises)))
    return problemes


def main():
    base.creer_base()
    numeros = [int(n) for n in sys.argv[1:]]
    scripts = base.scripts_a_controler(numeros)
    if not scripts:
        print("Aucune vidéo n'attend son contrôle. Lance d'abord veille/hyperframes.py.")
        return

    for script_id, video, duree_voix, visuels, audio in scripts:
        problemes = controler(script_id, video, duree_voix, visuels, audio)
        verdict = "ok" if not problemes else ("bloquant" if any(g == "bloquant" for g, _ in problemes) else "a_revoir")
        base.enregistrer_controle(script_id, verdict, [f"{g} : {texte}" for g, texte in problemes])
        marque = {"ok": "OK", "a_revoir": "À REVOIR", "bloquant": "BLOQUÉE"}[verdict]
        print(f"Script {script_id} : {marque}  ({video})")
        for gravite, texte in problemes:
            print(f"   - {'bloquant' if gravite == 'bloquant' else 'à revoir'} : {texte}")

    print("\nSeules les vidéos OK sont prêtes à publier. Pour les autres, corrige puis relance ce contrôle.")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
