# Monte la vidéo finale de chaque script avec HyperFrames (HeyGen, gratuit et open source) :
# une page web animée (photos, sous-titres, emojis, effets sonores) que HyperFrames filme dans Chrome.
# Tous les choix de montage sont dans veille/reglages_montage.json, que la skill /retour fait évoluer.
#
# Lancement : python veille/hyperframes.py        -> monte les scripts qui n'ont pas encore de vidéo
#             python veille/hyperframes.py 2 5    -> remonte les scripts 2 et 5 (après un retour)

import html  # pour écrire le texte sans casser la page web
import json  # pour lire les réglages, les images et le minutage des mots
import shutil  # pour copier les fichiers et trouver la commande npx
import subprocess  # pour lancer HyperFrames
import sys  # pour lire les numéros de scripts donnés au lancement
import unicodedata  # pour enlever les accents des mots
from pathlib import Path  # pour trouver les fichiers du projet

import base  # notre fichier base.py, dans le même dossier

RACINE = Path(__file__).parent.parent
FICHIER_REGLAGES = Path(__file__).parent / "reglages_montage.json"
DOSSIER_PROJETS = RACINE / "data" / "hyperframes"  # une page HyperFrames par script
DOSSIER_VIDEOS = RACINE / "data" / "videos"
POLICE = RACINE / "assets" / "polices" / "Montserrat-ExtraBold.ttf"
DOSSIER_SONS = RACINE / "assets" / "sons"  # boom, whoosh, pop et ding, fabriqués avec FFmpeg
VERSION_HYPERFRAMES = "hyperframes@0.9.23"  # version fixée : un même projet donne toujours la même vidéo

# Affiche correctement les accents, même quand Claude Code lit le résultat
sys.stdout.reconfigure(encoding="utf-8")


def sans_accent(mot):
    """« Écran, » devient « ecran » : pour chercher le mot dans le dictionnaire d'emojis."""
    mot = unicodedata.normalize("NFD", mot.lower())
    return "".join(c for c in mot if unicodedata.category(c) != "Mn").strip(".,!?:;'’\"…")


def est_mot_cle(mot, debut_de_phrase, emojis):
    """Un mot-clé : un nom propre au milieu d'une phrase (OpenAI, GPT), un nombre, ou un mot qui a un emoji."""
    nom_propre = mot[:1].isupper() and not debut_de_phrase and len(mot) > 2
    return nom_propre or any(c.isdigit() for c in mot) or sans_accent(mot) in emojis


def former_groupes(mots, mots_max, pause_max):
    """Coupe les mots en petits groupes à l'écran : quand c'est plein ou après une pause (comme sous_titres.py)."""
    groupes, groupe = [], []
    for i, mot in enumerate(mots):
        if groupe and (len(groupe) >= mots_max or mot["debut"] - mots[i - 1]["fin"] > pause_max):
            groupes.append(groupe)
            groupe = []
        groupe.append(mot)
    if groupe:
        groupes.append(groupe)
    return groupes


