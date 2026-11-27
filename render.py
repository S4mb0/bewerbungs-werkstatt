"""Lebenslauf und Anschreiben rendern und Stammdaten prüfen.

Einrichtung der lokalen .venv (einmalig je Checkout, sie ist gitignoriert):

    python -m venv .venv && <venv-python> -m pip install -r requirements.txt
    (<venv-python> = .venv/Scripts/python unter Windows, .venv/bin/python unter macOS/Linux)

Aufrufe aus dem Repo-Wurzelordner. Gibt es eine .venv, startet sich das Skript selbst darin neu,
`python render.py …` (macOS/Linux: `python3 render.py …`) genügt also:

    python render.py <ordner>            # <ordner>/lebenslauf.yaml -> <ordner>/lebenslauf.pdf
                                         # und, falls vorhanden, anschreiben.yaml -> anschreiben.pdf
    python render.py --nur-anschreiben <ordner>  # nur das Anschreiben neu (z. B. bei der Freigabe wegen des Datums)
    python render.py --pruefen [ordner…]  # nur prüfen: Schema, IDs, Verweise
    python render.py --vorschau <template> [ordner…]  # Standardlebensläufe (und -anschreiben) mit Template nach vorschau/

Ein Anschreiben nutzt immer das Template des Lebenslaufs im selben Ordner. Empfänger, Stelle und Datum liest es
aus bewerbung.yaml im selben Ordner; ohne bewerbung.yaml (Standardanschreiben) stehen dort Platzhalter.

Die persönlichen Daten liegen in daten/ (eigenes Git-Repo, hier gitignoriert): stammdaten/, standard/,
bewerbungen/, anlagen/, templates/ (eigene Templates) und einstellungen.yaml. Mit --daten lässt sich ein
anderer Daten-Ordner wählen (z. B. beispiel).

Ohne Ordner prüft --pruefen die Stammdaten sowie daten/standard/*/ und entwurf/ (lebenslauf.yaml und, falls
vorhanden, anschreiben.yaml).

Das Aussehen bestimmt ein Template (<name>.yaml = Grundlayout + Parameter, mitgeliefert in templates/,
eigene in daten/templates/). Welches: Feld `template` in lebenslauf.yaml, sonst `template` in
daten/einstellungen.yaml, sonst „klassisch“. --pruefen prüft auch alle Templates, Grundlayouts und Schriften.

Exit-Codes: 0 = in Ordnung, 1 = Prüfung fehlgeschlagen, 2 = PDF-Erzeugung oder PDF-Prüfung fehlgeschlagen.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import umgebung
from migrationen import SCHEMAVERSION, lies_version

REPO = umgebung.REPO

if __name__ == "__main__":
    umgebung.in_venv_neu_starten(__file__)

import jinja2
import markupsafe
import yaml
from pypdf import PdfReader

TEMPLATE_ORDNER = REPO / "templates"                 # mitgelieferte Templates: <name>.yaml = Grundlayout + Parameter
GRUNDLAYOUT_ORDNER = TEMPLATE_ORDNER / "grundlayouts"  # <name>.html.j2 + <name>.yaml (erlaubte Parameter)
SCHRIFTEN_ORDNER = TEMPLATE_ORDNER / "schriften"
VORSCHAU = REPO / "vorschau"                         # Ausgabe von --vorschau (gitignoriert)
ENTWURF = REPO / "entwurf"                           # Arbeitsordner während einer Anpassung (gitignoriert)
DATEN = REPO / "daten"                               # persönliche Daten (eigenes Git-Repo, gitignoriert)


def stammdaten_ordner() -> Path:
    return DATEN / "stammdaten"


def einstellungen_pfad() -> Path:
    return DATEN / "einstellungen.yaml"


def eigene_templates() -> Path:
    return DATEN / "templates"
STANDARD_TEMPLATE = "klassisch"                      # gilt, wenn weder Lebenslauf noch Einstellungen eins nennen
MAX_SEITEN = 2

CHROME_KANDIDATEN = umgebung.chrome_kandidaten()

# Kategorien mit fester Bedeutung; alle übrigen legt der Nutzer in stammdaten/kategorien.yaml an.
SPRACHE = "gesprochene-sprache"   # steht immer im Lebenslauf
ARBEITSWEISE = "arbeitsweise"     # kommt nur mit Beleg in den Lebenslauf

ID_MUSTER = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MONAT_MUSTER = re.compile(r"^(19|20)\d\d-(0[1-9]|1[0-2])$")


# --------------------------------------------------------------------------- Befunde

class Befunde:
    """Sammelt Fehler (brechen ab) und Warnungen (nur Hinweis)."""

    def __init__(self) -> None:
        self.fehler: list[str] = []
        self.warnungen: list[str] = []

    def fehler_(self, ort: str, text: str) -> None:
        self.fehler.append(f"{ort}: {text}")

    def warnung(self, ort: str, text: str) -> None:
        self.warnungen.append(f"{ort}: {text}")

    def ausgeben(self) -> None:
        for w in self.warnungen:
            print(f"WARNUNG  {w}")
        for f in self.fehler:
            print(f"FEHLER   {f}")


# --------------------------------------------------------------------------- Schema

# Ein Schema ist ein dict Feldname -> (Typ, Pflicht). Typen:
#   "id", "str", "text" (str oder Zahl), "monat", "bis" (monat oder "heute"), "bool",
#   "idliste", "strliste", ("enum", {…}), ("liste", schema), ("objekt", schema), ("aussage",)
AUSSAGE = ("aussage",)

POSITIONSARTEN = {"Festanstellung", "Teilzeit", "Ausbildung", "Praktikum", "Werkstudent", "Minijob",
                  "Freiberuflich", "Selbstständig", "Ehrenamt"}

TAETIGKEIT = {
    "id": ("id", True), "kernaussage": ("str", True), "details": ("str", True),
    "formulierungen": ("strliste", False), "schwerpunkte": ("idliste", True),
    "skills": ("idliste", False), "veraltet": ("bool", False),
}
POSITION = {
    "id": ("id", True), "art": (("enum", POSITIONSARTEN), True),
    "titel": ("str", True), "von": ("monat", True), "bis": ("bis", True),
    "taetigkeiten": (("liste", TAETIGKEIT), False), "anlage": ("str", False), "veraltet": ("bool", False),
}
ARBEITGEBER = {
    "id": ("id", True), "name": ("str", True), "ort": ("str", False),
    "positionen": (("liste", POSITION), True), "veraltet": ("bool", False),
}
ABSCHLUSS = {
    "id": ("id", True), "art": (("enum", {"schule", "ausbildung", "studium", "weiterbildung", "zertifikat"}), True),
    "bezeichnung": ("str", True), "institution": ("str", True),
    "von": ("monat", False), "bis": ("monat", False), "note": ("text", False),
    "status": (("enum", {"abgeschlossen", "laufend"}), True), "thema": ("str", False),
    "anlage": ("str", False), "position": ("id", False), "skills": ("idliste", False),
    "veraltet": ("bool", False),
}
PROJEKT = {
    "id": ("id", True), "titel": ("str", True),
    "kontext": (("enum", {"privat", "studium", "beruflich", "ehrenamt"}), True), "position": ("id", False),
    "von": ("monat", False), "bis": ("bis", False), "kernaussage": ("str", True),
    "details": ("str", True), "formulierungen": ("strliste", False), "repos": ("strliste", False),
    "schwerpunkte": ("idliste", True), "skills": ("idliste", False), "veraltet": ("bool", False),
}
SKILL = {
    "id": ("id", True), "name": ("str", True), "kategorie": ("id", True),
    "niveau": ("str", True), "schwerpunkte": ("idliste", False), "veraltet": ("bool", False),
}
PROFILTEXT = {"id": ("id", True), "text": ("str", True)}
SCHWERPUNKT = {"id": ("id", True), "profiltext": (("objekt", PROFILTEXT), True)}
PERSON = {
    "id": ("id", True), "name": ("str", True), "wohnort": ("str", True),
    "strasse": ("str", False), "plz": ("text", False),          # nur fürs Anschreiben (Absender)
    "telefon": ("str", False), "email": ("str", False), "web": ("strliste", False),
    "geburtsdatum": ("str", False), "geburtsort": ("str", False), "foto": ("str", False),
    "unterschrift": ("str", False),                               # Bild, relativ zu stammdaten/, nur fürs Anschreiben
}

# Anschreiben: Absätze mit einer Art. Bausteine (freigegebene Absätze in stammdaten/anschreiben.yaml) gibt es für
# alle Arten außer „hauptteil“: Aussagen über die eigene Erfahrung zitieren Tätigkeiten, Projekte und Abschlüsse.
ABSATZARTEN = {"einstieg", "hauptteil", "motivation", "rahmen", "schluss"}
BAUSTEIN = {
    "id": ("id", True), "art": (("enum", ABSATZARTEN - {"hauptteil"}), True), "text": ("str", True),
    "schwerpunkte": ("idliste", False), "veraltet": ("bool", False),
}
RAHMEN = {"verfuegbarkeit": ("str", False), "gehalt": ("str", False)}
ANSCHREIBEN_STAMMDATEN = {"bausteine": (("liste", BAUSTEIN), False), "rahmen": (("objekt", RAHMEN), False)}
RAHMEN_ID = "rahmen"   # feste ID der Rahmendaten (Verfügbarkeit, Gehalt) als Quelle eines Absatzes

KATEGORIE = {"id": ("id", True), "name": ("str", True)}

# Datei -> (Wurzelschlüssel oder None für ein einzelnes Objekt, Schema)
STAMMDATEN_DATEIEN = {
    "kategorien.yaml": ("kategorien", KATEGORIE),
    "person.yaml": (None, PERSON),
    "berufserfahrung.yaml": ("arbeitgeber", ARBEITGEBER),
    "ausbildung.yaml": ("abschluesse", ABSCHLUSS),
    "projekte.yaml": ("projekte", PROJEKT),
    "skills.yaml": ("skills", SKILL),
    "profil.yaml": ("schwerpunkte", SCHWERPUNKT),
}

LEBENSLAUF = {
    "schwerpunkt": ("id", True), "template": ("id", False),
    "untertitel": ("str", False), "profil": (AUSSAGE, False),
    "schalter": (("objekt", {
        "foto": ("bool", False),
        "positionen": (("enum", {"zusammengefasst", "einzeln"}), False),
    }), False),
    "berufserfahrung": (("liste", {
        "arbeitgeber": ("id", True), "taetigkeiten": (("liste", AUSSAGE), False),
    }), False),
    "kenntnisse": ("idliste", False),
    "projekte": (("liste", AUSSAGE), False),
    "fett": ("strliste", False),   # Treffer der Stellenausschreibung, die fett sein müssen (nur in Entwürfen)
}
AUSSAGE_SCHEMA = {"quelle": ("id", True), "text": ("str", False), "umformuliert": ("bool", False)}

ABSATZ = {
    "art": (("enum", ABSATZARTEN), True), "text": ("str", False), "quellen": ("idliste", False),
    "herkunft": (("enum", {"anzeige", "nutzer"}), False), "umformuliert": ("bool", False),
}
ANSCHREIBEN = {
    "betreff": ("str", False),   # ersetzt „Bewerbung als <Stelle>“
    "schalter": (("objekt", {"unterschrift": ("bool", False)}), False),
    "absaetze": (("liste", ABSATZ), True),
}
BEWERBUNG = {
    "firma": ("str", True), "stelle": ("str", True), "datum": ("tag", False), "schwerpunkt": ("id", False),
    "status": ("str", False), "kennziffer": ("text", False),
    "empfaenger": (("objekt", {
        "abteilung": ("str", False), "ansprechperson": ("str", False), "strasse": ("str", False),
        "plz": ("text", False), "ort": ("str", False), "anrede": ("str", False),
    }), False),
}
# Quellen, die ein Absatz zitieren darf
ABSATZ_QUELLEN = {"taetigkeit", "projekt", "abschluss", "position", "skill", "profiltext", "baustein", "rahmen"}
ANSCHREIBEN_WOERTER = (200, 400)   # außerhalb: Hinweis (Ziel 250–350)

# Templates, Grundlayouts, Schriften, Einstellungen
ABSCHNITTE = ["berufserfahrung", "ausbildung", "kenntnisse", "projekte"]
TEMPLATE_SCHEMA = {
    "beschreibung": ("str", True), "grundlayout": ("id", True),
    "farbe": ("farbe", True), "linienfarbe": ("farbe", False), "schrift": ("id", True),
    "foto": (("objekt", {
        "form": (("enum", {"eckig", "rund"}), True),
        "position": (("enum", {"rechts", "links"}), True),
    }), True),
    "ueberschriften": (("enum", {"linie", "balken", "fett"}), True),
    "reihenfolge": (("enum-liste", set(ABSCHNITTE)), True),
    "veraltet": ("bool", False),
}
GRUNDLAYOUT_SCHEMA = {
    "beschreibung": ("str", True),
    "foto_positionen": (("enum-liste", {"rechts", "links"}), True),
    "weisser_text_auf_farbe": ("bool", False),
    "spalten": ("spalten", True),
}
MIN_KONTRAST = 4.5  # WCAG AA für normalen Text
SCHRIFT_SCHEMA = {
    "id": ("id", True), "name": ("str", True), "stack": ("str", True), "system": ("bool", False),
    "lizenz": ("str", False),
    "dateien": (("liste", {
        "datei": ("str", True), "gewicht": (("enum", {300, 400, 500, 600, 700}), True),
        "stil": (("enum", {"normal", "italic"}), True),
    }), False),
}
EINSTELLUNGEN_SCHEMA = {
    "schemaversion": ("zahl", False), "template": ("id", False),
    "anschreiben": (("enum", {"nein"}), False),   # nein: einrichten fragt nicht mehr nach Anschreiben
}
FARB_MUSTER = re.compile(r"^#[0-9a-fA-F]{6}$")


def pruefe_schema(obj, schema: dict, ort: str, b: Befunde) -> None:
    if not isinstance(obj, dict):
        b.fehler_(ort, f"erwartet ein Objekt mit Feldern, gefunden: {kurz(obj)}")
        return
    for feld in obj:
        if feld not in schema:
            b.fehler_(ort, f"unbekanntes Feld '{feld}' (erlaubt: {', '.join(schema)})")
    for feld, (typ, pflicht) in schema.items():
        if feld not in obj or obj[feld] is None:
            if pflicht:
                b.fehler_(ort, f"Pflichtfeld '{feld}' fehlt")
            continue
        pruefe_wert(obj[feld], typ, f"{ort}.{feld}", b)


def pruefe_wert(wert, typ, ort: str, b: Befunde) -> None:
    if typ == AUSSAGE:
        if isinstance(wert, str):
            b.fehler_(ort, f"Aussage ohne Quelle: {kurz(wert)} – erwartet {{quelle: <ID>, text, umformuliert}}")
        elif isinstance(wert, dict) and not wert.get("quelle"):
            b.fehler_(ort, f"Aussage ohne Quelle: {kurz(wert.get('text', wert))}")
        else:
            pruefe_schema(wert, AUSSAGE_SCHEMA, ort, b)
        return
    if isinstance(typ, tuple):
        art, inhalt = typ
        if art == "enum-liste":
            if not isinstance(wert, list):
                b.fehler_(ort, "erwartet eine Liste")
                return
            for i, x in enumerate(wert):
                pruefe_wert(x, ("enum", inhalt), f"{ort}[{i}]", b)
            if len(set(map(str, wert))) != len(wert):
                b.fehler_(ort, "enthält einen Wert doppelt")
            return
        if art == "enum":
            if wert not in inhalt:
                b.fehler_(ort, f"'{wert}' ist nicht erlaubt (erlaubt: {', '.join(sorted(map(str, inhalt)))})")
        elif art == "objekt":
            pruefe_schema(wert, inhalt, ort, b)
        elif art == "liste":
            if not isinstance(wert, list):
                b.fehler_(ort, "erwartet eine Liste")
                return
            for i, x in enumerate(wert):
                if inhalt == AUSSAGE:
                    pruefe_wert(x, AUSSAGE, f"{ort}[{i}]", b)
                else:
                    pruefe_schema(x, inhalt, f"{ort}[{i}]", b)
        return
    if typ == "id":
        if not isinstance(wert, str) or not ID_MUSTER.match(wert):
            b.fehler_(ort, f"ungültige ID {kurz(wert)} (nur a–z, 0–9 und Bindestriche)")
    elif typ == "str":
        if not isinstance(wert, str) or not wert.strip():
            b.fehler_(ort, f"erwartet einen nicht leeren Text, gefunden: {kurz(wert)}")
    elif typ == "text":
        if not isinstance(wert, (str, int, float)):
            b.fehler_(ort, f"erwartet einen Text, gefunden: {kurz(wert)}")
    elif typ == "tag":   # "JJJJ-MM-TT" oder ein Platzhalter wie "<JJJJ-MM-TT>" im Entwurf
        if not isinstance(wert, (str, date)):
            b.fehler_(ort, f"erwartet ein Datum JJJJ-MM-TT, gefunden: {kurz(wert)}")
    elif typ == "zahl":
        if not isinstance(wert, int) or isinstance(wert, bool) or wert < 0:
            b.fehler_(ort, f"erwartet eine ganze Zahl ≥ 0, gefunden: {kurz(wert)}")
    elif typ == "farbe":
        if not isinstance(wert, str) or not FARB_MUSTER.match(wert):
            b.fehler_(ort, f"ungültige Farbe {kurz(wert)} (erwartet #rrggbb, in Anführungszeichen)")
    elif typ == "spalten":
        if not isinstance(wert, dict) or not wert:
            b.fehler_(ort, "erwartet Spalten als {name: [abschnitte]}")
            return
        alle = []
        for spalte, abschnitte in wert.items():
            pruefe_wert(spalte, "id", f"{ort}.{spalte}", b)
            pruefe_wert(abschnitte, ("enum-liste", set(ABSCHNITTE)), f"{ort}.{spalte}", b)
            alle += abschnitte if isinstance(abschnitte, list) else []
        if sorted(map(str, alle)) != sorted(ABSCHNITTE):
            b.fehler_(ort, f"jeder Abschnitt muss genau einmal vorkommen ({', '.join(ABSCHNITTE)})")
    elif typ == "bool":
        if not isinstance(wert, bool):
            b.fehler_(ort, f"erwartet true oder false, gefunden: {kurz(wert)}")
    elif typ in ("monat", "bis"):
        if typ == "bis" and wert == "heute":
            return
        if not isinstance(wert, str) or not MONAT_MUSTER.match(wert):
            erlaubt = "JJJJ-MM" + (" oder 'heute'" if typ == "bis" else "")
            b.fehler_(ort, f"ungültiges Datum {kurz(wert)} (erwartet {erlaubt}, in Anführungszeichen)")
    elif typ in ("idliste", "strliste"):
        if not isinstance(wert, list):
            b.fehler_(ort, "erwartet eine Liste")
            return
        for i, x in enumerate(wert):
            pruefe_wert(x, typ[:-5] if typ == "strliste" else "id", f"{ort}[{i}]", b)


def kurz(wert) -> str:
    s = repr(wert)
    return s if len(s) <= 70 else s[:67] + "…'"


# --------------------------------------------------------------------------- Stammdaten

class Stammdaten:
    """Geladene Stammdaten mit einem Index aller IDs."""

    def __init__(self, ordner: Path) -> None:
        self.ordner = ordner
        self.person: dict = {}
        self.arbeitgeber: list[dict] = []
        self.abschluesse: list[dict] = []
        self.projekte: list[dict] = []
        self.skills: list[dict] = []
        self.schwerpunkte: list[dict] = []
        self.kategorien: list[dict] = []   # Reihenfolge = Reihenfolge unter „Kenntnisse“
        self.bausteine: list[dict] = []    # aus der optionalen anschreiben.yaml
        self.rahmen: dict = {}
        # ID -> (Art, Objekt, Eltern-ID)
        self.index: dict[str, tuple[str, dict, str | None]] = {}

    def art(self, id_: str) -> str | None:
        return self.index[id_][0] if id_ in self.index else None

    def obj(self, id_: str) -> dict:
        return self.index[id_][1]

    def eltern(self, id_: str) -> str | None:
        return self.index[id_][2]


def lade_yaml(pfad: Path, b: Befunde):
    try:
        with pfad.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        b.fehler_(rel(pfad), f"kein gültiges YAML: {e}")
    except OSError as e:
        b.fehler_(rel(pfad), f"nicht lesbar: {e}")
    return None


def rel(pfad: Path) -> str:
    try:
        return pfad.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return pfad.as_posix()


def lade_stammdaten(ordner: Path, b: Befunde) -> Stammdaten:
    sd = Stammdaten(ordner)
    if not ordner.is_dir():
        b.fehler_(rel(ordner), "Stammdaten-Ordner fehlt")
        return sd

    for datei, (wurzel, schema) in STAMMDATEN_DATEIEN.items():
        pfad = ordner / datei
        ort = rel(pfad)
        if not pfad.exists():
            b.fehler_(ort, "Datei fehlt")
            continue
        daten = lade_yaml(pfad, b)
        if daten is None:
            continue
        if wurzel is None:
            pruefe_schema(daten, schema, ort, b)
            if isinstance(daten, dict):
                sd.person = daten
            continue
        if not isinstance(daten, dict) or set(daten) != {wurzel}:
            b.fehler_(ort, f"erwartet genau einen Schlüssel '{wurzel}:' mit einer Liste")
            continue
        liste = daten[wurzel] or []
        pruefe_wert(liste, ("liste", schema), f"{ort}:{wurzel}", b)
        if isinstance(liste, list):
            setattr(sd, wurzel, [x for x in liste if isinstance(x, dict)])

    lade_anschreiben_stammdaten(sd, b)
    baue_index(sd, b)
    pruefe_verweise(sd, b)
    return sd


def lade_anschreiben_stammdaten(sd: Stammdaten, b: Befunde) -> None:
    """Die optionale stammdaten/anschreiben.yaml: Bausteine und Rahmendaten. Fehlt sie, gibt es beides nicht."""
    pfad = sd.ordner / "anschreiben.yaml"
    if not pfad.exists():
        return
    daten = lade_yaml(pfad, b)
    if daten is None:
        return
    pruefe_schema(daten, ANSCHREIBEN_STAMMDATEN, rel(pfad), b)
    if not isinstance(daten, dict):
        return
    if isinstance(daten.get("bausteine"), list):
        sd.bausteine = [x for x in daten["bausteine"] if isinstance(x, dict)]
    if isinstance(daten.get("rahmen"), dict):
        sd.rahmen = daten["rahmen"]


def baue_index(sd: Stammdaten, b: Befunde) -> None:
    def neu(id_, art, obj, eltern=None):
        if not isinstance(id_, str):
            return
        if id_ in sd.index:
            b.fehler_(f"ID '{id_}'", f"doppelt vergeben ({sd.index[id_][0]} und {art})")
            return
        sd.index[id_] = (art, obj, eltern)

    if sd.person:
        neu(sd.person.get("id"), "person", sd.person)
    for ag in sd.arbeitgeber:
        neu(ag.get("id"), "arbeitgeber", ag)
        for pos in ag.get("positionen") or []:
            if isinstance(pos, dict):
                neu(pos.get("id"), "position", pos, ag.get("id"))
                for t in pos.get("taetigkeiten") or []:
                    if isinstance(t, dict):
                        neu(t.get("id"), "taetigkeit", t, pos.get("id"))
    for a in sd.abschluesse:
        neu(a.get("id"), "abschluss", a)
    for p in sd.projekte:
        neu(p.get("id"), "projekt", p)
    for s in sd.skills:
        neu(s.get("id"), "skill", s)
    for sp in sd.schwerpunkte:
        neu(sp.get("id"), "schwerpunkt", sp)
        pt = sp.get("profiltext")
        if isinstance(pt, dict):
            neu(pt.get("id"), "profiltext", pt, sp.get("id"))
    for bs in sd.bausteine:
        neu(bs.get("id"), "baustein", bs)
    if sd.rahmen:
        neu(RAHMEN_ID, "rahmen", sd.rahmen)


def verweis(sd: Stammdaten, id_, erwartet: str, ort: str, b: Befunde) -> bool:
    art = sd.art(id_) if isinstance(id_, str) else None
    if art is None:
        b.fehler_(ort, f"unbekannte ID '{id_}' (erwartet: {erwartet})")
        return False
    if art != erwartet:
        b.fehler_(ort, f"ID '{id_}' ist ein(e) {art}, erwartet: {erwartet}")
        return False
    return True


def pruefe_verweise(sd: Stammdaten, b: Befunde) -> None:
    for ag in sd.arbeitgeber:
        for pos in ag.get("positionen") or []:
            if not isinstance(pos, dict):
                continue
            ort = f"Position '{pos.get('id')}'"
            pruefe_zeitraum(pos.get("von"), pos.get("bis"), ort, b)
            pruefe_anlage(pos, ort, b)
            for t in pos.get("taetigkeiten") or []:
                if isinstance(t, dict):
                    pruefe_zuordnungen(sd, t, f"Tätigkeit '{t.get('id')}'", b)
    for p in sd.projekte:
        ort = f"Projekt '{p.get('id')}'"
        pruefe_zuordnungen(sd, p, ort, b)
        pruefe_zeitraum(p.get("von"), p.get("bis"), ort, b)
        if p.get("kontext") == "beruflich" and not p.get("position"):
            b.fehler_(ort, "Kontext 'beruflich' braucht einen Verweis 'position'")
        if p.get("position"):
            verweis(sd, p["position"], "position", f"{ort}.position", b)
    for a in sd.abschluesse:
        ort = f"Abschluss '{a.get('id')}'"
        pruefe_zeitraum(a.get("von"), a.get("bis"), ort, b)
        if a.get("status") == "abgeschlossen" and not a.get("bis"):
            b.fehler_(ort, "abgeschlossen, aber 'bis' (Datum des Abschlusses) fehlt")
        if a.get("status") == "laufend" and not a.get("von"):
            b.fehler_(ort, "laufend, aber 'von' fehlt")
        if a.get("position"):
            verweis(sd, a["position"], "position", f"{ort}.position", b)
        for s in a.get("skills") or []:
            verweis(sd, s, "skill", f"{ort}.skills", b)
        pruefe_anlage(a, ort, b)
    kategorien = [k.get("id") for k in sd.kategorien]
    for pflicht in (SPRACHE, ARBEITSWEISE):
        if sd.kategorien and pflicht not in kategorien:
            b.fehler_(rel(sd.ordner / "kategorien.yaml"), f"die Kategorie '{pflicht}' fehlt (sie hat eine feste Bedeutung)")
    if len(set(kategorien)) != len(kategorien):
        b.fehler_(rel(sd.ordner / "kategorien.yaml"), "eine Kategorie-ID ist doppelt vergeben")
    for s in sd.skills:
        if s.get("kategorie") and s["kategorie"] not in kategorien:
            b.fehler_(f"Skill '{s.get('id')}'.kategorie", f"unbekannte Kategorie '{s['kategorie']}' "
                                                         f"(vorhanden: {', '.join(map(str, kategorien))})")
        for sp in s.get("schwerpunkte") or []:
            verweis(sd, sp, "schwerpunkt", f"Skill '{s.get('id')}'.schwerpunkte", b)
    for feld, name in (("foto", "Foto"), ("unterschrift", "Unterschrift")):
        bild = sd.person.get(feld)
        if isinstance(bild, str) and not (sd.ordner / bild).exists():
            b.fehler_(rel(sd.ordner / "person.yaml"),
                      f"{name} '{bild}' nicht gefunden (Pfad relativ zum Stammdaten-Ordner)")
    for bs in sd.bausteine:
        for sp in bs.get("schwerpunkte") or []:
            verweis(sd, sp, "schwerpunkt", f"Baustein '{bs.get('id')}'.schwerpunkte", b)
    belegt = belegte_skills(sd)
    for s in sd.skills:
        if s.get("kategorie") == ARBEITSWEISE and s.get("id") not in belegt:
            b.warnung(f"Skill '{s.get('id')}'", "Arbeitsweise ohne Beleg – darf nicht in einen Lebenslauf")


def pruefe_anlage(obj: dict, ort: str, b: Befunde) -> None:
    """Anlagen (Zeugnisse, Urkunden) liegen relativ zum Daten-Ordner, meist unter anlagen/."""
    anlage = obj.get("anlage")
    if isinstance(anlage, str) and not (DATEN / anlage).exists():
        b.warnung(ort, f"Anlage '{anlage}' nicht gefunden")


def pruefe_zuordnungen(sd: Stammdaten, obj: dict, ort: str, b: Befunde) -> None:
    for sp in obj.get("schwerpunkte") or []:
        verweis(sd, sp, "schwerpunkt", f"{ort}.schwerpunkte", b)
    for s in obj.get("skills") or []:
        verweis(sd, s, "skill", f"{ort}.skills", b)


def pruefe_zeitraum(von, bis, ort: str, b: Befunde) -> None:
    if isinstance(von, str) and isinstance(bis, str) and bis != "heute" and MONAT_MUSTER.match(von) \
            and MONAT_MUSTER.match(bis) and bis < von:
        b.fehler_(ort, f"Zeitraum endet ({bis}) vor dem Beginn ({von})")


def belegte_skills(sd: Stammdaten) -> set[str]:
    """Skills, auf die eine Tätigkeit, ein Projekt oder ein Abschluss (Anlage) verweist."""
    belegt: set[str] = set()
    for art, obj, _ in sd.index.values():
        if art in ("taetigkeit", "projekt", "abschluss"):
            belegt.update(x for x in obj.get("skills") or [] if isinstance(x, str))
    return belegt


# --------------------------------------------------------------------------- Templates

class Gestaltung:
    """Geladene Templates, Grundlayouts und Schriften sowie das Standard-Template aus den Einstellungen."""

    def __init__(self) -> None:
        self.templates: dict[str, dict] = {}
        self.grundlayouts: dict[str, dict] = {}
        self.schriften: dict[str, dict] = {}
        self.standard = STANDARD_TEMPLATE


def lade_gestaltung(b: Befunde) -> Gestaltung:
    g = Gestaltung()
    lade_schriften(g, b)

    for meta in sorted(GRUNDLAYOUT_ORDNER.glob("*.yaml")):
        daten = lade_yaml(meta, b)
        if daten is None:
            continue
        pruefe_schema(daten, GRUNDLAYOUT_SCHEMA, rel(meta), b)
        for datei in (f"{meta.stem}.html.j2", f"{meta.stem}.anschreiben.html.j2"):
            if not (GRUNDLAYOUT_ORDNER / datei).exists():
                b.fehler_(rel(meta), f"Grundlayout-Datei {datei} fehlt")
        if isinstance(daten, dict):
            g.grundlayouts[meta.stem] = daten

    for pfad in sorted(TEMPLATE_ORDNER.glob("*.yaml")) + sorted(eigene_templates().glob("*.yaml")):
        ort = rel(pfad)
        if pfad.stem in g.templates:
            b.fehler_(ort, f"Template-Name '{pfad.stem}' gibt es schon (mitgeliefert und eigen dürfen nicht gleich heißen)")
            continue
        if not ID_MUSTER.match(pfad.stem):
            b.fehler_(ort, "ungültiger Template-Name (nur a–z, 0–9 und Bindestriche)")
        t = lade_yaml(pfad, b)
        if t is None:
            continue
        pruefe_schema(t, TEMPLATE_SCHEMA, ort, b)
        if not isinstance(t, dict):
            continue
        gl = g.grundlayouts.get(t.get("grundlayout"))
        if t.get("grundlayout") and gl is None:
            b.fehler_(f"{ort}.grundlayout", f"unbekanntes Grundlayout '{t['grundlayout']}' "
                                            f"(vorhanden: {', '.join(g.grundlayouts) or 'keins'})")
        position = (t.get("foto") or {}).get("position") if isinstance(t.get("foto"), dict) else None
        if gl and position and position not in (gl.get("foto_positionen") or []):
            b.fehler_(f"{ort}.foto.position", f"'{position}' ist bei Grundlayout '{t['grundlayout']}' nicht möglich "
                                              f"(möglich: {', '.join(gl.get('foto_positionen') or [])})")
        if gl and gl.get("weisser_text_auf_farbe") and isinstance(t.get("farbe"), str) \
                and FARB_MUSTER.match(t["farbe"]) and kontrast(t["farbe"], "#ffffff") < MIN_KONTRAST:
            b.fehler_(f"{ort}.farbe", f"'{t['farbe']}' ist zu hell für weißen Text "
                                      f"(Kontrast {kontrast(t['farbe'], '#ffffff'):.1f}, mindestens {MIN_KONTRAST})")
        if t.get("schrift") and t["schrift"] not in g.schriften:
            b.fehler_(f"{ort}.schrift", f"unbekannte Schrift '{t['schrift']}' (vorhanden: {', '.join(g.schriften)})")
        reihenfolge = t.get("reihenfolge")
        if isinstance(reihenfolge, list) and sorted(map(str, reihenfolge)) != sorted(ABSCHNITTE):
            b.fehler_(f"{ort}.reihenfolge", f"muss jeden Abschnitt genau einmal nennen ({', '.join(ABSCHNITTE)})")
        g.templates[pfad.stem] = t

    einstellungen = einstellungen_pfad()
    if einstellungen.exists():
        e = lade_yaml(einstellungen, b)
        if e is not None:
            pruefe_schema(e, EINSTELLUNGEN_SCHEMA, rel(einstellungen), b)
            if isinstance(e, dict) and e.get("template"):
                g.standard = e["template"]
    pruefe_template_name(g, g.standard, f"{rel(einstellungen)}.template", b)
    return g


def lade_schriften(g: Gestaltung, b: Befunde) -> None:
    pfad = SCHRIFTEN_ORDNER / "schriften.yaml"
    ort = rel(pfad)
    if not pfad.exists():
        b.fehler_(ort, "Datei fehlt")
        return
    daten = lade_yaml(pfad, b)
    if daten is None:
        return
    if not isinstance(daten, dict) or set(daten) != {"schriften"}:
        b.fehler_(ort, "erwartet genau einen Schlüssel 'schriften:' mit einer Liste")
        return
    liste = daten["schriften"] or []
    pruefe_wert(liste, ("liste", SCHRIFT_SCHEMA), f"{ort}:schriften", b)
    for s in liste if isinstance(liste, list) else []:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str):
            continue
        o = f"Schrift '{s['id']}'"
        if s["id"] in g.schriften:
            b.fehler_(o, "doppelt vergeben")
        g.schriften[s["id"]] = s
        # stack und name landen unescaped im CSS (Anführungszeichen müssen bleiben)
        for feld in ("stack", "name"):
            if isinstance(s.get(feld), str) and re.search(r"[<>{};\\]", s[feld]):
                b.fehler_(o, f"'{feld}' darf keines der Zeichen < > {{ }} ; \\ enthalten")
        if s.get("system"):
            continue
        if not s.get("lizenz"):
            b.fehler_(o, "Schrift aus dem Repo braucht 'lizenz' (nur freie Lizenzen wie SIL OFL)")
        if not s.get("dateien"):
            b.fehler_(o, "Schrift aus dem Repo braucht 'dateien' (sonst system: true setzen)")
        for d in s.get("dateien") or []:
            if isinstance(d, dict) and isinstance(d.get("datei"), str) and not (SCHRIFTEN_ORDNER / d["datei"]).exists():
                b.fehler_(o, f"Datei '{d['datei']}' fehlt in {rel(SCHRIFTEN_ORDNER)}")


def pruefe_template_name(g: Gestaltung, name, ort: str, b: Befunde) -> None:
    if name not in g.templates:
        b.fehler_(ort, f"unbekanntes Template '{name}' (vorhanden: {', '.join(g.templates) or 'keins'})")
    elif g.templates[name].get("veraltet"):
        b.warnung(ort, f"Template '{name}' ist als veraltet markiert")


def template_fuer(g: Gestaltung, ll: dict) -> str:
    """Reihenfolge: Feld im Lebenslauf (Entwurf übernimmt es vom Standardlebenslauf) > Einstellungen > klassisch."""
    return ll.get("template") or g.standard


def aufhellen(farbe: str, anteil: float) -> str:
    """Mischt die Farbe mit Weiß (anteil 0 = Farbe, 1 = Weiß)."""
    kanaele = [int(farbe[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(k + (255 - k) * anteil):02x}" for k in kanaele)


def kontrast(a: str, b: str) -> float:
    """Kontrastverhältnis zweier Farben nach WCAG (1 bis 21)."""
    def leuchtdichte(farbe: str) -> float:
        k = [int(farbe[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        k = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in k]
        return 0.2126 * k[0] + 0.7152 * k[1] + 0.0722 * k[2]
    hell, dunkel = sorted((leuchtdichte(a), leuchtdichte(b)), reverse=True)
    return (hell + 0.05) / (dunkel + 0.05)


def baue_stil(g: Gestaltung, name: str) -> tuple[str, dict]:
    """Liefert Grundlayout und die Parameter, die das Grundlayout als `stil` bekommt."""
    t = g.templates[name]
    schrift = g.schriften[t["schrift"]]
    return t["grundlayout"], {
        "name": name,
        "farbe": t["farbe"],
        "linienfarbe": t.get("linienfarbe") or aufhellen(t["farbe"], 0.75),
        "flaeche": aufhellen(t["farbe"], 0.92),  # getönte Flächen, z. B. Seitenleiste
        "auf_farbe_hell": aufhellen(t["farbe"], 0.85),  # Nebentext auf der Akzentfarbe (statt opacity)
        "auf_farbe_gedaempft": aufhellen(t["farbe"], 0.55),
        "schrift": {
            "name": schrift["name"], "stack": schrift["stack"],
            "dateien": [{"uri": (SCHRIFTEN_ORDNER / d["datei"]).resolve().as_uri(),
                         "gewicht": d["gewicht"], "stil": d["stil"]} for d in schrift.get("dateien") or []],
        },
        "foto": dict(t["foto"]),
        "ueberschriften": t["ueberschriften"],
        "reihenfolge": list(t["reihenfolge"]),
        "spalten": {s: [a for a in t["reihenfolge"] if a in abschnitte]
                    for s, abschnitte in g.grundlayouts[t["grundlayout"]]["spalten"].items()},
    }


# --------------------------------------------------------------------------- Lebenslauf

def normal(text: str) -> str:
    return " ".join(str(text).split())


FETT_MUSTER = re.compile(r"\*\*(.+?)\*\*")


def ohne_fett(text: str) -> str:
    return FETT_MUSTER.sub(r"\1", str(text))


def pruefe_aussage(sd: Stammdaten, a, erwartet: str, ort: str, b: Befunde, freigegeben) -> bool:
    """Prüft Quelle und Kennzeichnung einer Aussage. freigegeben(obj) liefert die freigegebenen Texte."""
    if not isinstance(a, dict) or not a.get("quelle"):
        return False  # schon als „Aussage ohne Quelle“ gemeldet
    if not verweis(sd, a["quelle"], erwartet, f"{ort}.quelle", b):
        return False
    obj = sd.obj(a["quelle"])
    if obj.get("veraltet"):
        b.warnung(ort, f"'{a['quelle']}' ist als veraltet markiert")
    if a.get("umformuliert") and not a.get("text"):
        b.fehler_(ort, "umformuliert: true, aber kein 'text' angegeben")
    if a.get("text"):
        ist_freigegeben = normal(ohne_fett(a["text"])) in {normal(ohne_fett(t)) for t in freigegeben(obj)}
        if not a.get("umformuliert") and not ist_freigegeben:
            b.fehler_(ort, f"Text weicht von den Stammdaten zu '{a['quelle']}' ab – "
                           "als 'umformuliert: true' kennzeichnen oder freigegebenen Text verwenden")
        if a.get("umformuliert") and ist_freigegeben:
            b.warnung(ort, f"Text zu '{a['quelle']}' ist inzwischen freigegeben – 'umformuliert: true' entfernen")
    return True


def freigegebene_texte(obj: dict) -> list[str]:
    return [obj.get("kernaussage") or obj.get("text") or ""] + list(obj.get("formulierungen") or [])


def pruefe_lebenslauf(sd: Stammdaten, ordner: Path, b: Befunde, g: Gestaltung | None = None) -> dict | None:
    pfad = ordner / "lebenslauf.yaml"
    ort = rel(pfad)
    if not pfad.exists():
        b.fehler_(ort, "Datei fehlt")
        return None
    ll = lade_yaml(pfad, b)
    if ll is None:
        return None
    pruefe_schema(ll, LEBENSLAUF, ort, b)
    if not isinstance(ll, dict):
        return None

    if ll.get("schwerpunkt"):
        verweis(sd, ll["schwerpunkt"], "schwerpunkt", f"{ort}.schwerpunkt", b)
    if g is not None and isinstance(ll.get("template"), str):
        pruefe_template_name(g, ll["template"], f"{ort}.template", b)
    if isinstance(ll.get("profil"), dict):
        pruefe_aussage(sd, ll["profil"], "profiltext", f"{ort}.profil", b, freigegebene_texte)

    gesehen: set[str] = set()

    def einmal(id_, o):
        if id_ in gesehen:
            b.fehler_(o, f"'{id_}' ist doppelt gewählt")
        gesehen.add(id_)

    gewaehlte_ag = set()
    for i, eintrag in enumerate(ll.get("berufserfahrung") or []):
        if not isinstance(eintrag, dict):
            continue
        o = f"{ort}.berufserfahrung[{i}]"
        ag = eintrag.get("arbeitgeber")
        if not verweis(sd, ag, "arbeitgeber", f"{o}.arbeitgeber", b):
            continue
        einmal(ag, o)
        gewaehlte_ag.add(ag)
        for j, t in enumerate(eintrag.get("taetigkeiten") or []):
            ot = f"{o}.taetigkeiten[{j}]"
            if pruefe_aussage(sd, t, "taetigkeit", ot, b, freigegebene_texte):
                einmal(t["quelle"], ot)
                if sd.eltern(sd.eltern(t["quelle"])) != ag:
                    b.fehler_(ot, f"Tätigkeit '{t['quelle']}' gehört nicht zum Arbeitgeber '{ag}'")
    for a in sd.arbeitgeber:
        if a.get("id") not in gewaehlte_ag and not a.get("veraltet"):
            b.warnung(ort, f"Arbeitgeber '{a.get('id')}' fehlt in der Berufserfahrung (Lücke im Lebenslauf?)")

    belegt = belegte_skills(sd)
    for i, s in enumerate(ll.get("kenntnisse") or []):
        o = f"{ort}.kenntnisse[{i}]"
        if not verweis(sd, s, "skill", o, b):
            continue
        einmal(s, o)
        skill = sd.obj(s)
        if skill.get("kategorie") == SPRACHE:
            b.warnung(o, f"'{s}' ist eine gesprochene Sprache – die stehen immer im Lebenslauf, Eintrag wird ignoriert")
        if skill.get("kategorie") == ARBEITSWEISE and s not in belegt:
            b.fehler_(o, f"'{s}' (Arbeitsweise) hat keinen Beleg und darf nicht in den Lebenslauf")
        if skill.get("veraltet"):
            b.warnung(o, f"'{s}' ist als veraltet markiert")

    for i, p in enumerate(ll.get("projekte") or []):
        o = f"{ort}.projekte[{i}]"
        if pruefe_aussage(sd, p, "projekt", o, b, freigegebene_texte):
            einmal(p["quelle"], o)

    schalter = ll.get("schalter") or {}
    if schalter.get("foto", True) and not sd.person.get("foto"):
        b.warnung(ort, "Foto ist eingeschaltet, aber person.yaml hat kein 'foto'")
    pruefe_fett(sd, ll, ort, b)
    return ll


def pruefe_fett(sd: Stammdaten, ll: dict, ort: str, b: Befunde) -> None:
    """Gleicht das Fett in Profil, Tätigkeiten und Projekten mit der Liste 'fett' ab (Treffer der Stellenausschreibung).

    Fehler: ein Begriff der Liste ist nirgends fett, oder etwas ist fett, das nicht in der Liste steht.
    Warnung: ein Begriff ist innerhalb eines Bereichs (Profil, Berufserfahrung, Projekte) mehrmals fett.
    Ohne Feld 'fett' (Standardlebensläufe, ältere Bewerbungen) wird nichts geprüft.
    """
    liste = ll.get("fett")
    if not isinstance(liste, list):
        return
    o = f"{ort}.fett"

    def schluessel(text: str) -> str:
        return normal(text).casefold()

    erwartet: dict[str, str] = {}
    for x in liste:
        if not isinstance(x, str):
            continue  # schon von der Schemaprüfung gemeldet
        if schluessel(x) in erwartet:
            b.fehler_(o, f"'{x}' steht doppelt in der Liste")
        erwartet.setdefault(schluessel(x), x)

    taetigkeiten = [t for e in ll.get("berufserfahrung") or [] if isinstance(e, dict)
                    for t in e.get("taetigkeiten") or []]
    bereiche = {"im Profil": [ll.get("profil")], "in der Berufserfahrung": taetigkeiten,
                "in den Projekten": list(ll.get("projekte") or [])}
    gefunden: set[str] = set()
    for bereich, aussagen in bereiche.items():
        anzahl: dict[str, int] = {}
        for a in aussagen:
            if not isinstance(a, dict) or not isinstance(a.get("quelle"), str) or sd.art(a["quelle"]) is None:
                continue  # schon als ungültige Aussage gemeldet
            for span in FETT_MUSTER.findall(aussage_text(sd, a)["text"] or ""):
                k = schluessel(span)
                anzahl[k] = anzahl.get(k, 0) + 1
                if k not in erwartet:
                    b.fehler_(o, f"'{normal(span)}' ist fett ({a['quelle']}), steht aber nicht in 'fett' – "
                                 "nur Treffer der Stellenausschreibung fett setzen oder den Begriff ergänzen")
        for k, n in anzahl.items():
            if n > 1 and k in erwartet:
                b.warnung(o, f"'{erwartet[k]}' ist {bereich} {n}-mal fett – nur beim ersten Vorkommen fett setzen")
        gefunden |= anzahl.keys()
    for k, x in erwartet.items():
        if k not in gefunden:
            b.fehler_(o, f"'{x}' steht in 'fett', ist aber nirgends fett – als **{x}** in Profil, Tätigkeit oder "
                         "Projekt setzen oder aus der Liste nehmen")


# --------------------------------------------------------------------------- Anschreiben

PLATZHALTER_MUSTER = re.compile(r"\[[^\[\]\n]{1,40}\]")   # z. B. [Firma] im Standardanschreiben
DATUM_MUSTER = re.compile(r"^(19|20)\d\d-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
GENDER_MUSTER = re.compile(r"\s*\(\s*[a-z]{1,3}(\s*/\s*[a-z]{1,3}){1,3}\s*\)", re.IGNORECASE)   # (m/w/d) usw.
MONATSNAMEN = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
               "November", "Dezember"]


def absatz_text(sd: Stammdaten, a: dict) -> str:
    """Eigener Text des Absatzes, sonst der freigegebene Text seiner einzigen Quelle; immer ohne Fett."""
    if a.get("text"):
        return ohne_fett(a["text"])
    quellen = a.get("quellen") or []
    return ohne_fett(freigegebene_texte(sd.obj(quellen[0]))[0]) if quellen else ""


def pruefe_anschreiben(sd: Stammdaten, ordner: Path, b: Befunde) -> dict | None:
    """Prüft <ordner>/anschreiben.yaml (und bewerbung.yaml, falls vorhanden).

    Jeder Absatz hat Quellen aus den Stammdaten oder eine Herkunft (anzeige, nutzer), ein Hauptteil immer Quellen.
    Texte, die von den freigegebenen Texten ihrer Quellen abweichen, sind als umformuliert gekennzeichnet.
    """
    pfad = ordner / "anschreiben.yaml"
    ort = rel(pfad)
    an = lade_yaml(pfad, b)
    if an is None:
        return None
    pruefe_schema(an, ANSCHREIBEN, ort, b)
    if not isinstance(an, dict):
        return None
    if not (ordner / "lebenslauf.yaml").exists():
        b.fehler_(ort, "im selben Ordner fehlt lebenslauf.yaml – das Anschreiben übernimmt dessen Template")

    bew = None
    bpfad = ordner / "bewerbung.yaml"
    if bpfad.exists():
        bew = lade_yaml(bpfad, b)
        if bew is not None:
            pruefe_schema(bew, BEWERBUNG, rel(bpfad), b)
        if not isinstance(bew, dict):
            bew = None

    belegt = belegte_skills(sd)
    texte = []
    absaetze = an.get("absaetze") if isinstance(an.get("absaetze"), list) else []
    for i, a in enumerate(absaetze):
        o = f"{ort}.absaetze[{i}]"
        if not isinstance(a, dict):
            continue  # schon von der Schemaprüfung gemeldet
        quellen = [q for q in a.get("quellen") or [] if isinstance(q, str)]
        if not quellen and not a.get("herkunft"):
            b.fehler_(o, "Absatz ohne Herkunft – 'quellen: [IDs]' aus den Stammdaten oder "
                         "'herkunft: anzeige | nutzer' angeben")
            continue
        if a.get("art") == "hauptteil" and not quellen:
            b.fehler_(o, "ein Absatz 'hauptteil' braucht mindestens eine Quelle aus den Stammdaten")
        gueltig = True
        for q in quellen:
            art = sd.art(q)
            if art is None:
                b.fehler_(f"{o}.quellen", f"unbekannte ID '{q}'")
                gueltig = False
                continue
            if art not in ABSATZ_QUELLEN:
                b.fehler_(f"{o}.quellen", f"ID '{q}' ist ein(e) {art} und kann keine Quelle eines Absatzes sein")
                gueltig = False
                continue
            obj = sd.obj(q)
            if obj.get("veraltet"):
                b.warnung(o, f"'{q}' ist als veraltet markiert")
            if art == "skill" and obj.get("kategorie") == ARBEITSWEISE and q not in belegt:
                b.fehler_(o, f"'{q}' (Arbeitsweise) hat keinen Beleg und darf nicht ins Anschreiben")
            if art == "baustein" and obj.get("art") != a.get("art"):
                b.warnung(o, f"Baustein '{q}' ist für '{obj.get('art')}' gedacht, der Absatz ist '{a.get('art')}'")
        if not gueltig:
            continue

        text = a.get("text")
        if isinstance(text, str) and "**" in text:
            b.fehler_(o, "im Anschreiben gibt es kein Fett – '**' entfernen")
        if not text:
            if a.get("umformuliert"):
                b.fehler_(o, "umformuliert: true, aber kein 'text' angegeben")
            if len(quellen) != 1 or not freigegebene_texte(sd.obj(quellen[0]))[0]:
                b.fehler_(o, "Absatz ohne 'text' – geht nur mit genau einer Quelle, die einen freigegebenen Text hat "
                             "(Baustein, Tätigkeit, Projekt, Profiltext)")
                continue
        elif quellen:
            freigegeben = {normal(ohne_fett(t)) for q in quellen for t in freigegebene_texte(sd.obj(q)) if t}
            ist_freigegeben = normal(ohne_fett(text)) in freigegeben
            if not a.get("umformuliert") and not ist_freigegeben:
                b.fehler_(o, f"Text weicht von den Stammdaten zu {', '.join(quellen)} ab – als 'umformuliert: true' "
                             "kennzeichnen oder freigegebenen Text verwenden")
            if a.get("umformuliert") and ist_freigegeben:
                b.warnung(o, "Text ist inzwischen freigegeben – 'umformuliert: true' entfernen")
        elif a.get("umformuliert"):
            b.warnung(o, "'umformuliert' gilt nur für Absätze mit Quellen – bei reiner Herkunft weglassen")
        texte.append(absatz_text(sd, a))

    woerter = len(" ".join(texte).split())
    if texte and not ANSCHREIBEN_WOERTER[0] <= woerter <= ANSCHREIBEN_WOERTER[1]:
        b.warnung(ort, f"{woerter} Wörter im Brieftext – Ziel sind etwa 250–350")
    if bew is not None:
        anrede = (bew.get("empfaenger") or {}).get("anrede") if isinstance(bew.get("empfaenger"), dict) else None
        for t in texte + [x for x in (an.get("betreff"), anrede) if isinstance(x, str)]:
            for p in PLATZHALTER_MUSTER.findall(t):
                b.fehler_(ort, f"Platzhalter {p} ist noch nicht ersetzt")
    return {"anschreiben": an, "bewerbung": bew}


def briefdatum(bew: dict) -> date | None:
    """Das Datum aus bewerbung.yaml (Tag der Freigabe), solange es noch ein Platzhalter ist: None."""
    datum = bew.get("datum")
    if isinstance(datum, date):   # YAML liest ein Datum ohne Anführungszeichen als date
        return datum
    if isinstance(datum, str) and DATUM_MUSTER.match(datum):
        try:
            return date.fromisoformat(datum)
        except ValueError:
            return None
    return None


def datum_lang(tag: date) -> str:
    return f"{tag.day}. {MONATSNAMEN[tag.month - 1]} {tag.year}"


def baue_anschreiben_kontext(sd: Stammdaten, ll: dict, an: dict, bew: dict | None, heute: date) -> dict:
    """Aufbereitete Daten für ein Anschreiben-Gegenstück. Ohne bewerbung.yaml stehen Platzhalter darin."""
    p = sd.person
    ort_zeile = " ".join(str(x) for x in (p.get("plz"), p["wohnort"]) if x)
    adresse = [p["strasse"], ort_zeile] if p.get("strasse") else [ort_zeile]
    kontakt = [x for x in (p.get("telefon"), p.get("email")) if x] + list(p.get("web") or [])

    if bew:
        e = bew.get("empfaenger") or {}
        stelle = GENDER_MUSTER.sub("", str(bew["stelle"])).strip()
        empfaenger = [bew["firma"], e.get("abteilung"), e.get("ansprechperson"), e.get("strasse"),
                      " ".join(str(x) for x in (e.get("plz"), e.get("ort")) if x)]
        anrede = e.get("anrede") or "Sehr geehrte Damen und Herren,"
        kennziffer = bew.get("kennziffer")
        tag = briefdatum(bew) or heute
    else:
        stelle, empfaenger, anrede, kennziffer, tag = "[Stelle]", ["[Firma]"], "Sehr geehrte Damen und Herren,", None, heute
    if not anrede.rstrip().endswith(","):
        anrede = anrede.rstrip() + ","

    schalter = an.get("schalter") or {}
    unterschrift = None
    if schalter.get("unterschrift", True) and p.get("unterschrift"):
        unterschrift = (sd.ordner / p["unterschrift"]).resolve().as_uri()

    return {
        "person": {"name": p["name"], "adresse": adresse, "kontakt": kontakt,
                   "kontakt_zeile": [", ".join(adresse)] + kontakt},
        "ruecksende": " · ".join([p["name"], *adresse]) if p.get("strasse") else None,
        "untertitel": ll.get("untertitel"),
        "empfaenger": [z for z in empfaenger if z],
        "ort_datum": f"{p['wohnort']}, {datum_lang(tag)}",
        "betreff": an.get("betreff") or f"Bewerbung als {stelle}",
        "kennziffer": kennziffer,
        "anrede": anrede,
        "absaetze": [{"art": a["art"], "text": absatz_text(sd, a), "quellen": " ".join(a.get("quellen") or []),
                      "herkunft": a.get("herkunft"), "umformuliert": bool(a.get("umformuliert"))}
                     for a in an["absaetze"]],
        "gruss": "Mit freundlichen Grüßen",
        "unterschrift": unterschrift,
    }


# --------------------------------------------------------------------------- Aufbereitung

def monat(m: str) -> str:
    return "heute" if m == "heute" else f"{m[5:7]}/{m[:4]}"


def zeitraum(von: str | None, bis: str | None) -> str:
    if von and bis:
        return f"{monat(von)} – {monat(bis)}"
    return monat(von or bis) if (von or bis) else ""


def neueste_zuerst(positionen: list[dict]) -> list[dict]:
    return sorted(positionen, key=lambda p: ("9999-99" if p["bis"] == "heute" else p["bis"], p["von"]), reverse=True)


def aussage_text(sd: Stammdaten, a: dict) -> dict:
    obj = sd.obj(a["quelle"])
    text = a.get("text") or obj.get("kernaussage") or obj.get("text")
    return {"quelle": a["quelle"], "text": text, "umformuliert": bool(a.get("umformuliert"))}


def baue_kontext(sd: Stammdaten, ll: dict) -> dict:
    p = sd.person
    schalter = ll.get("schalter") or {}
    einzeln = schalter.get("positionen") == "einzeln"

    berufserfahrung = []
    for eintrag in ll.get("berufserfahrung") or []:
        ag = sd.obj(eintrag["arbeitgeber"])
        organisation = ag["name"] + (f", {ag['ort']}" if ag.get("ort") else "")
        positionen = neueste_zuerst(ag["positionen"])
        taets = [aussage_text(sd, t) for t in eintrag.get("taetigkeiten") or []]
        if einzeln:
            for pos in positionen:
                berufserfahrung.append({
                    "quelle": pos["id"], "titel": pos["titel"], "organisation": organisation,
                    "zeitraum": zeitraum(pos["von"], pos["bis"]), "zuvor": "",
                    "taetigkeiten": [t for t in taets if sd.eltern(t["quelle"]) == pos["id"]],
                })
        else:
            neueste, frueher = positionen[0], positionen[1:]
            zuvor = list(dict.fromkeys(x["art"] for x in frueher))
            berufserfahrung.append({
                "quelle": ag["id"], "titel": neueste["titel"], "organisation": organisation,
                "zeitraum": zeitraum(min(x["von"] for x in positionen), neueste["bis"]),
                "zuvor": ", ".join(zuvor), "taetigkeiten": taets,
            })

    abschluesse = []
    # neueste zuerst: laufende oben, sonst nach Enddatum (ersatzweise Beginn), unabhängig von der Reihenfolge in der YAML
    for a in sorted(sd.abschluesse, reverse=True,
                    key=lambda a: ("9999-99" if a["status"] == "laufend" else a.get("bis") or a.get("von") or "",
                                   a.get("von") or "")):
        if a.get("veraltet"):
            continue
        titel = a["bezeichnung"] + (" (laufend)" if a["status"] == "laufend" else "")
        if a.get("note") is not None:
            titel += f" ({a['note']})"
        zr = f"seit {monat(a['von'])}" if a["status"] == "laufend" else zeitraum(a.get("von"), a.get("bis"))
        abschluesse.append({"quelle": a["id"], "titel": titel, "institution": a["institution"],
                            "zeitraum": zr})

    gruppen: dict[str, list] = {}
    for s in ll.get("kenntnisse") or []:
        skill = sd.obj(s)
        if skill["kategorie"] != SPRACHE:
            gruppen.setdefault(skill["kategorie"], []).append({"quelle": s, "name": skill["name"]})
    kenntnisse = [{"kategorie": k["name"], "skills": gruppen[k["id"]]} for k in sd.kategorien
                  if k["id"] in gruppen]
    sprachen_titel = next((k["name"] for k in sd.kategorien if k["id"] == SPRACHE), "Sprachen")
    sprachen = [{"quelle": s["id"], "name": s["name"], "niveau": s["niveau"]}
                for s in sd.skills if s["kategorie"] == SPRACHE and not s.get("veraltet")]

    projekte = []
    for a in ll.get("projekte") or []:
        proj = sd.obj(a["quelle"])
        projekte.append({**aussage_text(sd, a), "titel": proj["titel"],
                         "zeitraum": zeitraum(proj.get("von"), proj.get("bis"))})

    foto = None
    if schalter.get("foto", True) and p.get("foto"):
        foto = (sd.ordner / p["foto"]).resolve().as_uri()

    kontakt = [x for x in (p.get("wohnort"), p.get("telefon"), p.get("email")) if x] + list(p.get("web") or [])
    return {
        "person": {"name": p["name"], "kontakt": kontakt},
        "untertitel": ll.get("untertitel"),
        "profil": aussage_text(sd, ll["profil"]) if ll.get("profil") else None,
        "foto": foto,
        "berufserfahrung": berufserfahrung,
        "abschluesse": abschluesse,
        "kenntnisse": kenntnisse,
        "sprachen": sprachen,
        "sprachen_titel": sprachen_titel,
        "projekte": projekte,
    }


def auszeichnung(text: str) -> markupsafe.Markup:
    """Escaped den Text und erlaubt **fett** als einzige Auszeichnung."""
    sicher = str(markupsafe.escape(text))
    return markupsafe.Markup(FETT_MUSTER.sub(r"<b>\1</b>", sicher))


def rendere_html(kontext: dict, grundlayout: str, stil: dict, anschreiben: bool = False) -> str:
    """Lebenslauf (<grundlayout>.html.j2) oder Anschreiben (<grundlayout>.anschreiben.html.j2)."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(GRUNDLAYOUT_ORDNER),
        autoescape=True, undefined=jinja2.StrictUndefined,
    )
    env.filters["auszeichnung"] = auszeichnung
    datei = f"{grundlayout}.anschreiben.html.j2" if anschreiben else f"{grundlayout}.html.j2"
    return env.get_template(datei).render(**kontext, stil=stil)


