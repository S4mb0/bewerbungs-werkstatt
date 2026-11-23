"""Tests für Schemaversion, Migrationen und einrichten.py.

Aufruf: python -m unittest discover -s tests -v   (mit dem Python der .venv)
"""

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import einrichten  # noqa: E402
import migrationen  # noqa: E402
import render  # noqa: E402

SCHEMAS = REPO / "tests" / "schemas"


def still(funktion, *argumente):
    aus = io.StringIO()
    with contextlib.redirect_stdout(aus):
        ergebnis = funktion(*argumente)
    return ergebnis, aus.getvalue()


class Migrationen(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="migration-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_migrationen_lueckenlos(self):
        """Jede Version unter SCHEMAVERSION hat eine Migration und Altdaten in tests/schemas/v<N>/."""
        self.assertEqual(set(migrationen.MIGRATIONEN), set(range(migrationen.SCHEMAVERSION)))
        for v in range(migrationen.SCHEMAVERSION):
            self.assertTrue((SCHEMAS / f"v{v}" / "stammdaten").is_dir(),
                            f"tests/schemas/v{v}/ fehlt – Altdaten für die Migration {v} → {v + 1} ablegen")

    def test_altdaten_jeder_version_werden_gueltig(self):
        for ordner in sorted(SCHEMAS.glob("v*")):
            with self.subTest(schema=ordner.name):
                daten = self.tmp / ordner.name
                shutil.copytree(ordner, daten)
                self.assertEqual(migrationen.lies_version(daten), int(ordner.name[1:]))
                code, aus = still(render.main, ["--daten", str(daten), "--pruefen"])
                self.assertEqual(code, 1, aus)
                self.assertIn("zuerst migrieren", aus)
                _, aus = still(migrationen.migriere, daten)
                self.assertEqual(migrationen.lies_version(daten), migrationen.SCHEMAVERSION)
                code, aus = still(render.main, ["--daten", str(daten), "--pruefen"])
                self.assertEqual(code, 0, aus)

    def test_beispiel_ist_aktuell(self):
        self.assertEqual(migrationen.lies_version(REPO / "beispiel"), migrationen.SCHEMAVERSION)

    def test_zu_neue_daten(self):
        daten = self.tmp / "daten"
        shutil.copytree(REPO / "beispiel", daten)
        migrationen.setze_version(daten, migrationen.SCHEMAVERSION + 1)
        code, aus = still(render.main, ["--daten", str(daten), "--pruefen"])
        self.assertEqual(code, 1, aus)
        self.assertIn("System aktualisieren", aus)
        with self.assertRaises(ValueError):
            still(migrationen.migriere, daten)

    def test_setze_version_behaelt_kommentare(self):
        daten = self.tmp / "daten"
        daten.mkdir()
        (daten / "einstellungen.yaml").write_text("# Kopf\n# zweite Zeile\ntemplate: kopfband  # mein Template\n",
                                                  encoding="utf-8")
        migrationen.setze_version(daten, 3)
        text = (daten / "einstellungen.yaml").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Kopf\n# zweite Zeile\nschemaversion: 3"), text)
        self.assertIn("template: kopfband  # mein Template", text)
        migrationen.setze_version(daten, 4)
        self.assertEqual(migrationen.lies_version(daten), 4)
        self.assertEqual((daten / "einstellungen.yaml").read_text(encoding="utf-8").count("schemaversion"), 1)

    def test_ohne_einstellungen_gilt_version_0(self):
        self.assertEqual(migrationen.lies_version(self.tmp), 0)


class Einrichten(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="einrichten-test-"))
        self.alt = (einrichten.REPO, einrichten.DATEN)
        einrichten.REPO = self.tmp
        einrichten.DATEN = self.tmp / "daten"
        shutil.copytree(SCHEMAS / "v0", einrichten.DATEN)

    def tearDown(self):
        einrichten.REPO, einrichten.DATEN = self.alt
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sicherung_ohne_git_ist_eine_kopie(self):
        ok, aus = still(einrichten.sicherung)
        self.assertTrue(ok, aus)
        kopien = list(self.tmp.glob("daten-sicherung-*"))
        self.assertEqual(len(kopien), 1)
        self.assertTrue((kopien[0] / "stammdaten" / "person.yaml").exists())

    @unittest.skipUnless(shutil.which("git"), "git fehlt")
    def test_sicherung_mit_git_ist_ein_commit(self):
        d = einrichten.DATEN
        for argumente in (["init", "-q"], ["config", "user.name", "Test"], ["config", "user.email", "test@example.org"],
                          ["add", "-A"], ["commit", "-q", "-m", "Start"]):
            einrichten.befehl("git", *argumente, cwd=d, pruefen=True)
        (d / "stammdaten" / "notiz.md").write_text("ungespeichert\n", encoding="utf-8")
        ok, aus = still(einrichten.sicherung)
        self.assertTrue(ok, aus)
        self.assertIn("git -C daten reset --hard", aus)
        log = einrichten.befehl("git", "log", "--format=%s", cwd=d).stdout
        self.assertEqual(log.splitlines()[0], "Sicherung vor Migration")

    def test_hinweise_fuer_alle_systeme(self):
        for system in einrichten.HINWEISE.values():
            self.assertEqual(set(system), {"python", "git", "chrome", "venv"})


if __name__ == "__main__":
    unittest.main()
