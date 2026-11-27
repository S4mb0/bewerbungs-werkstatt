# Gemeinsame Regeln der Skills

Diese Regeln gelten in `einrichten`, `stammdaten-pflegen`, `lebenslauf-anpassen` und `template-pflegen` und bei jeder Handänderung an `daten/`. Für `template-pflegen` gelten nur die Abschnitte Ordner, Umgebung, Nach jeder Änderung, Commits und Sprache.

## Ordner

- **System** (dieses Repo): `render.py`, Skills, `templates/` (Grundlayouts, mitgelieferte Templates, Schriften), `beispiel/`, `tests/`. Die Skills ändern hier nichts. Änderungen am System laufen über Branch und PR im System-Repo.
- **`daten/`**: alle persönlichen Daten, ein **eigenes Git-Repo**, im System gitignoriert: `stammdaten/`, `standard/`, `bewerbungen/`, `anlagen/`, `templates/` (eigene Templates), `einstellungen.yaml`.
- `entwurf/` und `vorschau/` im Wurzelordner sind Arbeitsordner und gitignoriert. Die Abläufe selbst stehen im jeweiligen Skill. Hintergrund und Begründungen stehen in `SPEC.md`, die Begriffe in `GLOSSARY.md`.

## Faktentreue

Die **Stammdaten** sind die einzige Quelle. Jede Aussage in einem Lebenslauf ist durch eine Kernaussage, Details oder eine freigegebene Formulierung in den Stammdaten **gedeckt**. Für das Anschreiben gilt dasselbe für jede Aussage über den Nutzer; was dort darüber hinaus steht, regelt der Abschnitt „Anschreiben“.

- Umformulieren ist erlaubt, auch mit Begriffen aus der Stellenausschreibung. Die Fakten bleiben dieselben: Technologien, Zahlen, Verantwortungen und Ergebnisse stammen aus Kernaussage und Details derselben Quelle.
- Jede Aussage in `lebenslauf.yaml` hat die Form `{quelle: <ID>, text, umformuliert}`:
  - ohne `text`: der Lebenslauf zeigt die Kernaussage (beim Profil den Profiltext) der Quelle;
  - `text` gleich der Kernaussage oder einer freigegebenen Formulierung: `umformuliert` weglassen;
  - jeder andere `text`: `umformuliert: true`.
- Der Untertitel darf den Stellentitel aufgreifen, wenn der gewählte Schwerpunkt ihn deckt. Der Profiltext startet vom Profiltext des Schwerpunkts und folgt denselben Regeln.
- Ein Skill der Kategorie `arbeitsweise` kommt nur mit Beleg in einen Lebenslauf.
- In den Stammdaten steht nur, was der Nutzer freigegeben hat. Abgelehntes kommt gar nicht hinein, einen Schalter „versteckt“ gibt es nicht.

## Lücken

Eine **Lücke** ist eine Anforderung ohne Entsprechung in den Stammdaten. Bestätigt der Nutzer sie mit Beleg, wandert sie zuerst in die Stammdaten (mit Prüfung und Commit) und wird erst danach im Lebenslauf über ihre neue ID zitiert. Ohne Bestätigung bleibt sie eine Lücke und erscheint nicht im Lebenslauf.

## IDs

Jede Einheit hat eine feste, lesbare ID: Kleinbuchstaben, Ziffern und Bindestriche (`^[a-z0-9]+(-[a-z0-9]+)*$`), eindeutig über alle Dateien hinweg.

| Einheit | Muster | Beispiel |
|---|---|---|
| Arbeitgeber | Kurzname | `beispiel-technik` |
| Position | `<arbeitgeber>-<art>` | `beispiel-technik-werkstudent` |
| Tätigkeit | `taet-<thema>` | `taet-k8s-betrieb` |
| Projekt | `proj-<thema>` | `proj-deploy-tool` |
| Abschluss | `abschluss-<kurz>` | `abschluss-bsc` |
| Skill | `skill-<name>` | `skill-kubernetes` |
| Schwerpunkt | Name | `devops` |
| Profiltext | `profil-<schwerpunkt>` | `profil-devops` |
| Baustein (Anschreiben) | `baust-<thema>` | `baust-schluss-gespraech` |
| Rahmendaten (Anschreiben) | fest `rahmen` | `rahmen` |

