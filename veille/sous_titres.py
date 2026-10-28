# Crée les sous-titres au mot près de chaque script, au format .ass (lu par FFmpeg).
# Les mots s'affichent par petits groupes, et le mot en train d'être dit est mis en couleur,
# comme sur TikTok. Le minutage vient des fichiers script_<id>_mots.json créés par voix.py.

import json  # pour lire le minutage des mots
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
DOSSIER_AUDIO = RACINE / "data" / "audio"

# Réglages de chaque style de montage (vidéo verticale 1080 x 1920)
# Les couleurs ASS s'écrivent &HBBGGRR (bleu, vert, rouge : l'inverse de l'habitude)
STYLES = {
    # Gros mots, peu à la fois, mot actif en jaune : pour les vidéos rythmées
    "dynamique": {"mots_max": 3, "taille": 90, "couleur": "&H00FFFFFF", "actif": "&H0000E5FF",
                  "majuscules": True},
    # Plus de mots, plus petit, mot actif en bleu clair : pour les vidéos posées
    "explicatif": {"mots_max": 6, "taille": 70, "couleur": "&H00FFFFFF", "actif": "&H00FFD27A",
                   "majuscules": False},
}

# Une pause plus longue que ça entre deux mots commence un nouveau groupe
PAUSE_MAX = 0.6  # secondes

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def entete(reglages):
    """Renvoie le début du fichier .ass : taille de l'image et apparence du texte."""
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Defaut,Arial,{reglages['taille']},{reglages['couleur']},{reglages['couleur']},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,80,80,450,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def temps_ass(secondes):
    """Écrit un temps au format des sous-titres ASS : h:mm:ss.cc (centièmes)."""
    centiemes = round(secondes * 100)
    heures, centiemes = divmod(centiemes, 360000)
    minutes, centiemes = divmod(centiemes, 6000)
    secs, centiemes = divmod(centiemes, 100)
    return f"{heures}:{minutes:02d}:{secs:02d}.{centiemes:02d}"


def nettoyer(mot):
    """Enlève les caractères qui ont un sens spécial dans un fichier .ass."""
    return mot.replace("\\", "").replace("{", "").replace("}", "")


def former_groupes(mots, mots_max):
    """Coupe la liste des mots en petits groupes : à la fin d'une phrase, après une pause, ou quand c'est plein."""
    groupes, groupe = [], []
    for i, mot in enumerate(mots):
        if groupe and (len(groupe) >= mots_max or mot["debut"] - mots[i - 1]["fin"] > PAUSE_MAX):
            groupes.append(groupe)
            groupe = []
        groupe.append(mot)
        if mot["mot"][-1] in ".!?…":  # fin de phrase : on ferme le groupe
            groupes.append(groupe)
            groupe = []
    if groupe:
        groupes.append(groupe)
    return groupes


def lignes_dialogue(mots, reglages):
    """Crée une ligne de sous-titre par mot : le groupe entier, avec le mot dit en couleur."""
    lignes = []
    for groupe in former_groupes(mots, reglages["mots_max"]):
        for i, mot in enumerate(groupe):
            # Le mot reste en couleur jusqu'au début du mot suivant (pas de trou à l'écran)
            fin = groupe[i + 1]["debut"] if i + 1 < len(groupe) else mot["fin"]
            morceaux = []
            for autre in groupe:
                texte = nettoyer(autre["mot"])
                if reglages["majuscules"]:
                    texte = texte.upper()
                if autre is mot:
                    texte = f"{{\\c{reglages['actif']}}}{texte}{{\\c{reglages['couleur']}}}"
                morceaux.append(texte)
            lignes.append(f"Dialogue: 0,{temps_ass(mot['debut'])},{temps_ass(fin)},Defaut,,0,0,0,,"
                          + " ".join(morceaux))
    return lignes


def main():
    base.creer_base()
    scripts = base.scripts_sans_sous_titres()
    if not scripts:
        print("Aucun script n'attend ses sous-titres. Lance d'abord veille/voix.py.")
        return

    for script_id, style, audio in scripts:
        fichier_mots = DOSSIER_AUDIO / f"script_{script_id}_mots.json"
        if not fichier_mots.exists():
            print(f"Script {script_id} : minutage des mots introuvable, ignoré")
            continue
        with open(fichier_mots, encoding="utf-8") as fichier:
            mots = json.load(fichier)

        reglages = STYLES.get(style, STYLES["explicatif"])
        lignes = lignes_dialogue(mots, reglages)
        fichier_ass = DOSSIER_AUDIO / f"script_{script_id}.ass"
        with open(fichier_ass, "w", encoding="utf-8") as fichier:
            fichier.write(entete(reglages) + "\n".join(lignes) + "\n")

        base.enregistrer_sous_titres(script_id, str(fichier_ass.relative_to(RACINE)))
        print(f"Script {script_id} [{style}] : {len(mots)} mots, {len(lignes)} lignes de sous-titres")

    print("\nSous-titres dans data/audio/ (fichiers .ass)")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
