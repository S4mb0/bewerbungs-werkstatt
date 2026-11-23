"""Migrationen der Datenstruktur in daten/.

Regel: Jede Änderung am System, die vorhandene Daten ungültig macht (Feld umbenannt, neues Pflichtfeld,
Datei verschoben …), erhöht SCHEMAVERSION und bringt hier eine Migration von N nach N+1 mit. Neue optionale
Felder brauchen keine. Für jede alte Version liegen Beispieldaten unter tests/schemas/v<N>/; der Test
migriert sie und prüft sie mit render.py.

Migrationen arbeiten textbasiert und nur mit der Standardbibliothek, damit Kommentare in den YAML-Dateien
erhalten bleiben. Aufruf normalerweise über `python einrichten.py --migrieren` (legt vorher eine Sicherung an).

    python migrationen.py [--daten <ordner>]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parent
VERSION_MUSTER = re.compile(r"^schemaversion:\s*(\d+)\s*(#.*)?$", re.M)


def einstellungen(daten: Path) -> Path:
    return daten / "einstellungen.yaml"


def lies_version(daten: Path) -> int:
    """Schemaversion der Daten; ohne einstellungen.yaml oder ohne Feld gilt 0."""
    pfad = einstellungen(daten)
    if not pfad.exists():
        return 0
    treffer = VERSION_MUSTER.search(pfad.read_text(encoding="utf-8"))
    return int(treffer.group(1)) if treffer else 0


def setze_version(daten: Path, version: int) -> None:
    pfad = einstellungen(daten)
    zeile = f"schemaversion: {version}  # nicht von Hand ändern, siehe einrichten.py --migrieren"
    if not pfad.exists():
        pfad.write_text("# Persönliche Einstellungen.\n" + zeile + "\n", encoding="utf-8")
        return
    text = pfad.read_text(encoding="utf-8")
    if VERSION_MUSTER.search(text):
        text = VERSION_MUSTER.sub(zeile, text, count=1)
    else:
        # nach den Kopfkommentaren einfügen
        zeilen = text.splitlines(keepends=True)
        i = 0
        while i < len(zeilen) and zeilen[i].lstrip().startswith("#"):
            i += 1
        zeilen.insert(i, zeile + "\n")
        text = "".join(zeilen)
    pfad.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- Migrationen

def migration_0_auf_1(daten: Path) -> list[str]:
    """Skill-Kategorien kommen aus stammdaten/kategorien.yaml statt aus render.py; schemaversion wird eingeführt."""
    erledigt = []
    kategorien = daten / "stammdaten" / "kategorien.yaml"
    if not kategorien.exists():
        kategorien.write_text(
            "# Kategorien der Skills, in der Reihenfolge, in der sie unter „Kenntnisse“ erscheinen.\n"
            "# gesprochene-sprache und arbeitsweise haben eine feste Bedeutung und müssen bleiben.\n"
            "# (angelegt von Migration 0 → 1 mit den bis dahin fest eingebauten Kategorien)\n"
            "kategorien:\n"
            "  - {id: programmiersprache, name: Programmiersprachen}\n"
            "  - {id: embedded-elektronik, name: Embedded & Elektronik}\n"
            "  - {id: cloud-betrieb, name: Cloud & Betrieb}\n"
            "  - {id: werkzeug-os, name: Tools & Systeme}\n"
            "  - {id: arbeitsweise, name: Arbeitsweise}\n"
            "  - {id: gesprochene-sprache, name: Sprachen}\n",
            encoding="utf-8")
        erledigt.append("stammdaten/kategorien.yaml mit den bisherigen Kategorien angelegt")
    return erledigt


# Version N -> Funktion, die von N nach N+1 migriert
MIGRATIONEN: dict[int, Callable[[Path], list[str]]] = {
    0: migration_0_auf_1,
}
SCHEMAVERSION = len(MIGRATIONEN)


def migriere(daten: Path, ausgabe=print) -> int:
    """Migriert daten/ auf SCHEMAVERSION. Gibt die Version vorher zurück. Wirft ValueError bei zu neuen Daten."""
    vorher = lies_version(daten)
    if vorher > SCHEMAVERSION:
        raise ValueError(f"Die Daten haben Schema {vorher}, dieses System kennt nur bis {SCHEMAVERSION} – "
                         f"System aktualisieren (python einrichten.py --aktualisieren)")
    for v in range(vorher, SCHEMAVERSION):
        for zeile in MIGRATIONEN[v](daten):
            ausgabe(f"MIGRATION {v} → {v + 1}: {zeile}")
        setze_version(daten, v + 1)
    if vorher == SCHEMAVERSION:
        ausgabe(f"MIGRATION nicht nötig, Schema {SCHEMAVERSION} ist aktuell")
    else:
        ausgabe(f"MIGRATION Schema {vorher} → {SCHEMAVERSION} fertig")
    return vorher


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Daten auf die aktuelle Schemaversion migrieren (ohne Sicherung).")
    ap.add_argument("--daten", type=Path, default=REPO / "daten")
    args = ap.parse_args(argv)
    if not (args.daten / "stammdaten").is_dir():
        print(f"FEHLER   {args.daten / 'stammdaten'} fehlt")
        return 1
    try:
        migriere(args.daten)
    except ValueError as e:
        print(f"FEHLER   {e}")
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
