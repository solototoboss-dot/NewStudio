# Recherche web avec l'API Search de Perplexity, pour trouver les news
# que les flux RSS ne couvrent pas (Anthropic, Meta, annonces de dernière minute).

import json  # pour lire sources.json
import os  # pour lire la clé une fois chargée
from pathlib import Path  # pour trouver les fichiers du projet

import requests  # pour envoyer des requêtes à une API sur Internet
from dotenv import load_dotenv  # pour lire la clé rangée dans .env

DOSSIER = Path(__file__).parent
FICHIER_SOURCES = DOSSIER / "sources.json"
URL_API = "https://api.perplexity.ai/search"

# Charge les variables du fichier .env, à la racine du projet
load_dotenv(DOSSIER.parent / ".env")


def charger_recherches():
    """Renvoie la liste des recherches écrites dans sources.json."""
    with open(FICHIER_SOURCES, encoding="utf-8") as fichier:
        donnees = json.load(fichier)
    return donnees["recherches_web"]


def aplatir(resultats):
    """Met tous les résultats dans une seule liste, même s'ils arrivent groupés par recherche."""
    liste = []
    for element in resultats:
        if isinstance(element, list):
            liste.extend(element)
        else:
            liste.append(element)
    return liste


def chercher(recherches, cle):
    """Envoie jusqu'à 5 recherches en UNE seule requête, facturée une seule fois."""
    reponse = requests.post(
        URL_API,
        headers={"Authorization": f"Bearer {cle}"},
        json={
            "query": recherches[:5],         # 5 recherches maximum par requête
            "max_results": 10,               # 10 résultats par recherche
            "search_recency_filter": "day",  # seulement les dernières 24 heures
            "max_tokens_per_page": 256,      # des extraits courts
        },
        timeout=60,
    )
    reponse.raise_for_status()  # déclenche une erreur si l'API répond mal
    return aplatir(reponse.json().get("results", []))


def main():
    cle = os.getenv("PERPLEXITY_API_KEY")
    if not cle:
        print("Pas de clé PERPLEXITY_API_KEY dans .env : recherche web ignorée.")
        return

    recherches = charger_recherches()
    print(f"Recherche web : {len(recherches)} recherches envoyées à Perplexity\n")

    try:
        resultats = chercher(recherches, cle)
    except requests.RequestException as erreur:
        print(f"Erreur de l'API : {erreur}")
        return

    # Un même article peut sortir dans plusieurs recherches : on garde chaque lien une seule fois
    deja_vus = set()
    for resultat in resultats:
        lien = resultat.get("url", "")
        if lien in deja_vus:
            continue
        deja_vus.add(lien)
        print(f"- {resultat.get('title', '(sans titre)')}")
        print(f"  {resultat.get('date') or 'date inconnue'}")
        print(f"  {lien}")

    print(f"\n{len(deja_vus)} résultats uniques")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
