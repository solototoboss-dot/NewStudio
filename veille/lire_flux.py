# Lit les flux RSS de nos sources et range les news dans la base SQLite.

import json  # pour lire le fichier sources.json
import re  # pour retirer les balises HTML des résumés
from datetime import datetime, timezone  # pour convertir les dates
from pathlib import Path  # pour trouver les fichiers, peu importe d'où on lance le script

import feedparser  # bibliothèque qui sait lire les flux RSS

import base  # notre fichier base.py, dans le même dossier

# sources.json est rangé dans le même dossier que ce script
DOSSIER = Path(__file__).parent
FICHIER_SOURCES = DOSSIER / "sources.json"

NB_NEWS = 20  # nombre maximum de news lues par source


def charger_sources():
    """Ouvre sources.json et renvoie la liste des sources."""
    with open(FICHIER_SOURCES, encoding="utf-8") as fichier:
        donnees = json.load(fichier)
    return donnees["sources"]


def date_iso(entree):
    """Transforme la date du flux en texte standard (ISO), ou None si elle manque."""
    date = entree.get("published_parsed") or entree.get("updated_parsed")
    if not date:
        return None
    return datetime(*date[:6], tzinfo=timezone.utc).isoformat()


def nettoyer(texte):
    """Retire les balises HTML et coupe le texte à 500 caractères."""
    return re.sub(r"<[^>]+>", "", texte or "").strip()[:500]


def lire_flux(source):
    """Télécharge le flux d'une source et renvoie ses dernières news."""
    flux = feedparser.parse(source["flux"])
    news = []
    for entree in flux.entries[:NB_NEWS]:
        news.append({
            "source": source["nom"],
            "titre": entree.get("title", "(sans titre)"),
            "lien": entree.get("link", ""),
            "date": date_iso(entree),
            "resume": nettoyer(entree.get("summary")),
        })
    return news


def main():
    base.creer_base()
    sources = charger_sources()
    total = 0

    for source in sources:
        try:
            news = lire_flux(source)
        except Exception as erreur:
            # Une source en panne ne doit pas arrêter toute la veille
            print(f"{source['nom']} : erreur ({erreur})")
            continue

        if not news:
            print(f"{source['nom']} : aucune news (flux injoignable ?)")
            continue

        nouvelles = base.enregistrer_news(news)
        total += nouvelles
        print(f"{source['nom']} : {len(news)} news lues, {nouvelles} nouvelles")

    print(f"\nTotal : {total} nouvelles news enregistrées")

    print("\nNews des dernières 24 heures, par source :")
    for nom, nombre in base.compter_par_source():
        print(f"- {nom} : {nombre}")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