Eine vergebene ID ist **dauerhaft**: Sie bleibt, auch wenn sich Text, Titel oder Zuordnung ändern, denn Standardlebensläufe und versendete Bewerbungen zitieren sie. Ein überholter Eintrag bekommt `veraltet: true` und bleibt stehen. `render.py` warnt, wenn ein Lebenslauf etwas Veraltetes zitiert.

## Schema der Stammdaten

Durchgesetzt von `render.py --pruefen` (Konstanten `STAMMDATEN_DATEIEN` und folgende in `render.py`; bei Abweichung gilt `render.py`). Unbekannte Felder sind Fehler. **Fett** = Pflichtfeld. Jede Einheit außer Person, Schwerpunkt, Profiltext und Rahmen kennt `veraltet` (true/false).

| Datei | Wurzel | Einheit und Felder |
|---|---|---|
| `person.yaml` | ein Objekt | **id**, **name**, **wohnort**, strasse, plz, telefon, email, web (Liste), geburtsdatum, geburtsort, foto und unterschrift (Pfade relativ zu `daten/stammdaten/`). `strasse`, `plz` und `unterschrift` erscheinen nur im Anschreiben. |
| `berufserfahrung.yaml` | `arbeitgeber:` | Arbeitgeber: **id**, **name**, ort, **positionen** |
| | | Position: **id**, **art** (`Festanstellung`, `Teilzeit`, `Ausbildung`, `Praktikum`, `Werkstudent`, `Minijob`, `Freiberuflich`, `Selbstständig`, `Ehrenamt`), **titel**, **von**, **bis**, taetigkeiten, anlage |
| | | Tätigkeit: **id**, **kernaussage**, **details**, formulierungen, **schwerpunkte**, skills |
| `ausbildung.yaml` | `abschluesse:` | Abschluss: **id**, **art** (`schule`, `ausbildung`, `studium`, `weiterbildung`, `zertifikat`), **bezeichnung** (offiziell laut Nachweis), **institution**, von, bis, note, **status** (`abgeschlossen`, `laufend`), thema, anlage, position, skills |
| `projekte.yaml` | `projekte:` | Projekt: **id**, **titel**, **kontext** (`privat`, `studium`, `beruflich`, `ehrenamt`), position, von, bis, **kernaussage**, **details**, formulierungen, repos, **schwerpunkte**, skills |
| `skills.yaml` | `skills:` | Skill: **id**, **name**, **kategorie** (eine ID aus `kategorien.yaml`), **niveau** (freier Text; vereinbart sind `Grundlagen`, `gut`, `sehr gut`, bei gesprochenen Sprachen frei), schwerpunkte |
| `profil.yaml` | `schwerpunkte:` | Schwerpunkt: **id**, **profiltext** (Objekt mit **id** und **text**) |
| `kategorien.yaml` | `kategorien:` | Kategorie: **id**, **name** (Überschrift unter „Kenntnisse“). Reihenfolge = Reihenfolge im Lebenslauf. Pflicht sind `gesprochene-sprache` (steht immer im Lebenslauf) und `arbeitsweise` (nur mit Beleg). |
| `anschreiben.yaml` (optional) | `bausteine:`, `rahmen:` | Baustein: **id**, **art** (`einstieg`, `motivation`, `rahmen`, `schluss`), **text**, schwerpunkte. Rahmen: verfuegbarkeit, gehalt (freier Text). |

Zusätzliche Regeln:

- **Zeiträume** sind monatsgenau als `"JJJJ-MM"` in Anführungszeichen, `bis` auch `heute`. Maßgeblich ist der Nachweis. `bis` liegt nicht vor `von`.
- Abschluss `abgeschlossen` braucht `bis`, `laufend` braucht `von`. Projekt `beruflich` braucht `position`.
- `position`, `skills` und `schwerpunkte` verweisen auf existierende IDs der passenden Art.
- `anlage` ist ein Pfad relativ zu `daten/`, meist `anlagen/<sprechender-name>.pdf`.
- Kernaussagen, Formulierungen und Profiltexte dürfen `**fett**` enthalten, das Template übernimmt es. Dieses Fett gilt für die Standardlebensläufe; im angepassten Lebenslauf bestimmt die Anzeige, was fett ist (`lebenslauf-anpassen`, Feld `fett`). Ein Text, der sich nur im Fett von den Stammdaten unterscheidet, gilt als freigegeben.
- Kommentare im YAML halten Herkunft und Klärungen fest (z. B. `# laut Arbeitszeugnis 30.04.2020`).

