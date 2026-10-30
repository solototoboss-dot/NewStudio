# Crée les sous-titres animés au mot près de chaque script, au format .ass (lu par FFmpeg).
# Style des outils pros (Submagic, CapCut, style « Hormozi ») :
# - les mots arrivent par petits groupes, avec une petite animation d'entrée ;
# - le mot en train d'être dit « saute » (il grossit puis se pose) et change de couleur ;
# - en style dynamique, une boîte de couleur passe derrière le mot dit.
# Le minutage vient des fichiers script_<id>_mots.json créés par voix.py.

import json  # pour lire le minutage des mots
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
DOSSIER_AUDIO = RACINE / "data" / "audio"
# Les polices du projet (Montserrat, licence libre OFL) : à donner à FFmpeg avec fontsdir
DOSSIER_POLICES = RACINE / "assets" / "polices"

# Réglages de chaque style de montage (vidéo verticale 1080 x 1920)
# Les couleurs ASS s'écrivent &HAABBGGRR : transparence, bleu, vert, rouge (l'inverse de l'habitude)
STYLES = {
    # Gros mots en majuscules, 3 au maximum, boîte vert-jaune derrière le mot dit : pour les vidéos rythmées
    "dynamique": {
        "police": "Montserrat ExtraBold", "taille": 96, "mots_max": 3, "majuscules": True,
        "couleur": "&H00FFFFFF",       # blanc
        "actif": "&H00000000",         # mot dit en noir, sur la boîte
        "boite": "&H0033F0B4",         # boîte vert-jaune (#B4F033)
        "a_venir": "&H00",             # les mots pas encore dits restent bien visibles
        "pop": 120,                    # le mot dit grossit jusqu'à 120 %...
        "pose": 110,                   # ...puis se pose à 110 %
    },
    # Phrase plus longue, mots à venir en transparence, mot dit en bleu clair : pour les vidéos posées
    "explicatif": {
        "police": "Montserrat ExtraBold", "taille": 74, "mots_max": 5, "majuscules": False,
        "couleur": "&H00FFFFFF",       # blanc
        "actif": "&H00FFD27A",         # bleu clair (#7AD2FF)
        "boite": None,                 # pas de boîte, plus sobre
        "a_venir": "&H45",             # les mots pas encore dits sont un peu transparents (lisibles sur photo)
        "pop": 110,
        "pose": 104,
    },
}

POSITION_BAS = 620  # distance du bas de l'image : au-dessus des boutons de TikTok, Reels et Shorts
PAUSE_MAX = 0.6  # une pause plus longue que ça (en secondes) commence un nouveau groupe
DUREE_POP = 80  # durée du « saut » du mot dit, en millisecondes
DUREE_ENTREE = 120  # durée de l'animation d'arrivée d'un groupe, en millisecondes

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def entete(reglages):
    """Renvoie le début du fichier .ass : taille de l'image et apparence du texte."""
    police, taille, couleur = reglages["police"], reglages["taille"], reglages["couleur"]
    boite = reglages["boite"] or "&H00000000"
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Texte,{police},{taille},{couleur},{couleur},&H00000000,&H96000000,0,0,0,0,100,100,2,0,1,7,4,2,70,70,{POSITION_BAS},1
Style: Boite,{police},{taille},&HFF000000,&HFF000000,{boite},&HFF000000,0,0,0,0,100,100,2,0,3,11,0,2,70,70,{POSITION_BAS},1

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


def nettoyer(mot, reglages):
    """Enlève les caractères spéciaux du format .ass et met en majuscules si le style le demande."""
    mot = mot.replace("\\", "").replace("{", "").replace("}", "")
    return mot.upper() if reglages["majuscules"] else mot


def former_groupes(mots, mots_max):
    """Coupe la liste des mots en petits groupes : à la fin d'une phrase, après une pause, ou quand c'est plein."""
    groupes, groupe = [], []
    for i, mot in enumerate(mots):
        if groupe and (len(groupe) >= mots_max or mot["debut"] - mots[i - 1]["fin"] > PAUSE_MAX):
            groupes.append(groupe)
            groupe = []
        groupe.append(mot)
        if mot["mot"][-1] in ".!?…:":  # fin de phrase : on ferme le groupe
            groupes.append(groupe)
            groupe = []
    if groupe:
        groupes.append(groupe)
    return groupes


def animation_pop(reglages):
    """Balises qui font « sauter » un mot : il grossit vite, puis se pose un peu plus gros que les autres."""
    pop, pose = reglages["pop"], reglages["pose"]
    return (f"\\fscx100\\fscy100\\t(0,{DUREE_POP},\\fscx{pop}\\fscy{pop})"
            f"\\t({DUREE_POP},{DUREE_POP * 2},\\fscx{pose}\\fscy{pose})")


def texte_ligne(groupe, actif, reglages, pour_boite):
    """Écrit le texte d'un groupe quand le mot n°`actif` est dit.
    pour_boite=True : seule la boîte du mot dit est visible (calque du dessous)."""
    morceaux = []
    for i, mot in enumerate(groupe):
        texte = nettoyer(mot["mot"], reglages)
        if pour_boite:
            # Tout est invisible sauf la boîte derrière le mot dit
            alpha_boite = "&H00&" if i == actif else "&HFF&"
            balises = f"\\1a&HFF&\\3a{alpha_boite}"
        elif i == actif:
            balises = f"\\1a&H00&\\c{reglages['actif']}"
            if reglages["boite"]:
                balises += "\\bord0\\shad0"  # sur la boîte, pas besoin de contour
        elif i < actif:
            balises = f"\\1a&H00&\\c{reglages['couleur']}\\bord7\\shad4"  # mot déjà dit
        else:
            balises = f"\\1a{reglages['a_venir']}&\\c{reglages['couleur']}\\bord7\\shad4"  # mot à venir
        if i == actif:
            balises += animation_pop(reglages)
        else:
            balises += "\\fscx100\\fscy100"
        morceaux.append(f"{{{balises}}}{texte}")
    return " ".join(morceaux)


def lignes_dialogue(mots, reglages):
    """Crée les lignes de sous-titres : une par mot dit, avec le groupe entier à l'écran."""
    lignes = []
    groupes = former_groupes(mots, reglages["mots_max"])
    for n, groupe in enumerate(groupes):
        # Le dernier mot d'un groupe reste un peu à l'écran, mais jamais après l'arrivée du groupe suivant
        limite = groupes[n + 1][0]["debut"] if n + 1 < len(groupes) else float("inf")
        for i, mot in enumerate(groupe):
            # Le mot reste actif jusqu'au début du mot suivant (pas de trou à l'écran)
            fin = groupe[i + 1]["debut"] if i + 1 < len(groupe) else min(mot["fin"] + 0.3, limite)
            debut, fin = temps_ass(mot["debut"]), temps_ass(fin)
            # Quand un nouveau groupe arrive, il apparaît en fondu en montant un peu
            x, y = 540, 1920 - POSITION_BAS
            mouvement = (f"\\move({x},{y + 30},{x},{y},0,{DUREE_ENTREE})\\fad({DUREE_ENTREE},0)"
                         if i == 0 else f"\\pos({x},{y})")
            entree = f"{{{mouvement}}}"
            if reglages["boite"]:
                lignes.append(f"Dialogue: 0,{debut},{fin},Boite,,0,0,0,,{entree}"
                              + texte_ligne(groupe, i, reglages, pour_boite=True))
            lignes.append(f"Dialogue: 1,{debut},{fin},Texte,,0,0,0,,{entree}"
                          + texte_ligne(groupe, i, reglages, pour_boite=False))
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
