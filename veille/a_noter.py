# Prépare la liste des news du jour que Claude doit noter.
# La liste est écrite dans data/a_noter.json, en version courte pour économiser le quota.

import json  # pour écrire le fichier JSON
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

FICHIER_A_NOTER = Path(__file__).parent.parent / "data" / "a_noter.json"


def main():
    base.creer_base()
    news = []
    for identifiant, source, titre, resume in base.news_a_noter():
        news.append({
            "id": identifiant,
            "source": source,
            "titre": titre,
            "resume": (resume or "")[:200],  # 200 caractères suffisent pour juger
        })

    with open(FICHIER_A_NOTER, "w", encoding="utf-8") as fichier:
        json.dump(news, fichier, ensure_ascii=False, indent=2)

    print(f"{len(news)} news à noter, écrites dans data/a_noter.json")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