**Belege** sind die `skills`-Verweise von Tätigkeiten, Projekten und Abschlüssen. Wer einen Skill erfasst, hängt ihn an mindestens eine Tätigkeit, ein Projekt oder einen Abschluss.

## Anschreiben

Ein **Anschreiben** ist optional und gehört zu einer Bewerbung oder als **Standardanschreiben** zu einem Schwerpunkt: `anschreiben.yaml` (+ PDF) liegt neben `lebenslauf.yaml` und nimmt immer dessen Template. Es hat genau 1 Seite, etwa 250–350 Wörter und kein Fett.

Es besteht aus **Absätzen** `{art, text, quellen, herkunft, umformuliert}`:

- `art`: `einstieg`, `hauptteil`, `motivation`, `rahmen` oder `schluss`.
- `quellen`: IDs aus den Stammdaten (Tätigkeit, Projekt, Abschluss, Position, Skill, Profiltext, Baustein, `rahmen`). Jede Aussage über den Nutzer ist durch sie gedeckt, wie im Lebenslauf.
- `herkunft`: `anzeige` (Bezug auf Firma und Stelle aus der Stellenausschreibung) oder `nutzer` (was der Nutzer im Chat gesagt hat, etwa seine Motivation). Erfundene Gründe gibt es nicht.
- Jeder Absatz hat `quellen` oder `herkunft`, ein `hauptteil` immer `quellen`.
- Ohne `text` zeigt der Absatz den freigegebenen Text seiner einzigen Quelle (meist ein Baustein). Ein `text`, der von den freigegebenen Texten seiner Quellen abweicht, trägt `umformuliert: true`.

**Bausteine** (`daten/stammdaten/anschreiben.yaml`) sind freigegebene Absätze ohne Bezug auf eine bestimmte Firma: Einstiege, Motivationen, Schlüsse. Einen Baustein für den Hauptteil gibt es nicht: Erfahrung steht in Tätigkeiten und Projekten, gelungene Sätze dazu werden deren `formulierungen`. **Rahmendaten** (`rahmen`: Verfügbarkeit, Gehalt) erscheinen nur, wenn die Stellenausschreibung danach fragt.

Empfänger, Stelle, Kennziffer und Anrede stehen in `bewerbung.yaml` (`empfaenger:` mit abteilung, ansprechperson, strasse, plz, ort, anrede), nicht in den Stammdaten. Ohne `bewerbung.yaml` (Standardanschreiben) zeigt `render.py` Platzhalter wie `[Firma]`; in einer Bewerbung sind Platzhalter ein Fehler. Das Datum des Briefs ist das `datum` aus `bewerbung.yaml`, solange es ein Platzhalter ist, der heutige Tag.

## Schwerpunkte

Welche Schwerpunkte es gibt, steht nur in `daten/stammdaten/profil.yaml`; jeder Nutzer legt seine eigenen an, mindestens einen. Jeder hat dort einen Profiltext und unter `daten/standard/<schwerpunkt>/` seinen Standardlebenslauf, auf Wunsch auch ein Standardanschreiben. Tätigkeiten und Projekte tragen mindestens einen, Skills optional welche.

Ein neuer Schwerpunkt entsteht nur **bewusst**: Der Nutzer bestätigt Name, Profiltext und Zuordnungen ausdrücklich, und der neue Standardlebenslauf wird von ihm freigegeben. Passt eine Stellenausschreibung zu keinem Schwerpunkt, gilt das als Anlass zu fragen.

## Umgebung

`render.py` braucht die lokale `.venv/` im Repo-Wurzelordner (gitignoriert). Gibt es sie, startet sich `render.py` selbst darin neu: Der Aufruf ist immer `python render.py …`, unter macOS/Linux `python3 render.py …`. Wo ein Skill Python direkt mit den Paketen braucht, nimmt er das Python der venv: `.venv/Scripts/python` unter Windows, `.venv/bin/python` unter macOS/Linux.

Prüf vor dem ersten `render.py`-Aufruf eines Laufs, ob `.venv/` existiert. Fehlt sie, legst du sie ohne Rückfrage an:

```bash
python -m venv .venv && <venv-python> -m pip install -q -r requirements.txt
```

Sag dem Nutzer danach in einem Satz, dass die venv neu angelegt wurde. Scheitert die Einrichtung (kein `python`, kein Netz), halt an und nenne den Fehler.

Fehlt `daten/stammdaten/`, ist noch nichts eingerichtet: Verweise auf den Skill `einrichten`.

