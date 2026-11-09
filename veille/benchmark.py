# Benchmark du studio : mesure ce que la chaîne a réellement produit, avec des chiffres.
# Entonnoir des news, voix utilisées, qualité du son et de l'image, temps de montage, retours.
# Rien n'est modifié : la base est ouverte en lecture seule et aucune API payante n'est appelée.
#
# Lancement : python veille/benchmark.py                 -> données du dossier du projet
#             python veille/benchmark.py C:\...\NewStudio -> données d'un autre dossier (ex. depuis un worktree)
# Résultat  : docs/BENCHMARK.md

import json  # pour lire les réglages et les listes de photos
import re  # pour lire les heures dans le journal du matin
import sqlite3  # pour lire la base
import sys  # pour lire le dossier donné au lancement
from datetime import date, datetime  # pour dater le rapport et calculer des durées
from pathlib import Path  # pour trouver les fichiers

import controle  # on réutilise ses mesures FFmpeg (durée, volume, crête)

ICI = Path(__file__).parent
RAPPORT = ICI.parent / "docs" / "BENCHMARK.md"

# Prix indicatif du plan ElevenLabs Creator : 22 $ pour 100 000 caractères par mois
PRIX_PAR_CARACTERE = 22 / 100_000

sys.stdout.reconfigure(encoding="utf-8")


def ouvrir_base(racine):
    """Ouvre studio.db en lecture seule : le benchmark ne peut rien abîmer."""
    chemin = racine / "data" / "studio.db"
    if not chemin.exists():
        sys.exit(f"Base introuvable : {chemin}. Donne le dossier du projet en argument.")
    return sqlite3.connect(f"file:{chemin.as_posix()}?mode=ro", uri=True)


def compter(base, requete):
    """Renvoie le premier nombre d'une requête SQL."""
    return base.execute(requete).fetchone()[0] or 0


def entonnoir(base):
    """Combien de news et de scripts passent chaque étape de la chaîne."""
    verdicts = dict(base.execute(
        "SELECT verdict, COUNT(*) FROM verifications v "
        "WHERE id = (SELECT MAX(id) FROM verifications WHERE news_id = v.news_id) GROUP BY verdict"))
    controles = dict(base.execute("SELECT controle, COUNT(*) FROM scripts WHERE controle IS NOT NULL GROUP BY controle"))
    return [
        ("News collectées (flux RSS)", compter(base, "SELECT COUNT(*) FROM news")),
        ("News notées par Claude", compter(base, "SELECT COUNT(*) FROM news WHERE score IS NOT NULL")),
        ("News vérifiées", sum(verdicts.values())),
        ("  dont confirmées", verdicts.get("confirmee", 0)),
        ("  dont incertaines", verdicts.get("incertaine", 0)),
        ("  dont fausses", verdicts.get("fausse", 0)),
        ("Scripts écrits", compter(base, "SELECT COUNT(*) FROM scripts")),
        ("Scripts avec voix", compter(base, "SELECT COUNT(*) FROM scripts WHERE audio IS NOT NULL")),
        ("Scripts avec photos", compter(base, "SELECT COUNT(*) FROM scripts WHERE visuels IS NOT NULL")),
        ("Vidéos montées", compter(base, "SELECT COUNT(*) FROM scripts WHERE video IS NOT NULL")),
        ("Vidéos OK au contrôle", controles.get("ok", 0)),
        ("Vidéos à revoir", controles.get("a_revoir", 0)),
        ("Vidéos bloquées", controles.get("bloquant", 0)),
    ]


def voix(base):
    """Quel moteur de voix a parlé, combien de caractères et quel coût estimé."""
    lignes = base.execute(
        "SELECT voix, COUNT(*), SUM(LENGTH(texte)), SUM(duree) FROM scripts "
        "WHERE audio IS NOT NULL GROUP BY voix").fetchall()
    return [(v or "inconnue", n, caracteres or 0, duree or 0) for v, n, caracteres, duree in lignes]


def videos(base, racine):
    """Mesure chaque vidéo montée avec FFmpeg : format, durée, volume, crête, photos."""
    resultats = []
    for script_id, video, duree_voix, visuels, verdict in base.execute(
            "SELECT id, video, duree, visuels, controle FROM scripts WHERE video IS NOT NULL ORDER BY id"):
        chemin = racine / video
        if not chemin.exists():
            continue
        largeur, hauteur, ips, duree, _ = controle.mesurer_video(chemin)
        volume, crete, _ = controle.mesurer_son(chemin)
        resultats.append({
            "id": script_id, "format": f"{largeur}x{hauteur} à {ips} i/s", "duree": duree,
            "voix": duree_voix or 0, "volume": volume, "crete": crete,
            "photos": len(json.loads(visuels or "[]")), "taille": chemin.stat().st_size / 1_000_000,
            "verdict": verdict or "pas contrôlée",
        })
    return resultats


