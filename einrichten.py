"""Umgebung prüfen und einrichten, Daten migrieren, System aktualisieren.

Läuft mit dem System-Python, ohne Zusatzpakete (macOS/Linux: `python3` statt `python`):

    python einrichten.py                 # Umgebung prüfen, .venv anlegen und Pakete installieren
    python einrichten.py --migrieren     # daten/ auf die aktuelle Schemaversion bringen (mit Sicherung)
    python einrichten.py --aktualisieren # System per git pull holen, Pakete, Migrationen, Prüfung
    python einrichten.py --update-pruefen # nur nachsehen, ob es ein Update gibt (git fetch, ändert nichts)

Programme auf Systemebene (Python, git, Chrome) installiert das Skript nicht selbst, es nennt den Befehl.

Exit-Codes: 0 = in Ordnung, 1 = etwas fehlt oder ist fehlgeschlagen.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import umgebung

REPO = umgebung.REPO
DATEN = REPO / "daten"
MIN_PYTHON = (3, 10)

HINWEISE = {
    "Windows": {
        "python": "winget install Python.Python.3.12  (oder https://www.python.org/downloads/)",
        "git": "winget install Git.Git",
        "chrome": "winget install Google.Chrome  (Edge ist meist schon installiert)",
        "venv": "Python neu installieren, dabei „pip“ mit auswählen",
    },
    "Darwin": {
        "python": "brew install python  (oder https://www.python.org/downloads/)",
        "git": "xcode-select --install  (oder brew install git)",
        "chrome": "brew install --cask google-chrome",
        "venv": "brew reinstall python",
    },
    "Linux": {
        "python": "sudo apt install python3  (bzw. dnf/pacman)",
        "git": "sudo apt install git",
        "chrome": "sudo apt install chromium  (oder Google Chrome von https://www.google.com/chrome/)",
        "venv": "sudo apt install python3-venv",
    },
}


def hinweis(was: str) -> str:
    return HINWEISE.get(platform.system(), HINWEISE["Linux"])[was]


def melde(ok: bool, was: str, text: str) -> None:
    print(f"{'OK      ' if ok else 'FEHLT   '}{was}: {text}", flush=True)


def befehl(*argumente, cwd: Path = REPO, pruefen: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in argumente], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=pruefen)


# --------------------------------------------------------------------------- Umgebung

def pruefe_umgebung() -> bool:
    ok = True
    v = sys.version_info
    if v[:2] >= MIN_PYTHON:
        melde(True, "Python", f"{v.major}.{v.minor}.{v.micro}")
    else:
        melde(False, "Python", f"{v.major}.{v.minor} – mindestens {'.'.join(map(str, MIN_PYTHON))} nötig. {hinweis('python')}")
        ok = False

    git = shutil.which("git")
    if git:
        melde(True, "git", befehl("git", "--version").stdout.strip())
    else:
        melde(False, "git", hinweis("git"))
        ok = False

    chrome = umgebung.finde_chrome()
    if chrome:
        melde(True, "Browser für PDF", chrome)
    else:
        melde(False, "Browser für PDF", f"Chrome, Edge oder Chromium. {hinweis('chrome')} "
                                        f"– oder den Pfad in der Umgebungsvariable CHROME angeben")
        ok = False
    return ok


def richte_venv_ein(aktualisieren: bool = False) -> bool:
    py = umgebung.venv_python()
    if not py.exists():
        print("…       lege .venv an")
        erg = befehl(sys.executable, "-m", "venv", umgebung.VENV)
        if erg.returncode != 0 or not py.exists():
            melde(False, ".venv", f"konnte nicht angelegt werden: {erg.stderr.strip()[-300:]} – {hinweis('venv')}")
            return False
    print("…       installiere Pakete aus requirements.txt")
    argumente = [py, "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", REPO / "requirements.txt"]
    if aktualisieren:
        argumente.insert(4, "--upgrade")
    erg = befehl(*argumente)
    if erg.returncode != 0:
        melde(False, "Pakete", f"Installation fehlgeschlagen (Netz?): {erg.stderr.strip()[-300:]}")
        return False
    melde(True, ".venv", f"{py.relative_to(REPO).as_posix()} mit allen Paketen")
    return True


# --------------------------------------------------------------------------- Daten

def daten_ist_git() -> bool:
    return (DATEN / ".git").exists()


def sicherung() -> bool:
    """Sicherung vor einer Migration: Commit im Daten-Repo oder Kopie des Ordners."""
    if daten_ist_git():
        if befehl("git", "status", "--porcelain", cwd=DATEN).stdout.strip():
            befehl("git", "add", "-A", cwd=DATEN)
            erg = befehl("git", "commit", "-q", "-m", "Sicherung vor Migration", cwd=DATEN)
            if erg.returncode != 0:
                melde(False, "Sicherung", f"Commit im Daten-Repo fehlgeschlagen: {erg.stderr.strip() or erg.stdout.strip()}")
                return False
        stand = befehl("git", "rev-parse", "--short", "HEAD", cwd=DATEN).stdout.strip()
        melde(True, "Sicherung", f"Commit {stand} im Daten-Repo – zurück mit: git -C daten reset --hard {stand}")
        return True
    ziel = REPO / f"daten-sicherung-{datetime.now():%Y%m%d-%H%M%S}"
    shutil.copytree(DATEN, ziel)
    melde(True, "Sicherung", f"Kopie in {ziel.name}/")
    return True


def migrieren() -> bool:
    import migrationen  # erst hier, damit nach einem git pull die neue Fassung gilt

    if not (DATEN / "stammdaten").is_dir():
        melde(False, "Daten", "daten/stammdaten fehlt – noch nicht eingerichtet (Skill „einrichten“)")
        return False
    version = migrationen.lies_version(DATEN)
    if version == migrationen.SCHEMAVERSION:
        melde(True, "Schema", f"{version}, aktuell – keine Migration nötig")
        return pruefe_daten()
    if version > migrationen.SCHEMAVERSION:
        melde(False, "Schema", f"Daten haben {version}, System kennt nur bis {migrationen.SCHEMAVERSION} – "
                               f"python einrichten.py --aktualisieren")
        return False
    if not sicherung():
        return False
    try:
        migrationen.migriere(DATEN)
    except Exception as e:  # noqa: BLE001 – Fehler einer Migration vollständig melden
        melde(False, "Migration", f"{type(e).__name__}: {e} – Daten aus der Sicherung zurückholen")
        return False
    if daten_ist_git():
        befehl("git", "add", "-A", cwd=DATEN)
        befehl("git", "commit", "-q", "-m", f"Migration auf Schema {migrationen.SCHEMAVERSION}", cwd=DATEN)
    return pruefe_daten()


def pruefe_daten() -> bool:
    if not (DATEN / "stammdaten").is_dir():
        return True
    erg = subprocess.run([sys.executable, str(REPO / "render.py"), "--pruefen"], cwd=REPO)
    melde(erg.returncode == 0, "Prüfung", "render.py --pruefen " + ("bestanden" if erg.returncode == 0 else "mit Fehlern"))
    return erg.returncode == 0


DATEN_LIESMICH = """# Persönliche Daten für die Bewerbungs-Werkstatt

