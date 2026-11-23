# Spezifikation: Bewerbungs-Werkstatt

Jeder Abschnitt fasst eine Entscheidung zusammen. Begriffe: [GLOSSARY.md](GLOSSARY.md). Bei Abweichungen zwischen dieser Datei und `render.py` gilt `render.py`, für die Abläufe gelten die Skills.

## Ziel

Aus **Stammdaten** und einem **Template** entsteht pro **Schwerpunkt** ein **Standardlebenslauf**. Ein Claude-Code-Skill passt ihn in höchstens 15 Minuten (inklusive Gegenlesen) an eine **Stellenausschreibung** an und gibt ihn als PDF aus. Jede versendete **Bewerbung** wird abgelegt.

Feste Regeln:
- Jede Aussage im Lebenslauf ist durch die Stammdaten **gedeckt**. Die KI formuliert um, erfindet aber nichts.
- Das System ist öffentlich und enthält nichts Persönliches. Persönliche Daten liegen nur in `daten/`, lokal oder in einem **privaten** Remote.
- Jeder Nutzer braucht Claude Code (Pro oder höher), Python ≥ 3.10, git und Chrome, Edge oder Chromium. Ein GitHub-Account ist nicht nötig.
- Windows, macOS und Linux.
- Unterlagen, Skills und Dokumentation sind vorerst nur auf Deutsch.
- Es gibt keine GUI. Die Daten sind Textdateien.

## Komponenten

| Komponente | Zweck |
|---|---|
| `render.py` | YAML → HTML → PDF und alle Prüfungen |
| `templates/<name>.yaml` | mitgelieferte Templates: Grundlayout + Parameter |
| `templates/grundlayouts/` | Grundlayouts (Jinja2 + erlaubte Parameter) |
| `templates/schriften/` | Schriften mit freier Lizenz (SIL OFL) |
| `beispiel/` | vollständige Beispieldaten (erfundene Person), für Tests und Vorschaubilder |
| `tests/` | Tests für `render.py`, Migrationen und `einrichten.py`; `tests/schemas/v<N>/` Altdaten je Schemaversion |
| `docs/` | Vorschaubilder der Templates für die README (aus den Beispieldaten) |
| `README.md`, `LICENSE` | Anleitung für Nutzer; MIT (Schriften: OFL) |
| `.github/workflows/tests.yml` | CI auf Windows, macOS, Linux |
| `einrichten.py`, `migrationen.py`, `umgebung.py` | Umgebung einrichten, Daten anlegen, migrieren, aktualisieren |
| `.claude/skills/einrichten/` | Skill: Ersteinrichtung – Daten-Repo, Person und Foto, Import, Schwerpunkte, Template, Standardlebensläufe |
| `.claude/skills/stammdaten-pflegen/` | Skill: Stammdaten erfassen, ändern, Schwerpunkte anlegen |
| `.claude/skills/lebenslauf-anpassen/` | Skill: Stellenausschreibung → Bewerbung |
| `.claude/skills/template-pflegen/` | Skill: eigene Templates anlegen, ändern, veralten lassen; Standard-Template wählen |
| `.claude/skills/regeln.md` | gemeinsame Regeln der Skills |
| `entwurf/` (gitignoriert) | Arbeitsordner während einer Anpassung |
| `vorschau/` (gitignoriert) | Ausgabe von `render.py --vorschau` |
| `daten/` (gitignoriert, eigenes Git-Repo) | alle persönlichen Daten, siehe unten |

`daten/` enthält:

| Ordner/Datei | Zweck |
|---|---|
| `stammdaten/*.yaml` | die eine vollständige Quelle aller Inhalte, dazu das Foto |
| `standard/<schwerpunkt>/` | Standardlebensläufe (`lebenslauf.yaml` + PDF) |
| `bewerbungen/<datum>_<firma>_<stelle>/` | versendete Bewerbungen |
| `anlagen/` | bereinigte Nachweise |
| `templates/` | eigene Templates |
| `einstellungen.yaml` | persönliche Einstellungen, u. a. das Standard-Template |