def temps_de_montage(racine):
    """Lit les journaux du matin : minutes entre le début du montage et le contrôle, par vidéo."""
    mesures = []
    for journal in sorted((racine / "data" / "journal").glob("matin_*.txt")):
        texte = journal.read_text(encoding="utf-8", errors="replace")
        # Un journal peut contenir plusieurs lancements : on ne garde que le dernier
        dernier = texte.split("=== Matin du")[-1]
        debut = re.search(r"--- Montage HyperFrames \((\d+:\d+)\)", dernier)
        fin = re.search(r"--- Contrôle qualité \((\d+:\d+)\)", dernier)
        nb = dernier.count("Vidéo prête")
        if debut and fin and nb:
            minutes = (datetime.strptime(fin.group(1), "%H:%M") - datetime.strptime(debut.group(1), "%H:%M")).seconds / 60
            mesures.append((journal.stem.replace("matin_", ""), nb, minutes))
    return mesures


def ecrire_rapport(etapes, moteurs, mesures, temps, nb_retours, nb_regles):
    """Écrit docs/BENCHMARK.md avec des tableaux Markdown."""
    l = [f"# Benchmark du studio", "", f"Mesuré le {date.today():%d/%m/%Y} par `veille/benchmark.py`, "
         "sur les données réelles du studio (aucune API payante appelée).", "",
         "## Entonnoir de la chaîne", "", "| Étape | Nombre |", "|---|---:|"]
    l += [f"| {nom} | {n} |" for nom, n in etapes]

    l += ["", "## Voix", "", "| Moteur | Scripts | Caractères | Minutes de voix | Coût estimé |", "|---|---:|---:|---:|---:|"]
    for moteur, n, caracteres, duree in moteurs:
        cout = f"{caracteres * PRIX_PAR_CARACTERE:.2f} $" if "eleven" in moteur.lower() else "gratuit"
        l.append(f"| {moteur} | {n} | {caracteres} | {duree / 60:.1f} | {cout} |")
    l += ["", "Coût ElevenLabs estimé au prix du plan Creator (22 $ pour 100 000 caractères)."]

    l += ["", "## Qualité des vidéos (mesurée par FFmpeg)", "",
          "| Script | Format | Durée | Écart avec la voix | Volume | Crête | Photos | Poids | Contrôle |",
          "|---:|---|---:|---:|---:|---:|---:|---:|---|"]
    for v in mesures:
        volume = f"{v['volume']:.1f} LUFS" if v["volume"] is not None else "?"
        crete = f"{v['crete']:.1f} dBFS" if v["crete"] is not None else "?"
        l.append(f"| {v['id']} | {v['format']} | {v['duree']:.1f} s | {v['duree'] - v['voix']:+.1f} s | {volume} | "
                 f"{crete} | {v['photos']} | {v['taille']:.0f} Mo | {v['verdict']} |")
    if mesures:
        moyenne = sum(v["volume"] for v in mesures if v["volume"] is not None) / max(1, sum(v["volume"] is not None for v in mesures))
        l += ["", f"Volume moyen : {moyenne:.1f} LUFS (cible des réseaux : -14 LUFS ±2,5)."]

    l += ["", "## Temps de production", "", "| Matin | Vidéos HyperFrames | Minutes | Minutes par vidéo |", "|---|---:|---:|---:|"]
    l += [f"| {jour} | {nb} | {minutes:.0f} | {minutes / nb:.1f} |" for jour, nb, minutes in temps]
    l += ["", "Repères mesurés pendant le développement : montage FFmpeg seul environ 1 min 45 par vidéo, "
          "HyperFrames environ 4 min (rendu dans Chrome, plus riche : sous-titres animés, emojis, sons)."]

    l += ["", "## Boucle d'amélioration", "", f"- Retours donnés avec /retour : {nb_retours}",
          f"- Règles de montage apprises (reglages_montage.json) : {nb_regles}", ""]
    RAPPORT.parent.mkdir(exist_ok=True)
    RAPPORT.write_text("\n".join(l), encoding="utf-8")


def main():
    racine = Path(sys.argv[1]) if len(sys.argv) > 1 else ICI.parent
    base = ouvrir_base(racine)
    etapes = entonnoir(base)
    moteurs = voix(base)
    mesures = videos(base, racine)
    nb_retours = compter(base, "SELECT COUNT(*) FROM retours")
    base.close()
    nb_regles = len(json.loads((ICI / "reglages_montage.json").read_text(encoding="utf-8")).get("regles_apprises", []))
    temps = temps_de_montage(racine)

    ecrire_rapport(etapes, moteurs, mesures, temps, nb_retours, nb_regles)
    for nom, n in etapes:
        print(f"{nom} : {n}")
    print(f"\n{len(mesures)} vidéo(s) mesurée(s). Rapport : {RAPPORT}")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