def partie_photos(nb_photos, fin_video, r):
    """Les photos plein écran : zoom lent, puis une transition (glissé, zoom ou fondu) avec flash et whoosh."""
    elements, animations, sons = [], [], []
    duree_trans = r["photos"]["duree_transition"]
    part = fin_video / max(nb_photos, 1)
    for i in range(nb_photos):
        debut = i * part - (duree_trans if i else 0)
        duree = min(part + (duree_trans if i else 0) + 0.05, fin_video - debut)
        elements.append(f'<div class="clip photo" id="p{i}" data-start="{debut:.2f}" data-duration="{duree:.2f}">'
                        f'<img src="assets/photo_{i}.jpg"></div>')
        sens = 1 if i % 2 == 0 else -1  # le zoom glisse une fois vers la droite, une fois vers la gauche
        animations.append(f'tl.fromTo("#p{i} img",{{scale:{r["photos"]["zoom_depart"]},xPercent:{-2 * sens}}},'
                          f'{{scale:{r["photos"]["zoom_fin"]},xPercent:{2 * sens},duration:{duree:.2f},ease:"none"}},{debut:.2f});')
        if i == 0:
            continue
        genre = r["photos"]["transitions"][(i - 1) % len(r["photos"]["transitions"])]
        if genre == "glisse":  # la photo arrive par la droite avec un flou de vitesse
            animations.append(f'tl.fromTo("#p{i}",{{xPercent:100,filter:"blur(18px)"}},{{xPercent:0,filter:"blur(0px)",duration:{duree_trans},ease:"power3.out"}},{debut:.2f});')
            animations.append(f'tl.to("#p{i - 1}",{{xPercent:-35,duration:{duree_trans},ease:"power3.out"}},{debut:.2f});')
        elif genre == "zoom":  # la photo arrive en zoomant depuis le centre
            animations.append(f'tl.fromTo("#p{i}",{{scale:1.6,opacity:0,filter:"blur(14px)"}},{{scale:1,opacity:1,filter:"blur(0px)",duration:{duree_trans},ease:"power2.out"}},{debut:.2f});')
        else:  # fondu rapide
            animations.append(f'tl.fromTo("#p{i}",{{opacity:0}},{{opacity:1,duration:{duree_trans},ease:"power1.inOut"}},{debut:.2f});')
        # Flash blanc au milieu de la transition
        moment_flash = debut + duree_trans * 0.45
        animations.append(f'tl.fromTo("#flash",{{opacity:0}},{{opacity:{r["photos"]["flash"]},duration:0.06,ease:"none"}},{moment_flash:.2f});')
        animations.append(f'tl.to("#flash",{{opacity:0,duration:0.22,ease:"power2.out"}},{moment_flash + 0.06:.2f});')
        sons.append(("whoosh", debut - 0.15))
    return elements, animations, sons


def partie_sous_titres(mots, fin_video, r):
    """Les sous-titres au mot près, les emojis qui surgissent et les zooms « punch » sur les mots-clés."""
    st, em, zp = r["sous_titres"], r["emojis"], r["zoom_punch"]
    dico = em["dictionnaire"]
    groupes = former_groupes(mots, st["mots_max"], st["pause_max"])
    elements, animations, sons = [], [], []
    dernier_emoji, dernier_zoom, nb_emojis = -99, r["accroche"]["duree"], 0

    for n, groupe in enumerate(groupes):
        debut = groupe[0]["debut"] - 0.05
        fin = groupes[n + 1][0]["debut"] - 0.05 if n + 1 < len(groupes) else fin_video
        spans, cles, emoji, moment_emoji = "", [], None, 0
        for k, mot in enumerate(groupe):
            position = mots.index(mot)
            debut_phrase = position == 0 or mots[position - 1]["mot"][-1:] in ".!?"
            cle = est_mot_cle(mot["mot"], debut_phrase, dico)
            cles.append(cle)
            texte = mot["mot"].upper() if st["majuscules"] else mot["mot"]
            spans += f'<span class="mot{" cle" if cle else ""}" id="m{n}_{k}">{html.escape(texte)}</span>'
            # Un emoji au plus par groupe, et pas trop souvent
            symbole = dico.get(sans_accent(mot["mot"]))
            if em["actifs"] and symbole and not emoji and mot["debut"] - dernier_emoji > em["ecart_min"]:
                emoji, moment_emoji = symbole, mot["debut"]
            # Zoom « punch » sur un mot-clé, pas trop souvent
            if zp["actif"] and cle and mot["debut"] - dernier_zoom > zp["ecart_min"]:
                dernier_zoom = mot["debut"]
                animations.append(f'tl.to("#scene",{{scale:{zp["force"]},duration:0.12,ease:"power3.out"}},{mot["debut"]:.3f});')
                animations.append(f'tl.to("#scene",{{scale:1,duration:0.5,ease:"power2.inOut"}},{mot["debut"] + 0.5:.3f});')

        elements.append(f'<div class="clip groupe" id="g{n}" data-start="{debut:.2f}" data-duration="{fin - debut:.2f}">{spans}</div>')
        # Le groupe arrive en s'écrasant puis rebondit
        animations.append(f'tl.fromTo("#g{n}",{{scaleX:0.7,scaleY:1.15,opacity:0}},{{scaleX:1,scaleY:1,opacity:1,duration:0.16,ease:"back.out(2.5)"}},{debut:.2f});')
        for k, mot in enumerate(groupe):
            selecteur, classe = f"#m{n}_{k}", "mot cle" if cles[k] else "mot"
            # Le mot dit passe dans la boîte et « saute »
            animations.append(f'tl.set("{selecteur}",{{attr:{{class:"{classe} actif"}}}},{mot["debut"]:.3f});')
            animations.append(f'tl.fromTo("{selecteur}",{{scale:1}},{{scale:{st["grossissement_mot_dit"]},duration:0.07,ease:"power2.out"}},{mot["debut"]:.3f});')
            animations.append(f'tl.to("{selecteur}",{{scale:1,duration:0.1,ease:"power2.in"}},{mot["debut"] + 0.07:.3f});')
            if k < len(groupe) - 1:
                animations.append(f'tl.set("{selecteur}",{{attr:{{class:"{classe}"}}}},{groupe[k + 1]["debut"]:.3f});')

        if emoji:
            dernier_emoji = moment_emoji
            duree = min(em["duree"], fin_video - moment_emoji)
            elements.append(f'<div class="clip emoji" id="e{nb_emojis}" data-start="{moment_emoji:.2f}" data-duration="{duree:.2f}">{emoji}</div>')
            animations.append(f'tl.fromTo("#e{nb_emojis}",{{scale:0,rotation:-25,y:40}},{{scale:1,rotation:8,y:0,duration:0.25,ease:"back.out(3)"}},{moment_emoji:.2f});')
            animations.append(f'tl.to("#e{nb_emojis}",{{rotation:-6,y:-12,duration:0.6,ease:"sine.inOut"}},{moment_emoji + 0.25:.2f});')
            animations.append(f'tl.to("#e{nb_emojis}",{{scale:0,opacity:0,duration:0.18,ease:"back.in(2)"}},{moment_emoji + duree - 0.18:.2f});')
            sons.append(("pop", moment_emoji - 0.02))
            nb_emojis += 1
    return elements, animations, sons


