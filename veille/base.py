# Base de données SQLite : range les news et évite les doublons.

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
            collectee_le TEXT                   -- quand le studio l'a récupérée
        )
    """)
    connexion.commit()
    connexion.close()


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
