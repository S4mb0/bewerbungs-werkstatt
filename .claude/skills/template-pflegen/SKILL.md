---
name: template-pflegen
description: Legt Templates für den Lebenslauf an, ändert sie (Farbe, Schrift, Foto, Überschriften, Reihenfolge), markiert sie als veraltet und stellt das Standard-Template ein. Verwenden, wenn der Nutzer ein neues Aussehen für den Lebenslauf will, ein Template anpassen oder ein anderes Template als Standard möchte.
---

# Template pflegen

Ein **Template** ist eine kleine YAML-Datei: ein **Grundlayout** plus Parameter. Es bestimmt das Aussehen der Bewerbungsunterlagen, ihr Inhalt hängt nie vom Template ab. Mitgelieferte Templates liegen in `templates/` (System, nie ändern), eigene in `daten/templates/`. Es gibt vier Wege:

- **A. Neues Template**: Grundlayout wählen, Parameter setzen
- **B. Template ändern**: Parameter eines bestehenden Templates anpassen
- **C. Standard-Template wechseln**: `daten/einstellungen.yaml`
- **D. Template veralten lassen**: statt löschen

Dieser Skill ist bewusst allgemein gehalten: Er nennt keine Person und liest Name, Foto und Kontakt nur über `render.py` aus den Stammdaten. Für Commits, Umgebung (`.venv`) und Sprache gilt [`../regeln.md`](../regeln.md). Begriffe: `GLOSSARY.md`. Alle Befehle laufen im Repo-Wurzelordner. Zuerst die Update-Prüfung aus `regeln.md` (Abschnitt „Umgebung“), einmal pro Gespräch.

## Was es gibt

Lies vor jedem Weg, was vorhanden ist:

- **Grundlayouts**: `templates/grundlayouts/<name>.yaml`. `beschreibung` sagt, wofür es steht, `foto_positionen` was beim Foto geht, `spalten` welche Abschnitte in welcher Spalte stehen. Das HTML dazu (`<name>.html.j2`) änderst du in diesem Skill nicht.
- **Templates**: mitgeliefert in `templates/*.yaml`, eigene in `daten/templates/*.yaml`. Ein Name kommt nur einmal vor.
- **Schriften**: `templates/schriften/schriften.yaml`
- **Standard-Template**: `daten/einstellungen.yaml`, Feld `template`

Welches Template ein Lebenslauf bekommt: Feld `template` in seiner `lebenslauf.yaml`, sonst `daten/einstellungen.yaml`, sonst `klassisch`.

## Parameter eines Templates

```yaml
beschreibung: <ein Satz: Grundlayout, Farbe, Schrift, Besonderheit>
grundlayout: <name aus templates/grundlayouts/>
farbe: "#rrggbb"            # Akzentfarbe; Linien und Flächen werden daraus aufgehellt
linienfarbe: "#rrggbb"      # optional, überschreibt die berechnete Linienfarbe
schrift: <id aus schriften.yaml>
foto:
  form: eckig | rund
  position: rechts | links  # nur, was das Grundlayout in foto_positionen erlaubt
ueberschriften: linie | balken | fett
reihenfolge: [berufserfahrung, ausbildung, kenntnisse, projekte]   # jeder Abschnitt genau einmal
veraltet: true              # nur bei D
```

Was ein Template nicht setzt: Schriftgröße, Zeilenhöhe und Ränder. Die liegen im Grundlayout, und ihre Untergrenzen stehen in `SPEC.md`. Wünscht sich der Nutzer so etwas oder ein ganz neues Layout, ist das eine Änderung am Grundlayout und läuft als eigene Aufgabe über Branch und PR. Sag das und mach hier nicht weiter.

Bei Grundlayouts mit `weisser_text_auf_farbe: true` (z. B. `kopfband`) muss die Farbe dunkel genug für weißen Text sein. `render.py --pruefen` lehnt zu helle Farben ab.

## A. Neues Template

### 1. Vorschlag in einer Runde

Zeig in einer Nachricht:

- die Grundlayouts mit ihrer `beschreibung`, die vorhandenen Templates und die Schriften
- deinen Vorschlag als fertigen YAML-Block, abgeleitet aus dem Wunsch des Nutzers: Name (`^[a-z0-9]+(-[a-z0-9]+)*$`, noch nicht vergeben), Grundlayout und alle Parameter

Nennt der Nutzer nur eine Richtung („moderner“, „konservativer“, „mit Seitenleiste“), wähl passende Werte und begründe sie in einem Halbsatz. Fehlt etwas, nimm die Werte des nächstliegenden Templates. Zu einer Farbe gibst du immer den Hex-Wert an.

Der Nutzer bestätigt oder korrigiert. Neu zeigen musst du nur, was er geändert hat.

### 2. Schreiben und Vorschau

1. `daten/templates/<name>.yaml` schreiben (Ordner bei Bedarf anlegen), oben ein Kommentar mit einem Satz zum Template.
2. `python render.py --pruefen` muss mit Exit-Code 0 enden. Fehler behebst du im Template.
3. Vorschau mit allen Standardlebensläufen:

   ```bash
   python render.py --vorschau <name>
   ```

   Das rendert jeden `daten/standard/<schwerpunkt>/` nach `vorschau/<schwerpunkt>/lebenslauf.pdf` und, wo es ein Standardanschreiben gibt, nach `vorschau/<schwerpunkt>/anschreiben.pdf`: Das Anschreiben-Gegenstück des Grundlayouts übernimmt Farbe, Schrift und Überschriften. YAML und PDFs im Standard bleiben unberührt. Die letzten Zeilen (`VORSCHAU …`) fassen Seitenzahl und Ergebnis zusammen, darüber stehen die Warnungen je Lebenslauf.
