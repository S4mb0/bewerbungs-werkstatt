"""Gemeinsame Helfer für render.py und einrichten.py: venv und Browser finden.

Nur Standardbibliothek, damit einrichten.py es vor dem Anlegen der .venv nutzen kann.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
VENV = REPO / ".venv"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def laeuft_in_venv() -> bool:
    return Path(sys.prefix).resolve() == VENV.resolve()


def in_venv_neu_starten(skript: str) -> None:
    """Läuft das Skript nicht in der .venv des Repos, aber es gibt sie: dort neu starten und dessen Exit-Code übernehmen."""
    ziel = venv_python()
    if ziel.exists() and not laeuft_in_venv():
        sys.exit(subprocess.run([str(ziel), str(Path(skript).resolve()), *sys.argv[1:]]).returncode)


def chrome_kandidaten() -> list[str]:
    """Chrome, Edge oder Chromium auf Windows, macOS und Linux; CHROME (Umgebungsvariable) zuerst."""
    lokal = os.environ.get("LOCALAPPDATA", "")
    pfade = [
        os.environ.get("CHROME", ""),
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        f"{lokal}/Google/Chrome/Application/chrome.exe" if lokal else "",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "chrome"):
        pfade.append(shutil.which(name) or "")
    return [p for p in pfade if p]


def finde_chrome() -> str | None:
    for kandidat in chrome_kandidaten():
        if Path(kandidat).exists():
            return kandidat
    return None
