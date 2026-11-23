---
name: lebenslauf-anpassen
description: Passt den Lebenslauf des Nutzers an eine Stellenausschreibung an und legt die Bewerbung ab. Verwenden, wenn der Nutzer eine Stellenausschreibung (Text oder URL) schickt, einen Entwurf in entwurf/ korrigieren oder freigeben will.
---

# Lebenslauf anpassen

Aus einer **Stellenausschreibung** wird ein **Entwurf** in `entwurf/` und nach Freigabe durch den Nutzer eine **Bewerbung** in `daten/bewerbungen/`. Ziel: höchstens 15 Minuten von der Anzeige bis zur Freigabe, Gegenlesen eingeschlossen.

Vor dem ersten Schritt liest du [`../regeln.md`](../regeln.md). Sie gilt für jede Aussage, jede Lücke und jeden Commit in diesem Ablauf. Begriffe: `GLOSSARY.md`. Alle Befehle laufen im Repo-Wurzelordner.

## 1. Start

1. Startzeit festhalten: `date +%H:%M`.
2. Liegt schon etwas in `entwurf/`, ist das ein unfertiger Entwurf. Frag den Nutzer, ob er weitergeführt oder verworfen wird, und mach dann entsprechend mit Schritt 6 oder hier weiter.
3. Anzeige **wörtlich** einlesen:
   - Text vom Nutzer: so, wie er ist.
   - URL: im eingebauten Browser öffnen (`preview_start` mit `url`) und mit `get_page_text` den Seitentext holen. Er kommt Wort für Wort, ein Web-Fetch liefert dagegen nur eine Zusammenfassung. Nur ohne eingebauten Browser nimmst du Claude in Chrome.
   - Lässt sich die Seite nicht lesen oder verlangt sie eine Anmeldung, bitte den Nutzer um den Text.

   Von der Seite übernimmst du nur die Anzeige: Titel, Ort, Anstellungsart, Einleitung, Aufgaben, Anforderungen, Angebot, Kontakt. Navigation, Bewerbungstipps der Plattform und ähnliche Jobs bleiben draußen.
4. `entwurf/stellenausschreibung.md` schreiben:

   ```markdown
   # <Stelle> – <Firma>

   - Quelle: <URL oder „Text vom Nutzer“>
   - Abgerufen: <JJJJ-MM-TT>

   <vollständiger Anzeigentext, unverändert, nur als Markdown gegliedert>
   ```

Fertig, wenn `entwurf/stellenausschreibung.md` den ganzen Anzeigentext im Wortlaut enthält.

## 2. Analyse

1. Zieh die **Anforderungen** aus der Anzeige: Muss und Kann getrennt, jede als kurzer Begriff.
2. Wähle den **Schwerpunkt**: den aus `daten/stammdaten/profil.yaml`, dessen Tätigkeiten, Projekte und Skills (Feld `schwerpunkte`) die meisten Muss-Anforderungen decken.
   - Deckt keiner die Kernaufgabe der Stelle, **halt an**. Nenne den nächstliegenden Schwerpunkt und biete an: mit ihm weitermachen oder einen neuen Schwerpunkt über `stammdaten-pflegen` anlegen. Erst nach der Antwort des Nutzers geht es weiter.
3. Ordne jede Anforderung zu:
   - **Treffer**: gedeckt durch eine oder mehrere IDs aus den Stammdaten. Du suchst in Kernaussage, Details, Formulierungen und Skills aller Einträge, auch in denen anderer Schwerpunkte.
   - **Lücke**: keine Entsprechung in den Stammdaten.
4. Stell das **Template** fest: das Feld `template` in `daten/standard/<schwerpunkt>/lebenslauf.yaml`, sonst `template` in `daten/einstellungen.yaml`, sonst `klassisch`. Mit ihm renderst du zuerst.
   Spricht die Anzeige **klar** für ein anderes vorhandenes Template (`templates/*.yaml` oder `daten/templates/*.yaml`, nicht `veraltet`), merkst du dir einen **Vorschlag** mit Begründung in einem Halbsatz. Zum Beispiel: Behörde, Bank, Versicherung oder Kanzlei → ein schlichtes, einspaltiges Template; Startup, Agentur oder ausdrücklich gewünschte Kreativität → ein moderneres. Ohne klares Signal gibt es keinen Vorschlag. Gewechselt wird nur, wenn der Nutzer es sagt.

Fertig, wenn jede Anforderung entweder Treffer mit mindestens einer ID oder Lücke ist und das Template feststeht.

## 3. Entwurf bauen

1. `daten/standard/<schwerpunkt>/lebenslauf.yaml` nach `entwurf/lebenslauf.yaml` kopieren. Kopfkommentar anpassen: Firma, Stelle, Datum. Ein Feld `template` aus dem Standard bleibt stehen.
2. Gezielt austauschen, nur mit IDs aus den Stammdaten:
   - **Untertitel**: greift den Stellentitel auf, soweit der Schwerpunkt ihn deckt.
   - **Profil**: startet vom Profiltext des Schwerpunkts und stellt die Treffer nach vorn (`umformuliert: true`).
   - **Tätigkeiten**: Treffer nach vorn, passende Tätigkeiten aus den Stammdaten ergänzen, unpassende ans Ende oder raus. Begriffe der Anzeige dürfen in den `text`, Fakten nur aus derselben Quelle.
   - **Kenntnisse** und **Projekte**: Treffer rein und nach vorn, Unpassendes raus.
