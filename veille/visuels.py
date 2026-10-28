# Télécharge une photo Pexels pour chaque idée d'image des scripts.
# Pexels : photos gratuites, usage commercial permis, sans obligation de citer (mais c'est apprécié).
# Une idée d'image peut commencer par des mots-clés anglais : « robot hand mouse : Curseur qui bouge seul ».
# Sinon, on cherche avec les premiers mots de la description en français.

import json  # pour lire les idées d'images et écrire les crédits
import os  # pour lire la clé Pexels
import re  # pour nettoyer les descriptions
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import requests  # pour appeler l'API Pexels et télécharger les photos
from dotenv import load_dotenv  # lit le fichier .env sans jamais l'afficher

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
DOSSIER_VISUELS = RACINE / "data" / "visuels"
FICHIER_CREDITS = DOSSIER_VISUELS / "credits.json"  # qui a pris chaque photo

load_dotenv(RACINE / ".env")  # la clé PEXELS_API_KEY est rangée dans le .env
API_PEXELS = "https://api.pexels.com/v1/search"

# Petits mots à ignorer dans une recherche en français
MOTS_VIDES = {"le", "la", "les", "un", "une", "des", "de", "du", "d", "l", "et", "ou", "à", "au",
              "aux", "en", "sur", "sous", "avec", "qui", "que", "dans", "par", "pour", "son", "sa",
              "ses", "texte", "écran", "plan", "fixe", "gros", "grand", "final", "finale"}

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def preparer_recherche(idee):
    """Transforme une idée d'image en recherche Pexels. Renvoie (recherche, langue)."""
    avant = idee.split(" : ")[0].strip()
    # Mots-clés anglais écrits avant « : » (sans accents ni apostrophe : sinon c'est du français)
    if " : " in idee and avant.isascii() and "'" not in avant:
        return avant, "en-US"
    idee = re.sub(r"«[^»]*»|\"[^\"]*\"", "", idee)  # on enlève les textes à afficher entre guillemets
    mots = [m for m in re.findall(r"[\wÀ-ÿ-]+", idee.lower()) if m not in MOTS_VIDES]
    return " ".join(mots[:5]), "fr-FR"


def chercher_photo(recherche, langue, deja_prises):
    """Cherche une photo verticale sur Pexels et renvoie la première qui n'est pas déjà utilisée."""
    reponse = requests.get(
        API_PEXELS,
        headers={"Authorization": os.environ["PEXELS_API_KEY"]},
        params={"query": recherche, "orientation": "portrait", "per_page": 8, "locale": langue},
        timeout=20,
    )
    reponse.raise_for_status()
    for photo in reponse.json().get("photos", []):
        if photo["id"] not in deja_prises:
            return photo
    return None


def telecharger(url, fichier):
    """Télécharge une image depuis une adresse web."""
    reponse = requests.get(url, timeout=60)
    reponse.raise_for_status()
    fichier.write_bytes(reponse.content)


def main():
    base.creer_base()
    if not os.getenv("PEXELS_API_KEY"):
        print("Clé PEXELS_API_KEY absente du fichier .env : crée-la sur pexels.com/api")
        return
    DOSSIER_VISUELS.mkdir(parents=True, exist_ok=True)
    credits = json.loads(FICHIER_CREDITS.read_text(encoding="utf-8")) if FICHIER_CREDITS.exists() else {}

    scripts = base.scripts_sans_visuels()
    if not scripts:
        print("Aucun script n'attend ses visuels.")
        return

    for script_id, images in scripts:
        chemins, deja_prises = [], set()
        for numero, idee in enumerate(json.loads(images or "[]"), start=1):
            recherche, langue = preparer_recherche(idee)
            if not recherche:  # idée sans mot utile (ex. un texte à afficher) : pas de photo
                continue
            try:
                photo = chercher_photo(recherche, langue, deja_prises)
            except requests.RequestException as erreur:
                print(f"   Script {script_id}, image {numero} : Pexels indisponible ({erreur})")
                continue
            if photo is None:
                print(f"   Script {script_id}, image {numero} : rien trouvé pour « {recherche} »")
                continue
            fichier = DOSSIER_VISUELS / f"script_{script_id}_{numero}.jpg"
            # « large2x » : grande taille, suffisante pour une vidéo 1080 x 1920
            telecharger(photo["src"]["large2x"], fichier)
            deja_prises.add(photo["id"])
            chemins.append(str(fichier.relative_to(RACINE)))
            credits[fichier.name] = {"photographe": photo["photographer"], "lien": photo["url"]}

        if chemins:
            base.enregistrer_visuels(script_id, chemins)
        print(f"Script {script_id} : {len(chemins)} image(s) téléchargée(s)")

    FICHIER_CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nImages dans data/visuels/ (crédits des photographes dans credits.json)")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