## 1. Stammdaten

- YAML, eine Datei pro Art: `person.yaml`, `berufserfahrung.yaml`, `ausbildung.yaml`, `projekte.yaml`, `skills.yaml`, `kategorien.yaml`, `profil.yaml`.
- Ein **Arbeitgeber** hat eine oder mehrere **Positionen** (Zeitraum, Art, Titel). Jede Position hat **Tätigkeiten**. Eine Tätigkeit besteht aus einer Kernaussage und Details (Pflicht) und optional aus freigegebenen Formulierungen. Dazu kommen Schwerpunkte und belegte Skills.
- Ein **Projekt** hat einen Kontext (privat, Studium oder beruflich), optional einen Zeitraum, optional Repo-Links und kann mehrere Repos bündeln.
- **Abschluss**: Art, offizielle Bezeichnung, Institution, Zeitraum, Note, Status (abgeschlossen oder laufend), optional ein Thema und eine Anlage.
- **Skill**: Name, Kategorie und Niveau. **Belege** entstehen über Verweise von Tätigkeiten, Projekten und Abschlüssen. Soft Skills ohne Beleg kommen nicht in den Lebenslauf.
- **Kategorien** legt jeder Nutzer selbst an, passend zu seinem Beruf. Fest sind `gesprochene-sprache` (steht immer im Lebenslauf) und `arbeitsweise` (nur mit Beleg).
- **Schwerpunkte** legt jeder Nutzer selbst an, mindestens einen. Jeder hat einen **Profiltext**. Neue kommen nur bewusst dazu (siehe 6).
- Jede Einheit hat eine feste, lesbare **ID**. IDs werden nie umbenannt. Überholte Einträge werden als `veraltet` markiert, nicht gelöscht. Eine englische Fassung kann später als Übersetzungsdatei (ID → Text) dazukommen.
- Zeiträume sind monatsgenau und richten sich nach dem Nachweis.
- In den Stammdaten steht nur Freigegebenes.

## 2. Layout und PDF

- HTML/CSS, das PDF erzeugt headless Chrome (oder Edge/Chromium) mit `--print-to-pdf`.
- Das Aussehen bestimmt ein **Template** (Abschnitt 7). Mitgeliefert sind `klassisch`, `zwei-spalten` und `kopfband`.
- Grundlayout `klassisch`: einspaltig. Abschnitte: Kopf mit Foto und dem Profiltext daneben (ohne eigene Überschrift), Berufserfahrung, Ausbildung & Zertifizierung, Kenntnisse, Projekte. Kompakt gesetzt: Schrift 9,2 pt, Zeilenhöhe 1,28, Ränder 11/12/9 mm.
- **Untergrenzen für alle Grundlayouts**: Schrift 9 pt, Zeilenhöhe 1,25, Ränder 12 mm seitlich und 9 mm oben/unten. Ein farbiges Band am Blattrand (`kopfband`) zählt nicht als Rand, solange der Text darin denselben Abstand hält.
- Positionen werden standardmäßig pro Arbeitgeber zusammengefasst, pro Lebenslauf lässt sich das auf einzeln umstellen.
- Das Skill-Niveau erscheint nicht im PDF. Das Foto ist pro Lebenslauf abschaltbar.
- Höchstens 2 Seiten, Ziel ist 1. Kein halbleerer Rest, keine Detailseite.
- **Fest** sind (je Template) Layout, Kopf und Kontakt sowie (immer) Abschlüsse und gesprochene Sprachen. **Variabel** sind Untertitel, Profiltext, Auswahl und Reihenfolge der Tätigkeiten, Kenntnisse und Projekte.
- Text darf nicht mit `opacity` gesetzt werden: Chrome legt ihn sonst in eine eigene Ebene, und ATS lesen ihn in falscher Reihenfolge.

