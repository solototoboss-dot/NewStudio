# Chaîne du matin : enchaîne toutes les étapes Python du studio, de la voix au contrôle qualité.
# Elle se lance après /veille et /scripts (ces deux étapes ont besoin de Claude).
# Tout ce qui s'affiche est aussi écrit dans un journal : data/journal/matin_<date>.txt
#
# Lancement : python veille/matin.py

import subprocess  # pour lancer chaque étape
import sys  # pour réutiliser le même Python (celui du .venv)
from datetime import date, datetime  # pour dater le journal
from pathlib import Path  # pour trouver les fichiers du projet

RACINE = Path(__file__).parent.parent
DOSSIER_JOURNAL = RACINE / "data" / "journal"

# Les étapes, dans l'ordre du studio. Chacune ne traite que ce qui l'attend, donc on peut tout relancer sans risque.
ETAPES = [
    ("Voix", "voix.py"),
    ("Photos", "visuels.py"),
    ("Sous-titres", "sous_titres.py"),
    ("Montage HyperFrames", "hyperframes.py"),
    ("Contrôle qualité", "controle.py"),
]

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def main():
    DOSSIER_JOURNAL.mkdir(parents=True, exist_ok=True)
    journal = DOSSIER_JOURNAL / f"matin_{date.today()}.txt"
    echecs = []

    with journal.open("a", encoding="utf-8") as fichier:
        def ecrire(texte):
            """Affiche une ligne et la garde dans le journal."""
            print(texte)
            fichier.write(texte + "\n")
            fichier.flush()

        ecrire(f"=== Matin du {date.today()}, début à {datetime.now():%H:%M} ===")
        for nom, script in ETAPES:
            ecrire(f"\n--- {nom} ({datetime.now():%H:%M}) ---")
            resultat = subprocess.run([sys.executable, str(Path(__file__).parent / script)], cwd=RACINE,
                                      capture_output=True, text=True, encoding="utf-8", errors="replace")
            ecrire((resultat.stdout + resultat.stderr).strip() or "(rien à faire)")
            if resultat.returncode != 0:
                echecs.append(nom)  # on note l'échec mais on continue : les autres étapes peuvent avancer
        ecrire(f"\n=== Fin à {datetime.now():%H:%M}. "
               f"{'Étapes en échec : ' + ', '.join(echecs) if echecs else 'Toutes les étapes ont tourné.'} ===")

    print(f"\nJournal : {journal.relative_to(RACINE)}")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