4. Sieh dir jedes Vorschau-PDF mit dem Read-Tool an: Überlappungen, abgeschnittene Bilder, Lesbarkeit der Farben, Umbrüche.

Fertig, wenn alle Zeilen `VORSCHAU …` „in Ordnung“ sagen und du die PDFs gesehen hast. Sagt eine Zeile „FEHLER“, zum Beispiel mehr als 2 Seiten beim Lebenslauf oder mehr als 1 Seite beim Anschreiben, passt das Template nicht zu den Standardlebensläufen. Schlag eine Änderung am Template vor (andere Schrift oder Reihenfolge). Gekürzt wird hier nicht, Inhalte gehören zu `lebenslauf-anpassen`.

### 3. Zeigen

Eine Nachricht:

- ein Vorschau-PDF als Datei, am besten das des Schwerpunkts, den der Nutzer am häufigsten verwendet (im Zweifel das mit den meisten Bewerbungen unter `daten/bewerbungen/`)
- je Standardlebenslauf: Seitenzahl und Warnungen (Füllwarnung, `WARNUNG  Spalte …`, `HINWEIS  Spalte …`)
- was dir beim Ansehen aufgefallen ist

Warnungen blockieren das Speichern nicht. Sie sagen, wo ein Lebenslauf mit diesem Template später gekürzt werden müsste.

### 4. Speichern

Korrekturen einarbeiten, Schritt 2 wiederholen, bis der Nutzer freigibt. Dann:

1. Frag einmal, ob das neue Template das **Standard-Template** werden soll. Bei Ja: weiter mit C, im selben Commit.
2. `git -C daten status --short` zeigt nur `templates/<name>.yaml` (bei C zusätzlich `einstellungen.yaml` und `standard/`).
3. Commit im Daten-Repo nach `regeln.md`: `Template <name> angelegt`.

Fertig, wenn der Commit steht. `vorschau/` ist gitignoriert und darf liegen bleiben.

## B. Template ändern

Ändern lassen sich nur **eigene** Templates in `daten/templates/`. Will der Nutzer ein mitgeliefertes anpassen, kopierst du es unter neuem Namen nach `daten/templates/` (Weg A mit dem mitgelieferten als Ausgangspunkt), denn Updates des Systems würden Änderungen dort überschreiben.

1. Zeig nur die geänderten Zeilen, alt und neu. Bei einer neuen Farbe gibst du den Hex-Wert an.
2. Nach dem OK schreiben, `--pruefen`, `--vorschau <name>`, PDFs ansehen, zeigen wie in A, Schritte 2 und 3.
3. **Wer ist betroffen?**
   - Standardlebensläufe mit `template: <name>`, sowie alle ohne Feld `template`, wenn `<name>` in `daten/einstellungen.yaml` steht. Diese rendest du nach der Freigabe neu (`render.py daten/standard/<schwerpunkt>`, das rendert ein Standardanschreiben mit), damit ihre eingecheckten PDFs zum Template passen.
   - Abgelegte Bewerbungen (`grep -l "template: <name>" daten/bewerbungen/*/lebenslauf.yaml`) bleiben unverändert, ihr PDF ist eingefroren. Nenne ihre Zahl in einem Satz, damit der Nutzer weiß, dass ein neues Rendern dort anders aussähe. Soll das alte Aussehen erhalten bleiben, schlag stattdessen ein neues Template vor (A) und lass das alte stehen.
4. Commit im Daten-Repo: `Template <name>: <was sich ändert>`, mit den neu gerenderten Standards.

## C. Standard-Template wechseln

1. Nenne, was sich ändert: alle Standardlebensläufe ohne eigenes Feld `template` und jeder künftige Entwurf, der von ihnen startet. Bewerbungen tragen ihr Template selbst und bleiben, wie sie sind.
2. Nach dem OK `daten/einstellungen.yaml` ändern, `--pruefen`.
3. Die betroffenen Standardlebensläufe neu rendern (`render.py daten/standard/<schwerpunkt>`), PDFs ansehen, Warnungen nennen.
4. Commit im Daten-Repo: `Standard-Template: <name>`.

## D. Template veralten lassen

Nur eigene Templates lassen sich veralten. Ein Template wird nie gelöscht, denn abgelegte Bewerbungen nennen es und sollen sich neu rendern lassen.

1. Steht das Template in `daten/einstellungen.yaml` oder in einem Standardlebenslauf (`grep -l "template: <name>" daten/standard/*/lebenslauf.yaml`), halt an. Erst muss ein anderes Template dort eingetragen werden (C oder Feld im Standard).
2. `veraltet: true` setzen, `--pruefen`. Die Warnung „als veraltet markiert“ erscheint danach nur noch, wo es trotzdem verwendet wird.
3. Commit im Daten-Repo: `Template <name> veraltet`.

## Handänderung

Der Nutzer darf `daten/templates/*.yaml` und `daten/einstellungen.yaml` auch selbst bearbeiten. Danach gilt dasselbe: `--pruefen`, bei Bedarf `--vorschau`, betroffene Standards neu rendern, Commit.
