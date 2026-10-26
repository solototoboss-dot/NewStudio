# Range dans la base les notes données par Claude, puis garde le top 3 du jour.

import json  # pour lire le fichier des notes
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

FICHIER_SCORES = Path(__file__).parent.parent / "data" / "scores.json"

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def note_valide(note):
    """Vérifie qu'une note a un id, un score entier de 0 à 10 et une raison."""
    return (
        isinstance(note.get("id"), int)
        and isinstance(note.get("score"), int)
        and 0 <= note["score"] <= 10
        and isinstance(note.get("raison"), str)
    )


def main():
    with open(FICHIER_SCORES, encoding="utf-8") as fichier:
        notes = json.load(fichier)

    valides = [note for note in notes if note_valide(note)]
    if len(valides) < len(notes):
        print(f"Attention : {len(notes) - len(valides)} note(s) mal écrite(s) ignorée(s)")

    base.enregistrer_scores(valides)
    top = base.selectionner_top()

    print(f"{len(valides)} news notées. Top {len(top)} du jour :\n")
    if not top:
        print("Aucune news n'atteint 7/10 aujourd'hui.")
    for rang, (identifiant, source, titre, score, raison, lien) in enumerate(top, start=1):
        print(f"{rang}. [{score}/10] {titre} ({source})")
        print(f"   {raison}")
        print(f"   {lien}")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
