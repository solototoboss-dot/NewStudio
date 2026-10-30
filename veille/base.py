# Base de données SQLite : range les news et évite les doublons.

import json  # pour ranger la liste des preuves
import sqlite3  # SQLite est inclus dans Python, rien à installer
from datetime import datetime, timedelta, timezone  # pour les dates
from pathlib import Path  # pour trouver les fichiers du projet

# La base est rangée dans le dossier data/, à la racine du projet
FICHIER_BASE = Path(__file__).parent.parent / "data" / "studio.db"


def connecter():
    """Ouvre la base, et crée le dossier data/ s'il n'existe pas."""
    FICHIER_BASE.parent.mkdir(exist_ok=True)
    return sqlite3.connect(FICHIER_BASE)


def creer_base():
    """Crée la table news si elle n'existe pas encore."""
    connexion = connecter()
    connexion.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            source       TEXT NOT NULL,
            titre        TEXT NOT NULL,
            lien         TEXT NOT NULL UNIQUE,  -- UNIQUE : un même lien ne peut pas entrer deux fois
            date         TEXT,                  -- date de publication
            resume       TEXT,
            statut       TEXT DEFAULT 'nouvelle',
            collectee_le TEXT,                  -- quand le studio l'a récupérée
            score        INTEGER,               -- note de Claude, de 0 à 10
            raison       TEXT                   -- pourquoi cette note
        )
    """)
    # Si la base a été créée avant l'ajout des notes, on ajoute les colonnes manquantes
    ajouter_colonne(connexion, "score", "INTEGER")
    ajouter_colonne(connexion, "raison", "TEXT")

    # Table des vérifications : le verdict de l'agent vérificateur pour chaque news du top
    connexion.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id      INTEGER NOT NULL,  -- le numéro de la news vérifiée
            verdict      TEXT NOT NULL,     -- confirmee, incertaine ou fausse
            preuves      TEXT,              -- les liens des sources, au format JSON
            explication  TEXT,
            verifiee_le  TEXT
        )
    """)

    # Table des scripts : les textes de 45 à 60 secondes écrits pour chaque news confirmée
    connexion.execute("""
        CREATE TABLE IF NOT EXISTS scripts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id    INTEGER NOT NULL,  -- le numéro de la news racontée
            numero     INTEGER NOT NULL,  -- 1, 2 ou 3 : la version du script
            angle      TEXT,              -- l'idée principale de cette version
            style      TEXT NOT NULL,     -- le style de montage : dynamique ou explicatif
            texte      TEXT NOT NULL,     -- ce que la voix va lire
            images     TEXT,              -- les idées d'images, au format JSON
            mots       INTEGER,           -- nombre de mots du texte
            ecrit_le   TEXT,
            audio      TEXT,              -- chemin du fichier MP3 de la voix
            duree      REAL,              -- vraie durée du fichier audio, en secondes
            voix       TEXT,              -- la voix utilisée, ex. edge:fr-FR-HenriNeural
            vitesse    TEXT               -- le réglage de vitesse gardé, ex. -4%
        )
    """)
    # Si la table scripts a été créée avant l'ajout de la voix, on ajoute les colonnes manquantes
    ajouter_colonne(connexion, "audio", "TEXT", table="scripts")
    ajouter_colonne(connexion, "duree", "REAL", table="scripts")
    ajouter_colonne(connexion, "voix", "TEXT", table="scripts")
    ajouter_colonne(connexion, "vitesse", "TEXT", table="scripts")
    connexion.commit()
    connexion.close()


def ajouter_colonne(connexion, nom, type_sql, table="news"):
    """Ajoute une colonne à une table (news par défaut) si elle n'existe pas encore."""
    colonnes = [ligne[1] for ligne in connexion.execute(f"PRAGMA table_info({table})")]
    if nom not in colonnes:
        connexion.execute(f"ALTER TABLE {table} ADD COLUMN {nom} {type_sql}")


def maintenant():
    """Renvoie l'heure actuelle en UTC, au format texte standard (ISO)."""
    return datetime.now(timezone.utc).isoformat()


def enregistrer_news(news):
    """Ajoute les news dans la base et renvoie combien étaient vraiment nouvelles."""
    connexion = connecter()
    for article in news:
        # INSERT OR IGNORE : si le lien existe déjà, la ligne est simplement ignorée
        connexion.execute(
            "INSERT OR IGNORE INTO news (source, titre, lien, date, resume, collectee_le) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (article["source"], article["titre"], article["lien"],
             article["date"], article["resume"], maintenant()),
        )
    nouvelles = connexion.total_changes  # nombre de lignes vraiment ajoutées
    connexion.commit()
    connexion.close()
    return nouvelles