3. **Fett** neu setzen, nur für Treffer:
   - Fett wird jeder Begriff, der eine Muss- oder Kann-Anforderung trifft: wörtlich aus der Anzeige (Jira, CI/CD, Code Reviews) oder als konkrete Erfüllung einer abstrakten Anforderung („Cloud-Plattformen“ → **AWS**, „Infrastructure-as-Code“ → **Terraform**). Soft Skills werden nie fett.
   - Jeder solche Begriff muss fett in Profil, Tätigkeit oder Projekt stehen. Deckt ihn bisher nur ein Skill, zieh eine Tätigkeit nach, die ihn belegt (auch aus `details`, z. B. „Scrum mit **Jira**“, `umformuliert: true`). Gibt es keine, bleibt er nur in den Kenntnissen und kommt beim Zeigen unter „nicht fett“.
   - Alles andere Fett aus Standard und Stammdaten entfernst du. In den Kenntnissen ist nie etwas fett.
   - Je Begriff einmal fett im Profil und einmal in Erfahrung und Projekten, jeweils beim ersten Vorkommen. Fett ist nur der Begriff (1–3 Wörter): `**AWS** und **Kubernetes**`, nicht `**AWS und Kubernetes**`.
   - Ändert sich an einer Zeile nur das Fett, braucht sie kein `umformuliert: true`.
   - Trag die Begriffe genau so, wie sie fett im Text stehen, als Liste direkt unter `schwerpunkt:` (bzw. `template:`) in `entwurf/lebenslauf.yaml` ein: `fett: [Jira, Confluence, AWS, Terraform]`. `render.py` meldet einen Fehler, wenn ein Begriff der Liste nirgends fett ist oder etwas fett ist, das nicht in der Liste steht, und warnt bei mehrfachem Fett.
4. `entwurf/bewerbung.yaml` anlegen:

   ```yaml
   firma: <Firma>
   stelle: <Stelle laut Anzeige>
   datum: "<JJJJ-MM-TT>"     # Tag der Freigabe, wird in Schritt 7 gesetzt
   schwerpunkt: <schwerpunkt>
   status: entwurf
   ```

Fertig, wenn jede Aussage im Entwurf eine `quelle` hat, jeder umformulierte `text` als `umformuliert: true` markiert ist und `fett` jeden Treffer mit konkretem Begriff enthält, der in Fließtext belegt ist.

## 4. Rendern und kürzen

```bash
python render.py entwurf
```

- Exit-Code 1: Prüffehler. Behebe sie im Entwurf und rendere neu.
- Mehr als 2 Seiten (Exit-Code 2) oder die Warnung „Seite 2 ist nur zu etwa …“: kürze selbst, in dieser Reihenfolge:
  1. **Verwaiste Wörter**: Zeilen, in die nur ein oder zwei Wörter eines Eintrags gerutscht sind. Jede kostet eine ganze Zeile. Du findest sie mit
     ```bash
     <venv-python> -c "from pypdf import PdfReader; [print(s, '|', z) for s, p in enumerate(PdfReader('entwurf/lebenslauf.pdf').pages, 1) for z in p.extract_text().splitlines() if len(z.split()) <= 2]"
     ```
     (`<venv-python>` siehe `regeln.md`, „Umgebung“.) Kürze den Text des Eintrags davor so weit, dass er eine Zeile weniger braucht (`umformuliert: true`). Zeilen mit festem Inhalt, etwa Abschnittstitel oder Abschlüsse, bleiben, wie sie sind.
  2. **Inhalt**: Was am wenigsten zur Anzeige passt, kommt raus, zuerst Projekte, dann Tätigkeiten, dann Kenntnisse.

  Merk dir alles, was gestrichen wurde. Verschwindet dabei ein Begriff aus `fett` aus dem Text, setz ihn in einer anderen Zeile fett oder nimm ihn aus der Liste und nenn ihn.
- Bei Templates mit Spalten (z. B. `zwei-spalten`) meldet `render.py` die Höhe jeder Spalte (`SPALTEN …`):
  - `WARNUNG  Spalte 'seite' … braucht eine Seite mehr`: Die Seitenleiste bestimmt die Seitenzahl. Kürze **in dieser Spalte**, also bei den Kenntnissen (die am wenigsten zur Anzeige passen zuerst), nicht bei Tätigkeiten oder Projekten.
  - `HINWEIS  Spalte …`: Die Seitenleiste ist länger als die Hauptspalte, passt aber. Du kürzt nicht, du nennst es nur beim Zeigen.
- Schau dir das PDF mit dem Read-Tool an, bevor der Nutzer es sieht: Umbrüche, verwaiste Wörter, ein leerer Seitenrest.

