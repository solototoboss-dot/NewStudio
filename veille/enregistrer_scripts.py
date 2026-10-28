# Prépare les news confirmées pour l'écriture des scripts, puis range les scripts dans la base.
# - `python veille/enregistrer_scripts.py preparer` écrit la liste dans data/a_scripter.json
# - `python veille/enregistrer_scripts.py` lit data/scripts.json et range les scripts

import json  # pour lire et écrire les fichiers JSON
import sys  # pour lire l'argument "preparer" et régler l'affichage des accents
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

DOSSIER_DATA = Path(__file__).parent.parent / "data"
FICHIER_A_SCRIPTER = DOSSIER_DATA / "a_scripter.json"
FICHIER_SCRIPTS = DOSSIER_DATA / "scripts.json"

# La voix Edge TTS lit environ 2,8 mots par seconde (mesuré sur 12 scripts)
MOTS_PAR_SECONDE = 2.8
DUREE_MIN, DUREE_MAX = 45, 60  # durée visée d'une vidéo, en secondes
STYLES = ["dynamique", "explicatif"]  # les 2 styles de montage

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def preparer():
    """Écrit dans data/a_scripter.json les news confirmées qui attendent leurs scripts."""
    base.creer_base()
    news = []
    for identifiant, source, titre, resume, lien, explication, preuves in base.news_a_scripter():
        news.append({
            "id": identifiant, "source": source, "titre": titre, "lien": lien,
            "resume": resume or "",
            "verification": explication,  # les faits confirmés par le vérificateur
            "preuves": json.loads(preuves or "[]"),
        })
    with open(FICHIER_A_SCRIPTER, "w", encoding="utf-8") as fichier:
        json.dump(news, fichier, ensure_ascii=False, indent=2)
    print(f"{len(news)} news confirmée(s) à scripter, écrites dans data/a_scripter.json")


def script_valide(script):
    """Vérifie qu'un script a tous ses champs, un style connu et au moins une idée d'image."""
    return (
        isinstance(script.get("news_id"), int)
        and script.get("numero") in (1, 2, 3)
        and isinstance(script.get("angle"), str)
        and script.get("style") in STYLES
        and isinstance(script.get("texte"), str)
        and isinstance(script.get("images"), list)
        and len(script["images"]) > 0
    )


def duree_estimee(texte):
    """Estime en secondes le temps de lecture d'un texte par la voix."""
    return round(len(base.retirer_balises(texte).split()) / MOTS_PAR_SECONDE)


def enregistrer():
    """Lit data/scripts.json, vérifie chaque script et range les bons dans la base."""
    base.creer_base()
    with open(FICHIER_SCRIPTS, encoding="utf-8") as fichier:
        scripts = json.load(fichier)

    valides = []
    for script in scripts:
        if not script_valide(script):
            print(f"Script mal écrit, ignoré : {script.get('news_id')} n°{script.get('numero')}")
            continue
        valides.append(script)

        duree = duree_estimee(script["texte"])
        alerte = "" if DUREE_MIN <= duree <= DUREE_MAX else "  <- hors de 45 à 60 s"
        print(f"#{script['news_id']} n°{script['numero']} [{script['style']}] ~{duree} s : "
              f"{script['angle']}{alerte}")

    base.enregistrer_scripts(valides)
    print(f"\n{len(valides)} script(s) enregistré(s) sur {len(scripts)}")


# Ce bloc lance le bon travail seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preparer":
        preparer()
    else:
        enregistrer()