Meldet `render.py` „zuerst migrieren“, ist das System neuer als die Daten. Sag dem Nutzer in einem Satz, dass `python einrichten.py --migrieren` die Daten umstellt und vorher eine Sicherung anlegt, und führ es nach seinem OK aus. Meldet es „System aktualisieren“, ist es umgekehrt: `python einrichten.py --aktualisieren`, ebenfalls nach OK. Fehlen Python-Pakete oder die `.venv`, hilft `python einrichten.py`.

### Update-Prüfung

Einmal pro Gespräch, vor dem ersten Schritt eines Skills: `python einrichten.py --update-pruefen`. Es schaut nur nach (git fetch) und ändert nichts.

- `UPDATE   verfügbar (…)`: Sag dem Nutzer in einem Satz, dass es ein Update gibt, nenn die wichtigsten Änderungen aus der Liste in Stichworten und frag, ob du es holen sollst. Nach OK `python einrichten.py --aktualisieren`, danach liest du den Skill und `regeln.md` neu, weil sie sich geändert haben können. Ohne OK machst du mit dem jetzigen Stand weiter.
- `UPDATE   System ist aktuell` oder `UPDATE   übersprungen: …`: Nichts sagen, weitermachen.
- Meldet `--aktualisieren` „geänderte Dateien im System“, hat der Nutzer selbst etwas am System geändert. Nenn die Dateien und mach ohne Update weiter. Zurücksetzen oder überschreiben nur, wenn er es ausdrücklich sagt.

## Nach jeder Änderung

Nach jeder Änderung an `daten/stammdaten/`, `daten/standard/`, `entwurf/`, `templates/` oder `daten/einstellungen.yaml` läuft aus dem Repo-Wurzelordner:

```bash
python render.py --pruefen
```

Die Änderung ist fertig, wenn die Prüfung mit Exit-Code 0 endet und jede Warnung entweder behoben oder dem Nutzer genannt ist. Fehler werden in den Daten behoben, nie durch Abschwächen von `render.py`.

Ändern sich Stammdaten, die ein Standardlebenslauf oder Standardanschreiben zitiert, schlägt der Skill vor, sie nachzuziehen. Der Nutzer entscheidet.

## Commits

- Commit erst nach dem OK des Nutzers und bestandener Prüfung.
- Die Skills committen **nur im Daten-Repo**: `git -C daten add …` und `git -C daten commit …`, direkt auf dessen Hauptzweig, ohne Branch und PR. Das OK des Nutzers im Chat ist die Freigabe.
- Gepusht wird nur, wenn das Daten-Repo ein Remote hat (`git -C daten remote` ist nicht leer): vorher `git -C daten pull`, danach `git -C daten push`. Ohne Remote bleibt alles lokal.
- Das System-Repo im Wurzelordner ändern die Skills nie. Änderungen an Skills, `render.py`, Grundlayouts, mitgelieferten Templates, Schriften oder Tests sind Entwicklung am System und laufen dort über Branch und PR.
- Nachricht auf Deutsch, erste Zeile sagt, was sich inhaltlich ändert (`Stammdaten: Tätigkeit taet-lasttests-k6 ergänzt`), bei Bedarf Stichpunkte darunter.
- Letzte Zeile: die `Co-Authored-By`-Zeile, die Claude Code für Commits vorgibt.

## Datenschutz

`daten/` enthält Foto, Kontaktdaten, Zeugnisse und Bewerbungen. Es bleibt **lokal** oder liegt in einem **privaten** Remote, nie in einem öffentlichen. Hat das Daten-Repo ein GitHub-Remote, prüfst du vor dem ersten Push eines Laufs mit `gh repo view <remote> --json visibility`, dass es privat ist, und hältst sonst an.

Originaldokumente (alte Lebensläufe, ungeschwärzte Zeugnisse) bleiben, wo der Nutzer sie hat. In `daten/` landen nur Stammdaten und bereinigte Anlagen. Vor jedem Commit zeigt `git -C daten status` nur Dateien, die der Lauf geändert hat.

## Sprache

Alles ist Deutsch: Lebensläufe, Anschreiben, Rückfragen, Commit-Nachrichten, YAML-Kommentare. Verwende die Begriffe aus `GLOSSARY.md` (Tätigkeit, Position, Beleg, Lücke, Entwurf …) und meide die dort unter _Avoid_ genannten.
