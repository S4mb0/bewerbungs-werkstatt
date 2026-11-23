---
name: stammdaten-pflegen
description: Erfasst und ändert die Stammdaten des Nutzers (Tätigkeiten, Projekte, Skills, Abschlüsse, Formulierungen) im Gespräch und legt neue Schwerpunkte an. Verwenden, wenn der Nutzer etwas Neues über seine Arbeit, Projekte oder Abschlüsse erzählt, einen Eintrag korrigieren oder veralten lassen will, oder wenn ein neuer Schwerpunkt gebraucht wird.
---

# Stammdaten pflegen

Der Nutzer erzählt frei, du machst daraus Einträge in `daten/stammdaten/*.yaml`. Es gibt zwei Wege:

- **A. Erfassen und ändern**: neue Einträge, Ergänzungen, Korrekturen, `veraltet`
- **B. Neuer Schwerpunkt**: nur, wenn der Nutzer ihn ausdrücklich will oder `lebenslauf-anpassen` angehalten hat, weil kein Schwerpunkt passt

Vor dem ersten Schritt liest du [`../regeln.md`](../regeln.md). Sie gilt für jeden Eintrag, jede ID und jeden Commit. Begriffe: `GLOSSARY.md`. Alle Befehle laufen im Repo-Wurzelordner. Zuerst die Update-Prüfung aus `regeln.md` (Abschnitt „Umgebung“), einmal pro Gespräch.

`daten/stammdaten/offen.md` sammelt, was der Nutzer nachreichen will, und die Lücken aus Stellenausschreibungen. Lies sie mit: Erledigt die Erzählung des Nutzers einen Punkt, streichst du ihn im selben Commit. Was er gerade nicht weiß, trägst du dort ein, statt es zu raten.

## A. Erfassen und ändern

### 1. Zuordnen

Lies die betroffenen Stammdaten-Dateien und ordne jede Aussage des Nutzers zu:

- **Art**: Tätigkeit, Projekt, Skill, Abschluss, Formulierung zu einem bestehenden Eintrag, Korrektur oder `veraltet`.
- **Ort**: bei einer Tätigkeit Arbeitgeber und Position (über den Zeitraum), bei einem Projekt der Kontext.
- **Neu oder Ergänzung**: Deckt ein bestehender Eintrag denselben Sachverhalt, ergänzt du ihn (Details, Formulierung, Skills). Seine ID bleibt.
- **Belege**: welche Skills der Eintrag belegt. Fehlt ein Skill in `skills.yaml`, legst du ihn mit an.

Fertig, wenn jede Aussage einem Ziel zugeordnet ist und du weißt, was davon noch fehlt.

### 2. Nachfragen

Frag in **einer** Nachricht nur, was für die Pflichtfelder oder für die Faktentreue fehlt, zum Beispiel:

- Zeitraum, wenn er die Position nicht eindeutig macht
- welches Werkzeug genau, statt „etc.“ oder „Tools“
- eigener Anteil oder Team, wenn die Aussage eine Verantwortung behauptet
- Niveau eines neuen Skills (`Grundlagen`, `gut`, `sehr gut`)
- Schwerpunkte, wenn sie nicht naheliegen

Was der Nutzer nicht gesagt hat, bleibt draußen. Zahlen, Ergebnisse und Verantwortungen schreibst du nur, wenn er sie nennt.

### 3. Vorschlag zeigen

Zeig die Änderung als YAML-Ausschnitt mit Ort, so wie sie in die Datei kommt:

- neue IDs nach den Mustern aus `regeln.md`, vorher mit `grep` auf Eindeutigkeit geprüft
- `kernaussage` als ein Satz in der Sache des Nutzers, mit `**fett**` für die ein, zwei wichtigsten Begriffe
- `details` mit allem, was er erzählt hat, auch was nicht in die Kernaussage passt
- bei Änderungen bestehender Einträge nur die geänderten Zeilen, alt und neu