Dieser Ordner ist ein eigenes Git-Repo und gehört **nicht** ins System-Repo darüber.
Er enthält Foto, Kontaktdaten, Zeugnisse und Bewerbungen: lokal lassen oder nur in ein **privates** Remote pushen.

- `stammdaten/` – alle Inhalte (Person, Berufserfahrung, Ausbildung, Projekte, Skills, Kategorien, Schwerpunkte)
- `standard/<schwerpunkt>/` – Standardlebensläufe
- `bewerbungen/` – versendete Bewerbungen
- `anlagen/` – bereinigte Nachweise
- `templates/` – eigene Templates
- `einstellungen.yaml` – Standard-Template und Schemaversion
"""

OFFEN_MD = """# Offene Punkte

## Nachreichen

## Lücken aus Stellenausschreibungen
"""


def git_identitaet(name: str | None, email: str | None) -> bool:
    """Setzt Name/E-Mail nur für daten/, wenn angegeben. True, wenn danach eine Identität für Commits da ist."""
    if name:
        befehl("git", "config", "user.name", name, cwd=DATEN)
    if email:
        befehl("git", "config", "user.email", email, cwd=DATEN)
    return bool(befehl("git", "config", "user.name", cwd=DATEN).stdout.strip()
                and befehl("git", "config", "user.email", cwd=DATEN).stdout.strip())


def daten_anlegen(name: str | None = None, email: str | None = None) -> bool:
    """Legt daten/ als lokales Git-Repo mit leerem Gerüst an. Vorhandenes bleibt unverändert."""
    import migrationen

    if not shutil.which("git"):
        melde(False, "git", hinweis("git"))
        return False
    neu = not DATEN.exists()
    for ordner in ("stammdaten", "standard", "bewerbungen", "anlagen", "templates"):
        (DATEN / ordner).mkdir(parents=True, exist_ok=True)
    dateien = {
        DATEN / "LIESMICH.md": DATEN_LIESMICH,
        DATEN / "stammdaten" / "offen.md": OFFEN_MD,
        DATEN / "einstellungen.yaml": "# Persönliche Einstellungen.\n"
                                      f"schemaversion: {migrationen.SCHEMAVERSION}  # nicht von Hand ändern, "
                                      "siehe einrichten.py --migrieren\ntemplate: klassisch\n",
    }
    for pfad, inhalt in dateien.items():
        if not pfad.exists():
            pfad.write_text(inhalt, encoding="utf-8")
    if not daten_ist_git():
        befehl("git", "init", "-q", cwd=DATEN, pruefen=True)
        befehl("git", "checkout", "-q", "-b", "main", cwd=DATEN)
    melde(True, "daten/", ("angelegt" if neu else "vorhanden") + " – eigenes Git-Repo, nur lokal")
    if not git_identitaet(name, email):
        melde(False, "Git-Identität", "für Commits in daten/ fehlen Name oder E-Mail – erneut mit "
                                      "--git-name und --git-email aufrufen (gilt nur für daten/)")
        return False
    if befehl("git", "status", "--porcelain", cwd=DATEN).stdout.strip():
        befehl("git", "add", "-A", cwd=DATEN)
        befehl("git", "commit", "-q", "-m", "Daten-Repo angelegt", cwd=DATEN, pruefen=True)
    melde(True, "Git-Identität", befehl("git", "config", "user.name", cwd=DATEN).stdout.strip()
          + " <" + befehl("git", "config", "user.email", cwd=DATEN).stdout.strip() + ">")
    return True


# --------------------------------------------------------------------------- System aktualisieren

def aktualisieren() -> bool:
    if not (REPO / ".git").exists():
        melde(False, "System", "kein Git-Klon – neu klonen, um Updates zu bekommen")
        return False
    geaendert = befehl("git", "status", "--porcelain", "--untracked-files=no").stdout.strip()
    if geaendert:
        melde(False, "System", "geänderte Dateien im System (nicht in daten/) – erst zurücksetzen oder als PR einreichen:\n"
                               + geaendert)
        return False
    vorher = befehl("git", "rev-parse", "HEAD").stdout.strip()
    erg = befehl("git", "pull", "--ff-only", "-q")
    if erg.returncode != 0:
        melde(False, "System", f"git pull fehlgeschlagen: {erg.stderr.strip()}")
        return False
    neu = befehl("git", "log", "--oneline", "--no-merges", f"{vorher}..HEAD").stdout.strip()
    melde(True, "System", "aktualisiert:\n" + neu if neu else "schon aktuell")
    if not richte_venv_ein(aktualisieren=True):
        return False
    if not (DATEN / "stammdaten").is_dir():
        return True
    # neue Fassung von einrichten.py/migrationen.py nach dem Pull in einem frischen Prozess ausführen
    return subprocess.run([sys.executable, str(REPO / "einrichten.py"), "--migrieren"], cwd=REPO).returncode == 0


UPDATE_TIMEOUT = 15  # Sekunden für git fetch; ohne Netz soll die Prüfung den Start nicht aufhalten


def update_pruefen() -> bool:
    """Schaut nach, ob es ein Update gibt, ohne etwas zu ändern (nur git fetch).

    Gibt immer True zurück: Ohne Git-Klon, Upstream oder Netz wird die Prüfung mit einem Hinweis übersprungen.
    """
    if not (REPO / ".git").exists():
        print("UPDATE   übersprungen: kein Git-Klon")
        return True
    if befehl("git", "rev-parse", "--abbrev-ref", "@{u}", cwd=REPO).returncode != 0:
        print("UPDATE   übersprungen: kein Upstream-Branch")
        return True
    try:
        erg = subprocess.run(["git", "fetch", "-q"], cwd=REPO, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=UPDATE_TIMEOUT)
    except subprocess.TimeoutExpired:
        print("UPDATE   übersprungen: keine Antwort vom Server")
        return True
    if erg.returncode != 0:
        grund = (erg.stderr.strip().splitlines() or ["?"])[-1]
        print(f"UPDATE   übersprungen: git fetch fehlgeschlagen ({grund})")
        return True
    neu = befehl("git", "log", "--oneline", "--no-merges", "HEAD..@{u}", cwd=REPO).stdout.strip()
    if neu:
        print(f"UPDATE   verfügbar ({len(neu.splitlines())} Änderungen) – holen mit: "
              f"python einrichten.py --aktualisieren\n{neu}")
    else:
        print("UPDATE   System ist aktuell")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Umgebung prüfen und einrichten, Daten migrieren, System aktualisieren.")
    gruppe = ap.add_mutually_exclusive_group()
    gruppe.add_argument("--migrieren", action="store_true", help="daten/ auf die aktuelle Schemaversion bringen")
    gruppe.add_argument("--aktualisieren", action="store_true", help="System per git pull aktualisieren, dann migrieren")
    gruppe.add_argument("--update-pruefen", action="store_true",
                        help="nur nachsehen, ob es ein Update gibt (git fetch, ändert nichts)")
    gruppe.add_argument("--daten-anlegen", action="store_true",
                        help="daten/ als eigenes, lokales Git-Repo mit leerem Gerüst anlegen")
    ap.add_argument("--git-name", help="mit --daten-anlegen: Git-Name nur für daten/ (sonst der globale)")
    ap.add_argument("--git-email", help="mit --daten-anlegen: Git-E-Mail nur für daten/ (sonst die globale)")
    args = ap.parse_args(argv)

    if args.migrieren:
        return 0 if migrieren() else 1
    if args.aktualisieren:
        return 0 if aktualisieren() else 1
    if args.update_pruefen:
        return 0 if update_pruefen() else 1
    if args.daten_anlegen:
        return 0 if daten_anlegen(args.git_name, args.git_email) else 1
    ok = pruefe_umgebung()
    ok = richte_venv_ein() and ok
    if ok and not (DATEN / "stammdaten").is_dir():
        print("HINWEIS  daten/ ist noch nicht eingerichtet – in Claude Code „richte mich ein“ sagen (Skill einrichten)")
    print("Umgebung " + ("bereit." if ok else "unvollständig – fehlende Teile oben installieren und erneut ausführen."))
    return 0 if ok else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.exit(main())