# --------------------------------------------------------------------------- PDF

def chrome_zusatz() -> list[str]:
    """Zusätzliche Chrome-Argumente aus der Umgebungsvariable CHROME_ARGS, z. B. --no-sandbox in Containern."""
    return os.environ.get("CHROME_ARGS", "").split()


def finde_chrome() -> str:
    for kandidat in CHROME_KANDIDATEN:
        if kandidat and Path(kandidat).exists():
            return kandidat
    raise SystemExit("FEHLER   Chrome, Edge oder Chromium nicht gefunden – installieren oder den Pfad "
                     "über die Umgebungsvariable CHROME setzen")


def drucke_pdf(html: str, ziel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="lebenslauf-") as tmp:
        tmp = Path(tmp)
        html_pfad = tmp / "lebenslauf.html"
        html_pfad.write_text(html, encoding="utf-8")
        pdf_tmp = tmp / "lebenslauf.pdf"
        befehl = [
            finde_chrome(), *chrome_zusatz(), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={tmp / 'profil'}", "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_tmp}", html_pfad.as_uri(),
        ]
        erg = subprocess.run(befehl, capture_output=True, text=True, timeout=120)
        if erg.returncode != 0 or not pdf_tmp.exists():
            print(erg.stderr[-2000:], file=sys.stderr)
            raise SystemExit(2)
        shutil.copyfile(pdf_tmp, ziel)