## 3. render.py

- PyYAML, Jinja2 und pypdf stehen in `requirements.txt` und werden in eine lokale `.venv/` installiert (gitignoriert). Gibt es die venv, startet sich `render.py` selbst darin neu; der Aufruf ist immer `python render.py …`.
- `lebenslauf.yaml` enthält nur das Variable: Schwerpunkt, optional das Template, Untertitel, Profiltext, Schalter und die gewählten Einträge als `{quelle: <ID>, text, umformuliert}`. Das Feste liest `render.py` aus den Stammdaten.
- `render.py <ordner>` erzeugt das PDF im selben Ordner. `--pruefen` prüft Schema, IDs und Verweise sowie Templates, Grundlayouts, Schriften und `einstellungen.yaml`. `--vorschau <template>` rendert alle Standardlebensläufe mit einem Template nach `vorschau/`, ohne sie zu ändern. `--daten <ordner>` wählt einen anderen Daten-Ordner, z. B. `beispiel`.
- Die IDs stehen als unsichtbare `data-quelle`-Attribute im HTML. Das Skript bricht ab, wenn eine ID unbekannt ist oder eine Aussage keine Quelle hat.
- Nach dem Rendern prüft pypdf die Seitenzahl und ob der Text extrahierbar ist (ATS). Bei Grundlayouts mit Spalten misst `render.py` im Browser die Höhe jeder Spalte: Hinweis, wenn eine Nebenspalte länger als die Hauptspalte ist, Warnung, wenn sie dadurch eine Seite mehr braucht.

## 4. Anpassen an eine Stellenausschreibung

1. Die Stellenausschreibung kommt als Text oder URL rein. Der Anzeigentext wird immer gespeichert.
2. Der Skill startet vom **Standardlebenslauf** des passenden Schwerpunkts und tauscht gezielt Inhalte aus den Stammdaten aus.
3. Er zeigt in einem Schritt die Kurzanalyse (Anforderungen, Schwerpunkt, Treffer, **Lücken**, Template) und das PDF. Spricht die Anzeige klar für ein anderes Template, schlägt er es vor; gewechselt wird nur auf Wunsch des Nutzers. Passt die Anzeige zu keinem Schwerpunkt, hält er an (siehe 6).
4. Nach jedem Rendern prüft er die Seitenzahl und kürzt selbst, wenn es zu lang wird, bei Spalten-Layouts in der Spalte, die überläuft. Was er gestrichen hat, nennt er.
5. Der Nutzer korrigiert im Chat, der Skill rendert neu.
6. Bei der Freigabe fragt er einmal gesammelt, ob gelungene Formulierungen in die Stammdaten übernommen werden sollen.

Regeln:
- Umformulieren ist erlaubt, auch mit Begriffen aus der Anzeige, aber **nur mit Fakten aus den Stammdaten**.
- Jede Aussage trägt eine Quellen-ID, umformulierte Stellen sind markiert. Nur geändertes Fett zählt nicht als Umformulierung.
- **Fett** zeigt im angepassten Lebenslauf genau die Treffer zur Anzeige (wörtliche Begriffe und die konkrete Erfüllung abstrakter Anforderungen), jeden einmal im Profil und einmal in Erfahrung und Projekten, nie in den Kenntnissen. Die Liste steht im Feld `fett` des Lebenslaufs, `render.py` gleicht sie ab.
- Lücken kommen erst in die Stammdaten und erst danach in den Lebenslauf.
- Ändern sich die Stammdaten, schlägt der Skill vor, die Standardlebensläufe nachzuziehen. Automatisch passiert das nie.

## 5. Ablage

- Ein **Entwurf** liegt in `entwurf/`. Bei der Freigabe zieht er nach `daten/bewerbungen/<datum>_<firma>_<stelle>/` um und wird im Daten-Repo committet. Der Ordner enthält:
  - `lebenslauf.yaml` (immer mit Feld `template`, damit das Aussehen nicht vom späteren Standard-Template abhängt)
  - `lebenslauf.pdf` (eingefroren)
  - `stellenausschreibung.md`
  - `bewerbung.yaml` mit Firma, Stelle, Datum, Schwerpunkt und `status`
