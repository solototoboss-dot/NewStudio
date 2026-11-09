# Mémoire des retours : ce que je dis après chaque vidéo, et ce que le studio a changé.
# C'est la skill /retour qui l'utilise, pour que le studio s'améliore à chaque montage.
#
# Lancement : python veille/retours.py voir
#             python veille/retours.py ajouter 2 "Sous-titres trop gros" "taille 92 -> 80"

import sys  # pour lire ce qui est donné au lancement

import base  # notre fichier base.py, dans le même dossier

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def voir():
    """Affiche les derniers retours, pour ne jamais défaire une ancienne demande sans le savoir."""
    retours = base.derniers_retours()
    if not retours:
        print("Aucun retour pour l'instant.")
    for numero, script_id, retour, changements, donne_le in retours:
        print(f"#{numero} ({donne_le[:10]}, script {script_id}) : {retour}")
        print(f"   -> {changements or 'aucun changement'}")


def main():
    base.creer_base()
    if len(sys.argv) >= 4 and sys.argv[1] == "ajouter":
        changements = sys.argv[4] if len(sys.argv) > 4 else ""
        base.enregistrer_retour(int(sys.argv[2]), sys.argv[3], changements)
        print("Retour enregistré.")
    else:
        voir()


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
