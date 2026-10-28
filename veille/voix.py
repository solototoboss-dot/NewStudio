# Transforme chaque script en voix.
# Voix principale : ElevenLabs (modèle eleven_v4), très réaliste, qui comprend les balises
# d'émotion comme [excited]. Voix de secours : Edge TTS (gratuit, sans clé), utilisée si la clé
# manque ou si ElevenLabs refuse (quota épuisé, pas d'internet...).
# Pour chaque script : un fichier MP3 et la liste des mots avec leur moment exact,
# qui servira aux sous-titres au mot près (semaine 6).

import asyncio  # edge-tts travaille en "asynchrone" : on attend la voix sans bloquer
import base64  # ElevenLabs renvoie le son encodé en texte (base64)
import json  # pour écrire le minutage des mots
import os  # pour savoir si la clé ElevenLabs est présente
import sys  # pour régler l'affichage des accents dans le terminal
from pathlib import Path  # pour trouver les fichiers du projet

import edge_tts  # la voix de Microsoft Edge
from dotenv import load_dotenv  # lit le fichier .env sans jamais l'afficher
from elevenlabs import ElevenLabs, VoiceSettings  # la voix d'ElevenLabs

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
DOSSIER_AUDIO = RACINE / "data" / "audio"

# La clé ELEVENLABS_API_KEY est rangée dans le .env : la bibliothèque la lit toute seule
load_dotenv(RACINE / ".env")

# ElevenLabs : une voix française native de la bibliothèque publique
ELEVENLABS_VOIX_ID = "aQROLel5sQbj1vuIVi6B"  # Nicolas - Narrator, accent parisien
ELEVENLABS_VOIX_NOM = "Nicolas"
ELEVENLABS_MODELE = "eleven_v4"  # le modèle le plus expressif, qui comprend les balises d'émotion
# Stabilité basse = plus d'émotion ; similarité haute = reste fidèle à la voix d'origine
ELEVENLABS_REGLAGES = VoiceSettings(stability=0.4, similarity_boost=0.75)

# Edge TTS : la voix de secours
EDGE_VOIX = "fr-FR-HenriNeural"
EDGE_VITESSE = "+0%"  # vitesse normale de la voix

# Edge TTS compte le temps en "ticks" de 100 nanosecondes : 10 millions par seconde
TICKS_PAR_SECONDE = 10_000_000

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def voix_elevenlabs(texte, fichier_audio):
    """Crée la voix avec ElevenLabs et renvoie la liste des mots avec leur début et leur fin."""
    client = ElevenLabs()
    reponse = client.text_to_speech.convert_with_timestamps(
        ELEVENLABS_VOIX_ID,
        text=texte,
        model_id=ELEVENLABS_MODELE,
        language_code="fr",
        voice_settings=ELEVENLABS_REGLAGES,
    )
    with open(fichier_audio, "wb") as fichier:
        fichier.write(base64.b64decode(reponse.audio_base_64))

    # ElevenLabs donne le moment de chaque lettre : on les regroupe en mots
    alignement = reponse.alignment
    mots, mot, debut, fin = [], "", None, None
    dans_balise = False  # vrai quand on est entre [ et ], une balise qui n'est pas prononcée
    for lettre, t_debut, t_fin in zip(alignement.characters,
                                      alignement.character_start_times_seconds,
                                      alignement.character_end_times_seconds):
        if lettre == "[":
            dans_balise = True
        if dans_balise or lettre.isspace():
            # Fin d'un mot : on le garde s'il contient au moins une lettre ou un chiffre
            if any(c.isalnum() for c in mot):
                mots.append({"mot": mot, "debut": round(debut, 3), "fin": round(fin, 3)})
            mot, debut = "", None
            if lettre == "]":
                dans_balise = False
            continue
        if debut is None:
            debut = t_debut
        mot += lettre
        fin = t_fin
    if any(c.isalnum() for c in mot):
        mots.append({"mot": mot, "debut": round(debut, 3), "fin": round(fin, 3)})
    return mots


async def voix_edge(texte, fichier_audio):
    """Crée la voix avec Edge TTS et renvoie la liste des mots avec leur début et leur fin."""
    # Edge TTS ne comprend pas les balises d'émotion : on les enlève pour qu'il ne les lise pas
    communication = edge_tts.Communicate(base.retirer_balises(texte), EDGE_VOIX,
                                         rate=EDGE_VITESSE, boundary="WordBoundary")
    mots = []
    with open(fichier_audio, "wb") as fichier:
        # Edge TTS envoie des morceaux : soit du son, soit l'annonce d'un mot prononcé
        async for morceau in communication.stream():
            if morceau["type"] == "audio":
                fichier.write(morceau["data"])
            elif morceau["type"] == "WordBoundary":
                debut = morceau["offset"] / TICKS_PAR_SECONDE
                fin = (morceau["offset"] + morceau["duration"]) / TICKS_PAR_SECONDE
                mots.append({"mot": morceau["text"], "debut": round(debut, 3), "fin": round(fin, 3)})
    return mots


def creer_voix(texte, fichier_audio):
    """Essaie ElevenLabs, puis Edge TTS en secours. Renvoie (mots, nom de la voix utilisée)."""
    if os.getenv("ELEVENLABS_API_KEY"):
        try:
            return voix_elevenlabs(texte, fichier_audio), f"elevenlabs:{ELEVENLABS_VOIX_NOM}"
        except Exception as erreur:  # quota épuisé, clé refusée, pas d'internet...
            print(f"   ElevenLabs indisponible ({str(erreur)[:120]}), passage à Edge TTS")
    mots = asyncio.run(voix_edge(texte, fichier_audio))
    return mots, f"edge:{EDGE_VOIX}"


def main():
    base.creer_base()
    DOSSIER_AUDIO.mkdir(parents=True, exist_ok=True)
    scripts = base.scripts_sans_voix()
    if not scripts:
        print("Aucun script n'attend sa voix. Lance d'abord /scripts.")
        return

    for script_id, news_id, numero, texte in scripts:
        fichier_audio = DOSSIER_AUDIO / f"script_{script_id}.mp3"
        fichier_mots = DOSSIER_AUDIO / f"script_{script_id}_mots.json"
        try:
            mots, voix = creer_voix(texte, fichier_audio)
        except Exception as erreur:  # les deux voix ont échoué, par exemple sans internet
            print(f"Script {script_id} : échec de la voix ({erreur})")
            continue

        with open(fichier_mots, "w", encoding="utf-8") as fichier:
            json.dump(mots, fichier, ensure_ascii=False, indent=2)

        # La durée réelle de la voix, c'est la fin du dernier mot prononcé
        duree = mots[-1]["fin"] if mots else 0
        base.enregistrer_voix(script_id, str(fichier_audio.relative_to(RACINE)), duree, voix)
        alerte = "" if 45 <= duree <= 60 else "  <- hors de 45 à 60 s"
        print(f"Script {script_id} (news #{news_id}, n°{numero}) : {voix}, {duree:.1f} s, "
              f"{len(mots)} mots{alerte}")

    print("\nFichiers audio dans data/audio/")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