- Den `status` pflegt der Nutzer per Zuruf. Weitere Auswertungen gibt es nicht.
- `person.yaml`, das Foto und die bereinigten Anlagen liegen im Daten-Repo. Originaldokumente bleiben beim Nutzer.
- Die Skills committen nur im Daten-Repo und pushen nur, wenn es ein Remote hat. Ein Remote muss privat sein.

## 6. Stammdaten pflegen und neue Schwerpunkte

- `stammdaten-pflegen` arbeitet im Gespräch: Der Nutzer erzählt, der Skill ordnet zu und fragt nur nach, was fehlt. Er zeigt den Diff, schreibt nach OK, führt `render.py --pruefen` aus und committet.
- Handänderungen sind erlaubt und durchlaufen dieselbe Prüfung.
- Einen neuen Schwerpunkt gibt es nur bewusst. Der Ablauf:
  1. `lebenslauf-anpassen` hält an und bietet an, den nächstliegenden Schwerpunkt zu nehmen oder einen neuen anzulegen.
  2. Beim Anlegen schlägt `stammdaten-pflegen` Name, Profiltext und Zuordnungen vor. Der Nutzer bestätigt in einer Runde.
  3. Der neue Standardlebenslauf wird vom Nutzer freigegeben.

## 7. Templates

- Ein **Template** ist ein **Grundlayout** plus Parameter: Akzentfarbe (Linien und Flächen werden daraus aufgehellt, die Linienfarbe ist überschreibbar), Schrift, Fotoform (eckig oder rund) und -position, Stil der Überschriften (Linie, Balken, fett) und Reihenfolge der Abschnitte. Es bestimmt das Aussehen der ganzen Bewerbungsunterlagen; Anschreiben bekommen später ein passendes Gegenstück je Grundlayout.
- Mitgelieferte Templates liegen in `templates/` und werden von Updates überschrieben, eigene in `daten/templates/`. Ein Name kommt nur einmal vor.
- Ein **Grundlayout** (`templates/grundlayouts/<name>.html.j2` + `.yaml`) legt die Struktur fest und welche Parameter möglich sind: erlaubte Fotopositionen, Spalten mit ihren Abschnitten, ob weißer Text auf der Akzentfarbe steht (dann Kontrast ≥ 4,5). Neue Grundlayouts kommen nur über Branch und PR dazu.
- Mitgeliefert: `klassisch` (einspaltig, ATS-sicher), `zwei-spalten` (getönte Seitenleiste mit Foto, Kontakt, Kenntnissen und Sprachen; im HTML steht die Hauptspalte zuerst, damit ATS die Reihenfolge richtig lesen), `kopfband` (farbiges Band oben über die volle Breite). Später denkbar: `minimal`, `zeitleiste`.
- **Schriften** liegen mit freier Lizenz (SIL OFL) im Repo, damit das PDF überall gleich aussieht. Systemschriften sind erlaubt (`system: true`), aber nur für eigene Templates.
- **Auswahl**: Feld `template` im Lebenslauf (ein Entwurf übernimmt es vom Standardlebenslauf) > `template` in `daten/einstellungen.yaml` > `klassisch`.
- Alle Templates bekommen denselben Inhalt und dieselben Prüfungen. Ein Template verlangt nie eine andere Auswahl von Inhalten.
- `template-pflegen` legt eigene Templates im Gespräch an und ändert sie: Grundlayout und Parameter vorschlagen, Vorschau mit allen Standardlebensläufen, nur nach bestandener Prüfung und OK speichern. Templates werden nie gelöscht, sondern `veraltet`. Ändert sich ein Template, das ein Standardlebenslauf nutzt, wird dessen PDF neu gerendert.