# Misst im Browser die Höhe jeder mit data-spalte markierten Spalte (Bildschirmansicht: gleiche Breite wie im Druck).
MESS_SKRIPT = """<script>
document.fonts.ready.then(() => {
  for (const el of document.querySelectorAll('[data-spalte]'))
    el.setAttribute('data-hoehe-mm', (el.getBoundingClientRect().height * 25.4 / 96).toFixed(1));
  document.body.setAttribute('data-gemessen', 'ja');
});
</script>"""
SPALTEN_TOLERANZ_MM = 2.0
SEITEN_NUTZHOEHE_MM = 297 - 11 - 9  # A4 minus Rand oben/unten der Grundlayouts


def miss_spalten(html: str) -> dict[str, float]:
    """Höhe jeder Spalte in mm; leer, wenn das Grundlayout keine Spalten markiert."""
    if "data-spalte=" not in html:
        return {}
    with tempfile.TemporaryDirectory(prefix="lebenslauf-mess-") as tmp:
        tmp = Path(tmp)
        html_pfad = tmp / "messen.html"
        html_pfad.write_text(html.replace("</body>", MESS_SKRIPT + "</body>"), encoding="utf-8")
        befehl = [
            finde_chrome(), *chrome_zusatz(), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={tmp / 'profil'}", "--window-size=1000,1400", "--virtual-time-budget=5000",
            "--dump-dom", html_pfad.as_uri(),
        ]
        erg = subprocess.run(befehl, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if 'data-gemessen="ja"' not in erg.stdout:
        print("WARNUNG  Spaltenhöhen konnten nicht gemessen werden – Überlauf der Spalten bitte im PDF prüfen")
        return {}
    hoehen = {}
    for tag in re.findall(r"<[^>]*data-spalte=[^>]*>", erg.stdout):
        name, hoehe = re.search(r'data-spalte="([^"]+)"', tag), re.search(r'data-hoehe-mm="([\d.]+)"', tag)
        if name and hoehe:
            hoehen[name.group(1)] = float(hoehe.group(1))
    return hoehen


def pruefe_spalten(hoehen: dict[str, float]) -> None:
    """Eine Nebenspalte darf nicht länger sein als die Hauptspalte, sonst bestimmt sie die Seitenzahl."""
    haupt = hoehen.get("haupt")
    if haupt is None:
        return
    print("SPALTEN  " + ", ".join(f"{n} {h:.0f} mm" for n, h in hoehen.items()))
    seiten = lambda h: math.ceil(h / SEITEN_NUTZHOEHE_MM)  # noqa: E731 – grob, ohne Seitenumbruch-Verschnitt
    for name, hoehe in hoehen.items():
        if name == "haupt" or hoehe <= haupt + SPALTEN_TOLERANZ_MM:
            continue
        if seiten(hoehe) > seiten(haupt):
            print(f"WARNUNG  Spalte '{name}' ist {hoehe - haupt:.0f} mm länger als die Hauptspalte und braucht eine "
                  f"Seite mehr – dort kürzen (z. B. Kenntnisse), nicht in der Hauptspalte")
        else:
            print(f"HINWEIS  Spalte '{name}' ist {hoehe - haupt:.0f} mm länger als die Hauptspalte (wirkt unausgewogen)")


def pruefe_pdf(pdf: Path, name: str, max_seiten: int = MAX_SEITEN) -> bool:
    """Seitenzahl und Textextrahierbarkeit (ATS). Gibt False bei Fehlern zurück."""
    reader = PdfReader(pdf)
    seiten = len(reader.pages)
    texte = [(s.extract_text() or "") for s in reader.pages]
    zeichen = sum(len(normal(t)) for t in texte)
    ok = True
    print(f"PDF      {rel(pdf)}: {seiten} Seite{'n' if seiten != 1 else ''}, {zeichen} Zeichen extrahierbar")
    if seiten > max_seiten:
        print(f"FEHLER   {seiten} Seiten – höchstens {max_seiten} erlaubt, bitte kürzen")
        ok = False
    if zeichen == 0:
        print("FEHLER   kein Text extrahierbar – das PDF ist für ATS unbrauchbar")
        ok = False
    elif normal(name) not in normal(" ".join(texte)):
        print(f"WARNUNG  Name '{name}' im extrahierten Text nicht gefunden – Textextraktion prüfen")
    if seiten == 2 and texte[0] and max_seiten >= 2:
        fuellung = len(normal(texte[1])) / max(1, len(normal(texte[0])))
        if fuellung < 0.35:
            print(f"WARNUNG  Seite 2 ist nur zu etwa {fuellung:.0%} gefüllt – auf 1 Seite kürzen oder auffüllen")
    return ok


# --------------------------------------------------------------------------- Ablauf

def standard_ordner() -> list[Path]:
    ordner = sorted(p.parent for p in (DATEN / "standard").glob("*/lebenslauf.yaml"))
    if (ENTWURF / "lebenslauf.yaml").exists():
        ordner.append(ENTWURF)
    return ordner


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lebenslauf und Anschreiben aus Stammdaten rendern und prüfen.")
    ap.add_argument("ordner", nargs="*", type=Path, help="Ordner mit lebenslauf.yaml (und optional anschreiben.yaml)")
    ap.add_argument("--pruefen", action="store_true", help="nur prüfen, kein PDF erzeugen")
    ap.add_argument("--daten", type=Path, default=REPO / "daten",
                    help="Daten-Ordner mit stammdaten/, standard/, einstellungen.yaml … (Standard: daten/)")
    ap.add_argument("--html", action="store_true",
                    help="zusätzlich lebenslauf.html bzw. anschreiben.html (mit data-quelle) in den Ordner schreiben")
    ap.add_argument("--nur-anschreiben", action="store_true",
                    help="nur das Anschreiben rendern, den Lebenslauf nicht anfassen (z. B. bei der Freigabe)")
    ap.add_argument("--vorschau", metavar="TEMPLATE",
                    help="die Lebensläufe und Anschreiben (Standard: alle Standardlebensläufe) mit diesem Template nach "
                         "vorschau/<ordner>/ rendern, ohne ihre YAML-Dateien oder PDFs zu ändern")
    args = ap.parse_args(argv)

    if args.pruefen and args.vorschau:
        ap.error("--pruefen und --vorschau nicht zusammen verwenden")
    if not args.pruefen and not args.vorschau and len(args.ordner) != 1:
        ap.error("genau einen Ordner angeben oder --pruefen bzw. --vorschau verwenden")
    if args.nur_anschreiben and (args.pruefen or args.vorschau):
        ap.error("--nur-anschreiben nur zusammen mit genau einem Ordner verwenden")

    global DATEN
    DATEN = args.daten.resolve()
    if not stammdaten_ordner().is_dir():
        print(f"FEHLER   {rel(stammdaten_ordner())} fehlt – noch nicht eingerichtet? Den Skill „einrichten“ verwenden "
              f"oder mit --daten beispiel die Beispieldaten nehmen.")
        return 1
    version = lies_version(DATEN)
    if version < SCHEMAVERSION:
        print(f"FEHLER   {rel(DATEN)} hat Schema {version}, das System erwartet {SCHEMAVERSION} – "
              f"zuerst migrieren: python einrichten.py --migrieren")
        return 1
    if version > SCHEMAVERSION:
        print(f"FEHLER   {rel(DATEN)} hat Schema {version}, dieses System kennt nur bis {SCHEMAVERSION} – "
              f"System aktualisieren: python einrichten.py --aktualisieren")
        return 1

    b = Befunde()
    sd = lade_stammdaten(stammdaten_ordner(), b)
    g = lade_gestaltung(b)
    if args.vorschau:
        pruefe_template_name(g, args.vorschau, "--vorschau", b)
        ordner_liste = args.ordner or [o for o in standard_ordner() if o != ENTWURF]
    else:
        ordner_liste = args.ordner or (standard_ordner() if args.pruefen else [])
    lebenslaeufe, anschreiben = {}, {}
    if not b.fehler:
        lebenslaeufe = {o: pruefe_lebenslauf(sd, o, b, g) for o in ordner_liste}
        anschreiben = {o: pruefe_anschreiben(sd, o, b) for o in ordner_liste if (o / "anschreiben.yaml").exists()}
    if args.nur_anschreiben and not anschreiben:
        b.fehler_(rel(args.ordner[0] / "anschreiben.yaml"), "Datei fehlt")
    b.ausgeben()
    if b.fehler:
        print(f"Prüfung fehlgeschlagen: {len(b.fehler)} Fehler, {len(b.warnungen)} Warnungen.")
        return 1
    geprueft = ", ".join(rel(o) + (" (mit Anschreiben)" if o in anschreiben else "") for o in ordner_liste)         or "keine Lebensläufe"
    print(f"Prüfung bestanden ({rel(stammdaten_ordner())}; {geprueft}; {len(b.warnungen)} Warnungen).")
    if args.pruefen:
        return 0

    if args.vorschau:
        ergebnisse = []
        for ordner in ordner_liste:
            ziel = VORSCHAU / ordner.name
            ziel.mkdir(parents=True, exist_ok=True)
            print()
            ll = lebenslaeufe[ordner]
            ergebnisse.append((ziel / "lebenslauf.pdf", ordner,
                               rendere_lebenslauf(sd, g, ll, args.vorschau, ziel, args.html)))
            if ordner in anschreiben:
                ergebnisse.append((ziel / "anschreiben.pdf", ordner,
                                   rendere_anschreiben(sd, g, ll, anschreiben[ordner], args.vorschau, ziel, args.html)))
        print()
        for pdf, ordner, ok in ergebnisse:
            seiten = len(PdfReader(pdf).pages)
            print(f"VORSCHAU {rel(ordner)} -> {rel(pdf)}: {seiten} Seite{'n' if seiten != 1 else ''}, "
                  f"{'in Ordnung' if ok else 'FEHLER'}")
        return 0 if all(ok for _, _, ok in ergebnisse) else 2

    ordner = args.ordner[0]
    ll = lebenslaeufe[ordner]
    template = template_fuer(g, ll)
    ok = True
    if not args.nur_anschreiben:
        ok = rendere_lebenslauf(sd, g, ll, template, ordner, args.html)
    if ordner in anschreiben:
        print()
        ok = rendere_anschreiben(sd, g, ll, anschreiben[ordner], template, ordner, args.html) and ok
    return 0 if ok else 2


def rendere_lebenslauf(sd: Stammdaten, g: Gestaltung, ll: dict, template: str, ziel: Path, mit_html: bool) -> bool:
    """Rendert ll mit dem Template nach ziel/lebenslauf.pdf und prüft das PDF. False bei Fehlern."""
    grundlayout, stil = baue_stil(g, template)
    print(f"TEMPLATE {template} (Grundlayout {grundlayout})")
    html = rendere_html(baue_kontext(sd, ll), grundlayout, stil)
    if mit_html:
        (ziel / "lebenslauf.html").write_text(html, encoding="utf-8")
    pdf = ziel / "lebenslauf.pdf"
    drucke_pdf(html, pdf)
    ok = pruefe_pdf(pdf, sd.person["name"])
    pruefe_spalten(miss_spalten(html))
    return ok


def rendere_anschreiben(sd: Stammdaten, g: Gestaltung, ll: dict, ab: dict, template: str, ziel: Path,
                        mit_html: bool) -> bool:
    """Rendert das Anschreiben (Ergebnis von pruefe_anschreiben) nach ziel/anschreiben.pdf: genau 1 Seite."""
    grundlayout, stil = baue_stil(g, template)
    print(f"ANSCHREIBEN {template} (Grundlayout {grundlayout})")
    kontext = baue_anschreiben_kontext(sd, ll, ab["anschreiben"], ab["bewerbung"], date.today())
    html = rendere_html(kontext, grundlayout, stil, anschreiben=True)
    if mit_html:
        (ziel / "anschreiben.html").write_text(html, encoding="utf-8")
    pdf = ziel / "anschreiben.pdf"
    drucke_pdf(html, pdf)
    return pruefe_pdf(pdf, sd.person["name"], max_seiten=1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Umlaute auch in der Windows-Konsole
    sys.exit(main())