def partie_habillage(fin_video, r):
    """L'accroche du début (badge + titre qui claque), le bouton de fin et la barre de progression."""
    animations, sons = [], [("boom", 0.0)]
    animations.append('tl.fromTo("#badge",{scale:0,rotation:-12},{scale:1,rotation:-4,duration:0.3,ease:"back.out(3)"},0.05);')
    animations.append('tl.fromTo("#accroche",{scale:2.2,opacity:0},{scale:1,opacity:1,duration:0.22,ease:"power4.in"},0.1);')
    if r["accroche"]["secousse"]:
        animations.append('tl.fromTo("#scene",{x:0,y:0},{keyframes:[{x:-14,y:8},{x:12,y:-10},{x:-8,y:6},{x:5,y:-3},{x:0,y:0}],duration:0.3,ease:"none"},0.32);')
    animations.append(f'tl.to(["#accroche","#badge"],{{y:-80,opacity:0,duration:0.3,ease:"power2.in"}},{r["accroche"]["duree"]});')
    debut_fin = max(0, fin_video - r["fin"]["duree"])
    animations.append(f'tl.fromTo("#cta",{{y:220,opacity:0}},{{y:0,opacity:1,duration:0.4,ease:"back.out(2)"}},{debut_fin:.2f});')
    animations.append(f'tl.to("#cta",{{scale:1.08,duration:0.18,yoyo:true,repeat:3,ease:"sine.inOut"}},{debut_fin + 0.6:.2f});')
    sons.append(("ding", debut_fin))
    if r["barre_progression"]["active"]:
        animations.append(f'tl.fromTo("#barre",{{scaleX:0}},{{scaleX:1,duration:{fin_video:.2f},ease:"none"}},0);')
    return animations, sons