def depuis_24h():
    """Renvoie la date et l'heure d'il y a 24 heures, au format ISO."""
    return (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()


def news_du_jour():
    """Renvoie les news des dernières 24 heures, de la plus récente à la plus ancienne."""
    connexion = connecter()
    lignes = connexion.execute(
        "SELECT source, titre, lien, date FROM news "
        "WHERE COALESCE(date, collectee_le) >= ? "
        "ORDER BY COALESCE(date, collectee_le) DESC",
        (depuis_24h(),),
    ).fetchall()
    connexion.close()
    return lignes


def compter_par_source():
    """Renvoie le nombre de news des dernières 24 heures, source par source."""
    connexion = connecter()
    lignes = connexion.execute(
        "SELECT source, COUNT(*) FROM news "
        "WHERE COALESCE(date, collectee_le) >= ? "
        "GROUP BY source ORDER BY COUNT(*) DESC",
        (depuis_24h(),),
    ).fetchall()
    connexion.close()
    return lignes


def news_a_noter():
    """Renvoie les news des dernières 24 heures que Claude n'a pas encore notées."""
    connexion = connecter()
    lignes = connexion.execute(
        "SELECT id, source, titre, resume FROM news "
        "WHERE statut = 'nouvelle' AND COALESCE(date, collectee_le) >= ? "
        "ORDER BY COALESCE(date, collectee_le) DESC",
        (depuis_24h(),),
    ).fetchall()
    connexion.close()
    return lignes


def enregistrer_scores(notes):
    """Range la note et la raison de chaque news, puis la marque comme notée."""
    connexion = connecter()
    for note in notes:
        connexion.execute(
            "UPDATE news SET score = ?, raison = ?, statut = 'notee' WHERE id = ?",
            (note["score"], note["raison"], note["id"]),
        )
    connexion.commit()
    connexion.close()


def selectionner_top(nombre=3, minimum=7):
    """Garde les meilleures news notées (au moins `minimum`/10) et écarte les autres."""
    connexion = connecter()
    top = connexion.execute(
        "SELECT id, source, titre, score, raison, lien FROM news "
        "WHERE statut = 'notee' AND score >= ? "
        "ORDER BY score DESC, COALESCE(date, collectee_le) DESC LIMIT ?",
        (minimum, nombre),
    ).fetchall()
    for ligne in top:
        connexion.execute("UPDATE news SET statut = 'selectionnee' WHERE id = ?", (ligne[0],))
    # Toutes les autres news notées sont écartées
    connexion.execute("UPDATE news SET statut = 'ecartee' WHERE statut = 'notee'")
    connexion.commit()
    connexion.close()
    return top


def news_selectionnees():
    """Renvoie les news du top qui attendent encore leur vérification."""
    connexion = connecter()
    lignes = connexion.execute(
        "SELECT id, source, titre, lien FROM news WHERE statut = 'selectionnee' "
        "ORDER BY score DESC"
    ).fetchall()
    connexion.close()
    return lignes


# Le statut que prend une news selon le verdict du vérificateur
STATUT_SELON_VERDICT = {"confirmee": "verifiee", "incertaine": "incertaine", "fausse": "rejetee"}


def enregistrer_verification(news_id, verdict, preuves, explication):
    """Range le verdict du vérificateur et met à jour le statut de la news."""
    connexion = connecter()
    connexion.execute(
        "INSERT INTO verifications (news_id, verdict, preuves, explication, verifiee_le) "
        "VALUES (?, ?, ?, ?, ?)",
        (news_id, verdict, json.dumps(preuves), explication, maintenant()),
    )
    connexion.execute(
        "UPDATE news SET statut = ? WHERE id = ?",
        (STATUT_SELON_VERDICT[verdict], news_id),
    )
    connexion.commit()
    connexion.close()


def news_a_scripter():
    """Renvoie les news confirmées qui n'ont pas encore de scripts, avec leur dernière vérification."""
    connexion = connecter()
    lignes = connexion.execute(
        "SELECT news.id, news.source, news.titre, news.resume, news.lien, "
        "verifications.explication, verifications.preuves "
        "FROM news JOIN verifications ON verifications.news_id = news.id "
        "WHERE news.statut = 'verifiee' "
        # On garde seulement la vérification la plus récente de chaque news
        "AND verifications.id = (SELECT MAX(id) FROM verifications WHERE news_id = news.id) "
        "ORDER BY news.score DESC"
    ).fetchall()
    connexion.close()
    return lignes


def enregistrer_scripts(scripts):
    """Range les scripts d'une liste et marque leurs news comme scriptées."""
    connexion = connecter()
    for script in scripts:
        connexion.execute(
            "INSERT INTO scripts (news_id, numero, angle, style, texte, images, mots, ecrit_le) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (script["news_id"], script["numero"], script["angle"], script["style"],
             script["texte"], json.dumps(script["images"], ensure_ascii=False),
             len(script["texte"].split()), maintenant()),
        )
        connexion.execute("UPDATE news SET statut = 'scriptee' WHERE id = ?", (script["news_id"],))
    connexion.commit()
    connexion.close()


def audio_present(chemin):
    """Dit si un fichier audio existe et n'est pas vide. Le chemin part de la racine du projet."""
    if not chemin:
        return False
    fichier = FICHIER_BASE.parent.parent / chemin
    return fichier.is_file() and fichier.stat().st_size > 0


def scripts_sans_voix():
    """Renvoie les scripts dont le fichier audio n'est pas noté, manque ou est vide."""
    connexion = connecter()
    lignes = connexion.execute(
        "SELECT id, news_id, numero, texte, audio FROM scripts ORDER BY id"
    ).fetchall()
    connexion.close()
    return [ligne[:4] for ligne in lignes if not audio_present(ligne[4])]


def enregistrer_voix(script_id, audio, duree, voix, vitesse):
    """Range le chemin du fichier audio, sa durée, la voix et la vitesse d'un script."""
    connexion = connecter()
    connexion.execute(
        "UPDATE scripts SET audio = ?, duree = ?, voix = ?, vitesse = ? WHERE id = ?",
        (audio, duree, voix, vitesse, script_id),
    )
    connexion.commit()
    connexion.close()


def scripts_avec_voix():
    """Renvoie le bilan des scripts qui ont leur audio : numéro, fichier, durée et vitesse."""
    connexion = connecter()
    lignes = connexion.execute(
        "SELECT id, audio, duree, vitesse FROM scripts WHERE audio IS NOT NULL ORDER BY id"
    ).fetchall()
    connexion.close()
    return lignes