Bei vielen Einträgen auf einmal schreibst du sie stattdessen gleich in die Dateien, ohne zu committen, lässt `render.py --pruefen` laufen und zeigst eine Übersicht: neue IDs, ergänzte IDs, neue Skills. Der Diff (`git diff daten/stammdaten/`) ist dann der Vorschlag.

Frag nach OK. Korrigiert der Nutzer, zeigst du den Ausschnitt neu. Lehnt er ab, setzt `git -C daten checkout -- stammdaten/` die Dateien zurück.

### 4. Schreiben und prüfen

Nach dem OK:

```bash
python render.py --pruefen
git -C daten status --short
```

Behebe Fehler in den Daten, bis die Prüfung mit Exit-Code 0 endet. Nenne dem Nutzer jede Warnung. `git -C daten status` zeigt nur Dateien unter `stammdaten/`. Dann committen nach `regeln.md`, zum Beispiel `Stammdaten: Tätigkeit taet-lasttests-k6 ergänzt`.

Fertig, wenn der Commit steht.

### 5. Standardlebensläufe

Prüf für jeden Ordner unter `daten/standard/`, ob die Änderung ihn betrifft:

- er zitiert eine geänderte oder veraltete ID (`grep -l <id> daten/standard/*/lebenslauf.yaml`), oder
- ein neuer Eintrag trägt seinen Schwerpunkt.

Nenne die betroffenen Standardlebensläufe mit einem Satz, was sich ändern würde, und frag, ob du sie nachziehen sollst. Bei Ja: ändern, `render.py daten/standard/<schwerpunkt>` (höchstens 2 Seiten, ohne Füllwarnung), PDF mit dem Read-Tool ansehen, der Nutzer zeigen, nach Freigabe committen. Bei Nein bleibt der Standardlebenslauf, wie er ist.

## B. Neuer Schwerpunkt

### 1. Vorschlag in einer Runde

Zeig alles in einer Nachricht:

- **ID** (`^[a-z0-9]+(-[a-z0-9]+)*$`, kurz und sprechend) und ein Satz, wofür der Schwerpunkt steht
- **Profiltext** (`profil-<id>`), nur aus Fakten der Stammdaten, Länge wie die vorhandenen Profiltexte
- **Zuordnungen**: welche Tätigkeiten, Projekte und Skills den neuen Schwerpunkt zusätzlich bekommen, als Liste von IDs
- Abgrenzung zum nächstliegenden bestehenden Schwerpunkt in einem Satz

Der Nutzer bestätigt oder korrigiert. Neu zeigen musst du nur, was er geändert hat.

### 2. Schreiben

1. In `daten/stammdaten/profil.yaml` den Schwerpunkt mit Profiltext anlegen.
2. Bei den bestätigten Einträgen die ID in `schwerpunkte` ergänzen.
3. Die Liste der Schwerpunkte in `.claude/skills/regeln.md` (Abschnitt „Schwerpunkte“) und in `GLOSSARY.md` (Eintrag **Schwerpunkt**) nachziehen.
4. `render.py --pruefen`.

### 3. Standardlebenslauf

`daten/standard/<id>/lebenslauf.yaml` anlegen, mit dem nächstliegenden Standardlebenslauf als Vorlage:

- jede Aussage mit `quelle`, Umformuliertes mit `umformuliert: true`
- `render.py daten/standard/<id>`: höchstens 2 Seiten, Ziel 1, ohne Füllwarnung
- PDF mit dem Read-Tool ansehen, dann dem Nutzer zeigen, mit einem Satz Begründung zur Auswahl

Korrekturen einarbeiten, bis der Nutzer freigibt. Dann alles in einem Commit: `Schwerpunkt <id> angelegt`.

Fertig, wenn der Commit steht. Kam der Anlass aus `lebenslauf-anpassen`, geht es dort mit dem neuen Schwerpunkt in Schritt 3 weiter.