## 8. Verteilung, Updates und Kompatibilität

- Der Nutzer klont das öffentliche System-Repo. `daten/` ist dort gitignoriert und wird beim Einrichten ein eigenes, lokales Git-Repo; ein privates Remote ist optional.
- Updates holt ein `git pull` im System. Weil System und Daten getrennt sind, gibt es dabei keine Konflikte. Zu Beginn jedes Skills prüft Claude, ob es ein Update gibt (`einrichten.py --update-pruefen`, nur `git fetch`), und holt es nur nach Rückfrage.
- `daten/einstellungen.yaml` trägt eine `schemaversion`. `render.py` bricht ab, wenn die Daten älter (→ migrieren) oder neuer (→ System aktualisieren) sind. Jede Änderung, die die Datenstruktur bricht, bringt eine Migration mit; neue optionale Felder brauchen keine.
- Migrationen stehen in `migrationen.py` (nur Standardbibliothek, textbasiert, damit Kommentare bleiben). Für jede alte Version liegen Altdaten unter `tests/schemas/v<N>/`; ein Test migriert sie und prüft sie mit `render.py`. Fehlt eine Migration oder ihre Altdaten, schlägt er fehl.
- `einrichten.py` läuft mit dem System-Python ohne Zusatzpakete: ohne Argument prüft es Python ≥ 3.10, git und einen Browser, legt `.venv` an und installiert die Pakete. Was auf Systemebene fehlt, installiert es nicht, sondern nennt den Befehl für Windows, macOS oder Linux. `--migrieren` sichert `daten/` (Commit im Daten-Repo, sonst Kopie `daten-sicherung-<zeit>/`), migriert und prüft. `--aktualisieren` holt das System per `git pull --ff-only` (nur, wenn im System nichts geändert ist), aktualisiert die Pakete und migriert.
- `CHROME` (Pfad) und `CHROME_ARGS` (z. B. `--no-sandbox` in Containern) passen den Browseraufruf an.
- CI (GitHub Actions) führt `einrichten.py`, das Rendern der Beispieldaten und alle Tests auf Windows, macOS und Linux aus.
- `einrichten.py --daten-anlegen` legt `daten/` als lokales Git-Repo mit leerem Gerüst an (`einstellungen.yaml` mit aktueller Schemaversion, `offen.md`, `LIESMICH.md`) und setzt bei Bedarf Name und E-Mail für Git nur dort.

## 9. Einrichten

- Der Skill `einrichten` führt einen neuen Nutzer in dieser Reihenfolge: Umgebung (`einrichten.py`), Daten-Repo (lokal oder zusätzlich privates GitHub-Repo, Sichtbarkeit geprüft), Person und Foto, Import des bisherigen Lebenslaufs und weiterer Nachweise (sonst Interview), Nachfragen, Schwerpunkte und Kategorien, Template, Standardlebensläufe.
- Aus Dokumenten Gelesenes ist ein Vorschlag, bis der Nutzer es bestätigt. Unklares kommt nach `offen.md`, nicht in die Stammdaten.
- Die Einrichtung lässt sich abbrechen und an der Stelle fortsetzen, die die vorhandenen Dateien zeigen.
- Das Schema deckt auch Berufe außerhalb der IT ab: Positionsarten u. a. Teilzeit, Minijob, Freiberuflich, Selbstständig, Ehrenamt; Abschlüsse auch als Weiterbildung; Projekte auch im Ehrenamt; Kategorien frei.

## Nicht Teil dieser Spezifikation

- Anschreiben: kommt als Erweiterung, auf Basis der freigegebenen Formulierungen.
- Englische Unterlagen, Projektliste als Zusatzdokument, Bewerbungsmappe (Lebenslauf + Anlagen als ein PDF). Für alle drei hält die Struktur den Weg offen.
- GUI, Bewerbungs-Tracking über das Statusfeld hinaus.