def style_page(r):
    """Le CSS de la page : couleurs et tailles viennent des réglages."""
    st = r["sous_titres"]
    return f"""
@font-face{{font-family:"Montserrat XB";src:url("assets/Montserrat-ExtraBold.ttf");}}
@font-face{{font-family:"Emoji";src:local("Segoe UI Emoji"),local("Apple Color Emoji"),local("Noto Color Emoji");}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#0d0d17}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;font-family:"Montserrat XB",sans-serif}}
#scene{{position:absolute;inset:0;transform-origin:50% 45%}}
.photo{{position:absolute;inset:0;overflow:hidden}}
.photo img{{width:100%;height:100%;object-fit:cover}}
#voile{{position:absolute;inset:0;z-index:5;background:
  radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,.45)),
  linear-gradient(transparent 40%,rgba(0,0,0,.3) 52%,rgba(0,0,0,{r["photos"]["assombrissement_bas"]}) 70%,rgba(0,0,0,.2))}}
#flash{{position:absolute;inset:0;background:#fff;opacity:0;z-index:20}}
.groupe{{position:absolute;left:50px;right:50px;bottom:{st["distance_du_bas"]}px;text-align:center;z-index:10;
  font-size:{st["taille"]}px;line-height:1.2}}
.mot{{display:inline-block;margin:0 .12em;padding:2px 16px;border-radius:16px;color:{st["couleur"]};
  -webkit-text-stroke:{st["epaisseur_contour"]}px #000;paint-order:stroke fill}}
.mot.cle{{color:{st["couleur_mot_cle"]}}}
.mot.actif{{background:{st["couleur_boite"]};color:{st["couleur_mot_dans_boite"]};-webkit-text-stroke:0;box-shadow:0 8px 0 rgba(0,0,0,.35)}}
.emoji{{position:absolute;left:0;right:0;bottom:{st["distance_du_bas"] + 220}px;text-align:center;font-size:{r["emojis"]["taille"]}px;
  z-index:11;font-family:"Emoji";filter:drop-shadow(0 12px 18px rgba(0,0,0,.5))}}
#badge{{position:absolute;top:200px;left:0;right:0;margin:auto;width:max-content;z-index:12;
  background:{r["accroche"]["couleur_badge"]};color:#fff;font-size:44px;padding:10px 26px;border-radius:12px;letter-spacing:.04em}}
#accroche{{position:absolute;top:300px;left:60px;right:60px;z-index:11;text-align:center;
  font-size:{r["accroche"]["taille_titre"]}px;line-height:1.15;color:#fff;-webkit-text-stroke:12px #000;paint-order:stroke fill}}
#cta{{position:absolute;top:260px;left:0;right:0;margin:auto;width:max-content;z-index:12;opacity:0;
  background:{r["fin"]["couleur"]};color:#fff;font-size:48px;padding:20px 40px;border-radius:60px;box-shadow:0 14px 40px rgba(0,0,0,.45)}}
#barre{{position:absolute;left:0;top:0;height:14px;width:100%;background:{r["barre_progression"]["couleur"]};transform-origin:left;z-index:30}}
"""


def preparer_projet(script_id, angle, audio, duree, visuels, r):
    """Écrit le dossier HyperFrames d'un script : la page index.html et ses fichiers (voix, photos, sons, police)."""
    dossier = DOSSIER_PROJETS / f"script_{script_id}"
    (dossier / "assets").mkdir(parents=True, exist_ok=True)
    images = json.loads(visuels or "[]")
    mots = json.loads((RACINE / audio.replace(".mp3", "_mots.json")).read_text(encoding="utf-8"))
    shutil.copy(RACINE / audio, dossier / "assets" / "voix.mp3")
    shutil.copy(POLICE, dossier / "assets" / POLICE.name)
    for son in DOSSIER_SONS.glob("*.wav"):
        shutil.copy(son, dossier / "assets" / son.name)
    for i, image in enumerate(images):
        shutil.copy(RACINE / image, dossier / "assets" / f"photo_{i}.jpg")

    fin_video = duree + 0.3  # la vidéo s'arrête juste après le dernier mot
    photos, anim_photos, sons_photos = partie_photos(len(images), fin_video, r)
    textes, anim_textes, sons_textes = partie_sous_titres(mots, fin_video, r)
    anim_habillage, sons_habillage = partie_habillage(fin_video, r)
    sons = sons_habillage + sons_photos + sons_textes
    balises_sons = "".join(
        f'<audio id="son{i}" src="assets/{nom}.wav" data-start="{max(0, moment):.2f}" '
        f'data-duration="1.3" data-volume="{r["sons"][nom]}"></audio>'
        for i, (nom, moment) in enumerate(sons))

    page = f"""<!doctype html>
<html lang="fr" data-resolution="portrait">
<head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>{style_page(r)}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fin_video:.2f}" data-width="1080" data-height="1920">
<div id="scene">{"".join(photos)}<div id="voile"></div></div>
{"".join(textes)}
<div id="badge">{html.escape(r["accroche"]["badge"])}</div>
<div id="accroche">{html.escape(angle.upper())}</div>
<div id="cta">{html.escape(r["fin"]["texte"])}</div>
<div id="flash"></div>
<div id="barre"></div>
<audio id="voix" src="assets/voix.mp3" data-start="0" data-duration="{fin_video:.2f}"></audio>
{balises_sons}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused:true}});
{chr(10).join(anim_habillage + anim_photos + anim_textes)}
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body></html>
"""
    (dossier / "index.html").write_text(page, encoding="utf-8")
    return dossier, len(sons)


