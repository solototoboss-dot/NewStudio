# Tests simples du studio : vérifient les petites fonctions qui décident du montage.
# Ils n'ont besoin ni de la base, ni d'Internet, ni de clé.
#
# Lancement : python -m unittest discover tests

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Les fichiers du studio sont dans le dossier veille/
VEILLE = Path(__file__).parent.parent / "veille"
sys.path.insert(0, str(VEILLE))

import base  # noqa: E402
import benchmark  # noqa: E402
import hyperframes  # noqa: E402

REGLAGES = json.loads((VEILLE / "reglages_montage.json").read_text(encoding="utf-8"))


class TestAccroche(unittest.TestCase):
    def test_accroche_ecrite_par_scripts_gardee(self):
        self.assertEqual(hyperframes.texte_accroche("Google crée des mondes", "Peu importe.", 7),
                         "Google crée des mondes")

    def test_sinon_premiere_phrase_sans_balise(self):
        texte = "[excited] Deux IA ont tout changé. La suite est longue."
        self.assertEqual(hyperframes.texte_accroche(None, texte, 7), "Deux IA ont tout changé")

    def test_phrase_trop_longue_raccourcie(self):
        texte = "Une famille américaine attaque OpenAI en justice après la mort de sa fille."
        self.assertEqual(hyperframes.texte_accroche("", texte, 7),
                         "Une famille américaine attaque OpenAI en justice…")


class TestSujetSensible(unittest.TestCase):
    MOTS = REGLAGES["sujets_sensibles"]["mots"]

    def test_justice_et_deces_reperes_malgre_les_accents(self):
        self.assertTrue(hyperframes.est_sensible("Un procès après le décès de sa fille.", self.MOTS))

    def test_annonce_technique_pas_sensible(self):
        self.assertFalse(hyperframes.est_sensible("Google présente Genie quatre, un monde virtuel.", self.MOTS))

    def test_montage_sobre(self):
        r = hyperframes.adapter_au_sujet(REGLAGES, True)
        self.assertFalse(r["emojis"]["actifs"])
        self.assertFalse(r["accroche"]["secousse"])
        self.assertEqual(r["sons"]["boom"], 0)
        self.assertGreater(r["sons"]["whoosh"], 0)
        # Les réglages d'origine ne doivent pas changer
        self.assertTrue(REGLAGES["emojis"]["actifs"])

    def test_sujet_normal_inchange(self):
        self.assertIs(hyperframes.adapter_au_sujet(REGLAGES, False), REGLAGES)


class TestSousTitres(unittest.TestCase):
    def test_groupes_coupes_quand_pleins_ou_apres_une_pause(self):
        mots = [{"mot": m, "debut": d, "fin": d + 0.2} for m, d in
                [("un", 0.0), ("deux", 0.3), ("trois", 0.6), ("quatre", 0.9), ("cinq", 3.0)]]
        groupes = hyperframes.former_groupes(mots, mots_max=3, pause_max=0.6)
        self.assertEqual([len(g) for g in groupes], [3, 1, 1])

    def test_balises_emotion_retirees(self):
        self.assertNotIn("[", base.retirer_balises("[serious] Une plainte a été déposée."))


class TestBenchmark(unittest.TestCase):
    def test_temps_de_montage_lu_dans_le_journal(self):
        with tempfile.TemporaryDirectory() as dossier:
            journal = Path(dossier) / "data" / "journal"
            journal.mkdir(parents=True)
            (journal / "matin_2026-11-09.txt").write_text(
                "=== Matin du 2026-11-09 ===\n--- Montage HyperFrames (13:41) ---\n"
                "   Vidéo prête : a\n   Vidéo prête : b\n--- Contrôle qualité (13:53) ---\n", encoding="utf-8")
            self.assertEqual(benchmark.temps_de_montage(Path(dossier)), [("2026-11-09", 2, 12.0)])


if __name__ == "__main__":
    unittest.main()