Fertig, wenn `render.py entwurf` mit Exit-Code 0, ohne Füllwarnung und ohne `WARNUNG  Spalte …` endet und du das PDF gesehen hast.

## 5. Zeigen

Eine Nachricht, ohne Zwischenstopp davor:

- das PDF (`entwurf/lebenslauf.pdf`) als Datei
- **Schwerpunkt** mit einem Satz Begründung
- **Treffer**: Anforderung → was im Lebenslauf dafür steht
- **Fett**: die Liste `fett`, und welche Treffer nur in den Kenntnissen stehen und deshalb nicht fett sind
- **Lücken**: jede mit der Frage „Hast du X? Wo ist es belegt?“
- **Gestrichen**: was beim Kürzen rausflog
- Seitenzahl
- **Template**: das verwendete, und falls du in Schritt 2 einen Vorschlag hast: „Für <Firma> würde ich <template> nehmen, weil …“

## 6. Korrekturen

Der Nutzer korrigiert im Chat, du änderst `entwurf/lebenslauf.yaml`, renderst neu (Schritt 4) und zeigst das neue PDF mit den Änderungen in einem Satz.

Will der Nutzer ein anderes Template („nimm zwei-spalten“), setzt du `template: <name>` direkt unter `schwerpunkt:` in `entwurf/lebenslauf.yaml` und renderst neu. Ein anderes Template kann die Seitenzahl ändern: Kürze dann nach Schritt 4, und was du dabei streichst, nennst du. Neue Templates oder geänderte Farben gibt es nur über `template-pflegen`.

Bestätigt der Nutzer eine **Lücke** mit Beleg, ergänzt du sie zuerst in den Stammdaten nach `regeln.md`: Diff zeigen, nach OK schreiben, `render.py --pruefen`, Commit. Erst dann zitierst du die neue ID im Entwurf. Ohne Beleg bleibt sie Lücke und kommt nicht in den Lebenslauf. Bei der Freigabe trägst du sie in `daten/stammdaten/offen.md` unter „Lücken aus Stellenausschreibungen“ ein.

Fertig, wenn der Nutzer den Entwurf freigibt.

## 7. Freigabe

1. **Sammelfrage**: Liste alle Texte mit `umformuliert: true` auf, auch das Profil, und frag einmal, welche als freigegebene Formulierungen in die Stammdaten sollen. Die gewählten hängst du an `formulierungen` der jeweiligen Quelle an (beim Profil an keine: Profiltexte ändert nur `stammdaten-pflegen`). Ein übernommener Text ist danach keine Umformulierung mehr: Entferne `umformuliert: true` bei ihm im Entwurf und überall in `daten/standard/*/lebenslauf.yaml`, wo derselbe Text zur selben Quelle steht. Danach `render.py --pruefen`. Die Warnung „ist inzwischen freigegeben“ zeigt Stellen, die du übersehen hast.
2. Ordnername bilden: `daten/bewerbungen/<JJJJ-MM-TT>_<firma>_<stelle>/`. Firma und Stelle in Kleinbuchstaben, Umlaute als ae/oe/ue/ss, alles andere als `-`, ohne Rechtsform (GmbH, AG …) und ohne Zusatz wie (w/m/d), höchstens etwa 40 Zeichen je Teil.
3. In `entwurf/bewerbung.yaml` `datum` auf heute und `status` auf `freigegeben` setzen. In `entwurf/lebenslauf.yaml` steht danach immer ein Feld `template` mit dem verwendeten Template (fehlt es, trägst du es unter `schwerpunkt:` ein). So bleibt die Bewerbung bei ihrem Aussehen, auch wenn sich das Standard-Template später ändert.
4. Verschieben: `git mv` geht nicht (der Entwurf ist gitignoriert), also `mkdir -p <ordner> && mv entwurf/* <ordner>/`. Der Ordner enthält danach `lebenslauf.yaml`, `lebenslauf.pdf` (eingefroren, nicht neu rendern), `stellenausschreibung.md` und `bewerbung.yaml`.
5. `python render.py --pruefen`, dann im Daten-Repo committen und, falls es ein Remote hat, pushen (siehe `regeln.md`, „Commits“): `Bewerbung: <Firma> – <Stelle>`, mit den übernommenen Formulierungen als eigene Zeile.
6. Dauer melden: Startzeit bis jetzt, gemessen an den 15 Minuten.

Fertig, wenn der Commit steht, `entwurf/` leer ist und der Nutzer die Dauer kennt.

## Danach

- Den `status` in `bewerbung.yaml` pflegt der Nutzer per Zuruf (zum Beispiel `versendet`, `gespraech`, `absage`, `zusage`). Du änderst nur dieses Feld und committest: `Bewerbung <ordner>: Status <status>`.
- Haben sich beim Lauf Stammdaten geändert, die ein Standardlebenslauf zitiert oder die zu seinem Schwerpunkt passen, schlag am Ende vor, `daten/standard/<schwerpunkt>/` nachzuziehen. Der Nutzer entscheidet.
