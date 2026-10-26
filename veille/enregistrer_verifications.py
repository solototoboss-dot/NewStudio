# Range dans la base les verdicts de l'agent vérificateur.

import json  # pour lire le fichier des verdicts
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

FICHIER_VERIFICATIONS = Path(__file__).parent.parent / "data" / "verifications.json"

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")

# Le mot affiché pour chaque verdict
AFFICHAGE = {"confirmee": "CONFIRMÉE", "incertaine": "INCERTAINE", "fausse": "FAUSSE"}


def verdict_valide(verification):
    """Vérifie qu'un verdict a un id, un verdict connu, une liste de liens et une explication."""
    return (
        isinstance(verification.get("id"), int)
        and verification.get("verdict") in AFFICHAGE
        and isinstance(verification.get("preuves"), list)
        and isinstance(verification.get("explication"), str)
    )


def main():
    base.creer_base()
    with open(FICHIER_VERIFICATIONS, encoding="utf-8") as fichier:
        verifications = json.load(fichier)

    confirmees = 0
    for verification in verifications:
        if not verdict_valide(verification):
            print(f"Verdict mal écrit, ignoré : {verification}")
            continue

        base.enregistrer_verification(
            verification["id"], verification["verdict"],
            verification["preuves"], verification["explication"],
        )
        if verification["verdict"] == "confirmee":
            confirmees += 1

        print(f"#{verification['id']} {AFFICHAGE[verification['verdict']]} : {verification['explication']}")
        for lien in verification["preuves"]:
            print(f"   {lien}")

    print(f"\n{confirmees} news confirmée(s), prête(s) pour l'étape des scripts")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
