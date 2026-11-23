"""Tests für einrichten.py --update-pruefen mit echten, temporären Git-Repos.

Aufruf: python -m unittest discover -s tests -v   (mit dem Python der .venv)
"""

import contextlib
import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import einrichten  # noqa: E402

GIT = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-c", "init.defaultBranch=main"]


def schreibbar_loeschen(funktion, pfad, _):
    """Git legt Objekte schreibgeschützt an; unter Windows lassen sie sich erst nach chmod löschen."""
    os.chmod(pfad, stat.S_IWRITE)
    funktion(pfad)


def git(*argumente, cwd: Path):
    subprocess.run(GIT + list(argumente), cwd=cwd, check=True, capture_output=True)


class UpdatePruefen(unittest.TestCase):
    """Ein Remote (bare), ein Klon als „System“ und ein zweiter Klon, der neue Commits pusht."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="update-test-"))
        self.remote = self.tmp / "remote.git"
        git("init", "--bare", "-q", str(self.remote), cwd=self.tmp)
        quelle = self.tmp / "quelle"
        git("clone", "-q", str(self.remote), str(quelle), cwd=self.tmp)
        self.commit(quelle, "Erste Fassung")
        git("push", "-q", "origin", "HEAD:main", cwd=quelle)
        self.quelle = quelle
        self.system = self.tmp / "system"
        git("clone", "-q", str(self.remote), str(self.system), cwd=self.tmp)
        self.alt = einrichten.REPO
        einrichten.REPO = self.system

    def tearDown(self):
        einrichten.REPO = self.alt
        shutil.rmtree(self.tmp, onerror=schreibbar_loeschen)

    def commit(self, ordner: Path, nachricht: str):
        (ordner / "datei.txt").write_text(nachricht, encoding="utf-8")
        git("add", "datei.txt", cwd=ordner)
        git("commit", "-q", "-m", nachricht, cwd=ordner)

    def pruefen(self) -> str:
        aus = io.StringIO()
        with contextlib.redirect_stdout(aus):
            self.assertTrue(einrichten.update_pruefen())
        return aus.getvalue()

    def test_aktuell(self):
        self.assertIn("System ist aktuell", self.pruefen())

    def test_update_verfuegbar(self):
        self.commit(self.quelle, "Neue Fett-Regeln")
        git("push", "-q", "origin", "HEAD:main", cwd=self.quelle)
        aus = self.pruefen()
        self.assertIn("verfügbar (1 Änderungen)", aus)
        self.assertIn("Neue Fett-Regeln", aus)
        # nur nachgesehen, nichts geholt
        self.assertEqual((self.system / "datei.txt").read_text(encoding="utf-8"), "Erste Fassung")

    def test_ohne_upstream(self):
        git("checkout", "-q", "-b", "lokal", cwd=self.system)
        self.assertIn("übersprungen: kein Upstream-Branch", self.pruefen())

    def test_remote_nicht_erreichbar(self):
        git("remote", "set-url", "origin", str(self.tmp / "gibts-nicht.git"), cwd=self.system)
        self.assertIn("übersprungen: git fetch fehlgeschlagen", self.pruefen())

    def test_kein_git_klon(self):
        einrichten.REPO = self.tmp
        self.assertIn("übersprungen: kein Git-Klon", self.pruefen())


if __name__ == "__main__":
    unittest.main()