def rendre(dossier, sortie, r):
    """Demande à HyperFrames de filmer la page dans Chrome et d'en faire un MP4."""
    npx = shutil.which("npx")  # sous Windows, c'est npx.cmd
    commande = [npx, "--yes", VERSION_HYPERFRAMES, "render", str(dossier), "-o", str(sortie),
                "--crf", str(r["rendu"]["qualite_crf"]), "--workers", str(r["rendu"]["processus_paralleles"]), "--quiet"]
    return subprocess.run(commande, capture_output=True, text=True, encoding="utf-8", errors="replace")


def normaliser_son(sortie, r):
    """Met le son au volume des réseaux (-14 LUFS) sans toucher à l'image, qui est juste recopiée."""
    temporaire = sortie.with_name(sortie.stem + "_son.mp4")
    commande = ["ffmpeg", "-y", "-v", "error", "-i", str(sortie), "-c:v", "copy",
                "-af", f"loudnorm=I={r['rendu']['volume_cible_lufs']}:TP=-1.5:LRA=11",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(temporaire)]
    if subprocess.run(commande).returncode == 0:
        temporaire.replace(sortie)


def main():
    base.creer_base()
    DOSSIER_VIDEOS.mkdir(parents=True, exist_ok=True)
    reglages = json.loads(FICHIER_REGLAGES.read_text(encoding="utf-8"))

    # Les numéros donnés au lancement, sinon les meilleurs scripts du jour (3 par défaut, un par news)
    numeros = [int(n) for n in sys.argv[1:]] or base.scripts_du_matin(reglages["videos_par_matin"])
    if not numeros:
        print("Aucun script prêt à monter (il faut la voix et les photos). Lance d'abord voix.py et visuels.py.")
        return

    for script_id in numeros:
        infos = base.infos_montage(script_id)
        if not infos or not infos[1] or not json.loads(infos[3] or "[]"):
            print(f"Script {script_id} : il manque la voix ou les photos, montage impossible.")
            continue
        angle, audio, duree, visuels = infos
        dossier, nb_sons = preparer_projet(script_id, angle, audio, duree, visuels, reglages)
        sortie = DOSSIER_VIDEOS / f"script_{script_id}.mp4"
        if sortie.exists():  # on garde la version d'avant pour comparer après un retour
            sortie.replace(DOSSIER_VIDEOS / f"script_{script_id}_avant.mp4")
        print(f"Script {script_id} : montage HyperFrames de {duree:.0f} s avec {nb_sons} effets sonores "
              f"(environ 4 minutes sur ce PC)...")
        resultat = rendre(dossier, sortie, reglages)
        if resultat.returncode != 0 or not sortie.exists():
            print(f"   Échec du montage : {(resultat.stderr or resultat.stdout).strip()[-400:]}")
            continue
        normaliser_son(sortie, reglages)
        base.enregistrer_video(script_id, f"data/videos/{sortie.name}")
        print(f"   Vidéo prête : data/videos/{sortie.name}")

    print("\nAprès avoir regardé une vidéo, tape /retour pour dire ce qu'il faut améliorer (ou « rien »).")


# Ce bloc lance main() seulement quand on exécute ce fichier directement
if __name__ == "__main__":
    main()
