---
name: lebenslauf-anpassen
description: Passt den Lebenslauf des Nutzers an eine Stellenausschreibung an, schreibt auf Wunsch ein Anschreiben dazu und legt die Bewerbung ab. Verwenden, wenn der Nutzer eine Stellenausschreibung (Text oder URL) schickt, ein Anschreiben zu einem Entwurf möchte oder einen Entwurf in entwurf/ korrigieren oder freigeben will.
---

# Lebenslauf anpassen

Aus einer **Stellenausschreibung** wird ein **Entwurf** in `entwurf/` und nach Freigabe durch den Nutzer eine **Bewerbung** in `daten/bewerbungen/`. Auf Wunsch gehört ein **Anschreiben** dazu (Schritt 6). Ziel: höchstens 15 Minuten von der Anzeige bis zur Freigabe des Lebenslaufs, Gegenlesen eingeschlossen, und höchstens 10 Minuten mehr für das Anschreiben.

Vor dem ersten Schritt liest du [`../regeln.md`](../regeln.md). Sie gilt für jede Aussage, jede Lücke und jeden Commit in diesem Ablauf. Begriffe: `GLOSSARY.md`. Alle Befehle laufen im Repo-Wurzelordner. Zuerst die Update-Prüfung aus `regeln.md` (Abschnitt „Umgebung“), einmal pro Gespräch.

## 1. Start

1. Startzeit festhalten: `date +%H:%M`.
2. Liegt schon etwas in `entwurf/`, ist das ein unfertiger Entwurf. Frag den Nutzer, ob er weitergeführt oder verworfen wird, und mach dann entsprechend mit Schritt 7 oder hier weiter.
   Sagt der Nutzer schon mit der Anzeige, dass er ein Anschreiben will („mit Anschreiben“), merk es dir: Dann fragst du in Schritt 5 nicht danach.
3. Anzeige **wörtlich** einlesen:
   - Text vom Nutzer: so, wie er ist.
   - URL: im eingebauten Browser öffnen (`preview_start` mit `url`) und mit `get_page_text` den Seitentext holen. Er kommt Wort für Wort, ein Web-Fetch liefert dagegen nur eine Zusammenfassung. Nur ohne eingebauten Browser nimmst du Claude in Chrome.
   - Lässt sich die Seite nicht lesen oder verlangt sie eine Anmeldung, bitte den Nutzer um den Text.

   Von der Seite übernimmst du nur die Anzeige: Titel, Ort, Anstellungsart, Einleitung, Aufgaben, Anforderungen, Angebot, Kontakt. Navigation, Bewerbungstipps der Plattform und ähnliche Jobs bleiben draußen. Zum Kontakt gehören auch Ansprechperson, Anschrift und Kennziffer: Das Anschreiben braucht sie.
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

5. Halte fest, ob die Anzeige ausdrücklich nach **Gehaltsvorstellung** oder **Eintrittstermin** fragt. Das braucht nur das Anschreiben.

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
   - Je Begriff höchstens einmal fett pro Bereich (Profil, Berufserfahrung, Projekte), jeweils beim ersten Vorkommen im Bereich. Fett ist nur der Begriff (1–3 Wörter): `**AWS** und **Kubernetes**`, nicht `**AWS und Kubernetes**`.
   - Ändert sich an einer Zeile nur das Fett, braucht sie kein `umformuliert: true`.
   - Trag die Begriffe genau so, wie sie fett im Text stehen, als Liste direkt unter `schwerpunkt:` (bzw. `template:`) in `entwurf/lebenslauf.yaml` ein: `fett: [Jira, Confluence, AWS, Terraform]`. `render.py` meldet einen Fehler, wenn ein Begriff der Liste nirgends fett ist oder etwas fett ist, das nicht in der Liste steht, und warnt bei mehrfachem Fett.
4. `entwurf/bewerbung.yaml` anlegen:

   ```yaml
   firma: <Firma>
   stelle: <Stelle laut Anzeige>
   datum: "<JJJJ-MM-TT>"     # Tag der Freigabe, wird in Schritt 8 gesetzt
   schwerpunkt: <schwerpunkt>
   status: entwurf
   kennziffer: <nur, wenn die Anzeige eine nennt>
   empfaenger:               # aus dem Kontakt der Anzeige, nur was dort steht
     abteilung: <z. B. Personalabteilung>
     ansprechperson: <z. B. Frau Dr. Erika Beispiel>
     strasse: <Straße und Hausnummer>
     plz: "<PLZ>"
     ort: <Ort>
   ```

   `firma` ist der Name, wie er im Anschriftfeld stehen soll (mit Rechtsform, ohne Werbezusätze). Felder, die die Anzeige nicht hergibt, lässt du weg, ohne Kontakt das ganze `empfaenger`.

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
- **Anschreiben**: Hat der Nutzer es nicht schon in Schritt 1 gewollt, fragst du am Ende „Soll ich ein Anschreiben dazu schreiben?“. Ohne Ja gibt es keins.

Will er eins, geht es mit Schritt 6 weiter, sonst mit Schritt 7. Korrekturen am Lebenslauf nimmst du auch an, während das Anschreiben entsteht.

## 6. Anschreiben (optional)

Nur, wenn der Nutzer eins will. Startzeit festhalten (`date +%H:%M`), Ziel: höchstens 10 Minuten bis zum gezeigten Anschreiben.

### 6.1 Ausgangspunkt

Ausgangspunkt ist das **Standardanschreiben** des Schwerpunkts: `daten/standard/<schwerpunkt>/anschreiben.yaml`.

- Fehlt es, gibt es aber das Standardanschreiben eines anderen Schwerpunkts, sag das in einem Satz und nimm das nächstliegende.
- Gibt es gar keins, halt an: Standardanschreiben entstehen im Schritt „Anschreiben“ von `einrichten` (alte Anschreiben importieren, Bausteine, Standardanschreiben je Schwerpunkt). Biete an, das jetzt zu machen, und mach danach hier weiter. Der Entwurf bleibt so lange in `entwurf/` liegen.

Kopier es nach `entwurf/anschreiben.yaml` und pass den Kopfkommentar an (Firma, Stelle, Datum). Lies dazu `daten/stammdaten/anschreiben.yaml` (Bausteine und Rahmendaten).

### 6.2 Eine Rückfrage

Frag in **einer** Nachricht, nummeriert, nur, was du nicht aus Anzeige und Stammdaten hast:

1. **Motivation**: „Was reizt dich an <Firma> / dieser Stelle?“ Dazu 2–3 Vorschläge, die du aus der Anzeige ziehst (Produkt, Technologie, Branche, Aufgabe, Arbeitsweise), und die passenden Motivations-Bausteine. Du erfindest keine Gründe: Nur was der Nutzer sagt oder auswählt, wird zu seiner Motivation.
2. **Gehalt**, nur wenn die Anzeige danach fragt (Schritt 2): „Hinterlegt ist <gehalt aus rahmen>, passt das hier?“ Fehlt der Wert in den Stammdaten, fragst du danach, ebenso nach der Verfügbarkeit, wenn sie gefragt ist und fehlt.
3. **Ansprechperson**, nur wenn die Anzeige keine nennt: „Kennst du eine Ansprechperson? Sonst schreibe ich ‚Sehr geehrte Damen und Herren‘.“

### 6.3 Absätze bauen

Jeder Absatz in `entwurf/anschreiben.yaml` hat eine `art` und `quellen` (IDs aus den Stammdaten) oder eine `herkunft` (`anzeige`, `nutzer`), oft beides. Die Faktentreue aus `regeln.md` gilt für jeden Satz über den Nutzer.

- **einstieg**: Bezug auf Stelle und Firma (`herkunft: anzeige`), gern mit einem Einstiegs-Baustein (`quellen: [baust-…]`). Ohne Floskeln wie „hiermit bewerbe ich mich“.
- **hauptteil** (1–3 Absätze): die 2–3 stärksten **Treffer** aus Schritt 2, erzählt statt aufgezählt: was der Nutzer getan hat und wozu. `quellen` sind die IDs der Treffer (Tätigkeiten, Projekte, Abschlüsse, Skills). Fakten stammen nur aus Kernaussage, Details und Formulierungen dieser Quellen; Begriffe der Anzeige darfst du verwenden. Lücken kommen nicht vor.
- **motivation**: die Antwort des Nutzers aus 6.2 (`herkunft: nutzer`), bei einem gewählten Baustein zusätzlich mit dessen ID. Antwortet er darauf nicht, bleibt es beim Bezug auf die Anzeige (`herkunft: anzeige`) ohne persönliche Begründung.
- **rahmen**: nur, wenn die Anzeige nach Gehalt oder Eintrittstermin fragt. `quellen: [rahmen]`; weicht das Gehalt auf Wunsch des Nutzers vom hinterlegten ab, zusätzlich `herkunft: nutzer`.
- **schluss**: ein Schluss-Baustein, ohne `text` (`quellen: [baust-…]`) oder angepasst.

Dazu:
- Jeder `text`, der nicht wörtlich ein freigegebener Text einer seiner Quellen ist, bekommt `umformuliert: true`. Ein Absatz ohne `text` zeigt den Baustein bzw. die Kernaussage seiner einzigen Quelle.
- Ich-Form, sachlich, im Ton der Bausteine, 250–350 Wörter. Kein Fett, keine Platzhalter wie `[Firma]` mehr.
- `betreff` setzt du nur, wenn „Bewerbung als <Stelle>“ nicht passt. `render.py` nimmt die Stelle aus `bewerbung.yaml` ohne „(m/w/d)“.
- **Anrede** in `entwurf/bewerbung.yaml` unter `empfaenger.anrede`: „Sehr geehrte Frau …“ bzw. „Sehr geehrter Herr …“ nur, wenn die Anzeige Frau oder Herr nennt, sonst „Guten Tag <Vorname Nachname>“. Ohne Ansprechperson fehlt das Feld, dann gilt „Sehr geehrte Damen und Herren“.

### 6.4 Rendern und zeigen

```bash
python render.py entwurf
```

Das rendert Lebenslauf und Anschreiben (`entwurf/anschreiben.pdf`) mit demselben Template. Das Anschreiben hat **genau 1 Seite**: Ist es länger, kürzt du die Hauptteil-Sätze, die am wenigsten zur Anzeige passen. Meldet `render.py` „… Wörter im Brieftext“, kürzt oder ergänzt du aus denselben Quellen. Sieh dir das PDF mit dem Read-Tool an.

Zeig in einer Nachricht:
- das PDF (`entwurf/anschreiben.pdf`) als Datei
- je Absatz eine Zeile: Art, Quellen, Herkunft (z. B. „hauptteil – taet-k8s-betrieb, taet-pipelines“, „motivation – von dir“)
- Wörterzahl und Dauer seit der Startzeit dieses Schritts

Korrekturen am Anschreiben laufen wie in Schritt 7.

Fertig, wenn `render.py entwurf` mit Exit-Code 0 endet, das Anschreiben genau 1 Seite hat und du es gezeigt hast.

## 7. Korrekturen

Der Nutzer korrigiert im Chat, du änderst `entwurf/lebenslauf.yaml` bzw. `entwurf/anschreiben.yaml`, renderst neu (Schritt 4 bzw. 6.4) und zeigst das neue PDF mit den Änderungen in einem Satz.

Will der Nutzer ein anderes Template („nimm zwei-spalten“), setzt du `template: <name>` direkt unter `schwerpunkt:` in `entwurf/lebenslauf.yaml` und renderst neu. Ein anderes Template kann die Seitenzahl ändern: Kürze dann nach Schritt 4, und was du dabei streichst, nennst du. Das Anschreiben wechselt mit, weil es immer das Template des Lebenslaufs nimmt. Neue Templates oder geänderte Farben gibt es nur über `template-pflegen`.

Bestätigt der Nutzer eine **Lücke** mit Beleg, ergänzt du sie zuerst in den Stammdaten nach `regeln.md`: Diff zeigen, nach OK schreiben, `render.py --pruefen`, Commit. Erst dann zitierst du die neue ID im Entwurf. Ohne Beleg bleibt sie Lücke und kommt nicht in den Lebenslauf. Bei der Freigabe trägst du sie in `daten/stammdaten/offen.md` unter „Lücken aus Stellenausschreibungen“ ein.

Fertig, wenn der Nutzer den Entwurf freigibt.

## 8. Freigabe

1. **Sammelfrage**: Liste alle Texte mit `umformuliert: true` auf, auch das Profil und die Absätze des Anschreibens, und frag einmal, welche als freigegebene Formulierungen in die Stammdaten sollen. Die gewählten hängst du an `formulierungen` der jeweiligen Quelle an (beim Profil an keine: Profiltexte ändert nur `stammdaten-pflegen`). Ein übernommener Text ist danach keine Umformulierung mehr: Entferne `umformuliert: true` bei ihm im Entwurf und überall in `daten/standard/*/lebenslauf.yaml`, wo derselbe Text zur selben Quelle steht. Danach `render.py --pruefen`. Die Warnung „ist inzwischen freigegeben“ zeigt Stellen, die du übersehen hast.

   Für Absätze des Anschreibens gilt:
   - Ein **hauptteil** mit genau einer Quelle (Tätigkeit oder Projekt) kann eine Formulierung dieser Quelle werden. Einer mit mehreren Quellen nicht: Biete stattdessen einzelne Sätze daraus als Formulierungen ihrer jeweiligen Quelle an.
   - **einstieg**, **motivation** und **schluss** können neue **Bausteine** werden (`daten/stammdaten/anschreiben.yaml`, ID `baust-<thema>`, Art wie der Absatz, `schwerpunkte` optional), aber nur ohne Bezug auf diese Firma oder Stelle. Schlag dafür eine allgemeine Fassung vor und übernimm sie erst nach OK. Im Entwurf bleibt der Absatz, wie er ist.
   - Was der Nutzer zu Gehalt oder Verfügbarkeit neu gesagt hat, kommt nur auf ausdrücklichen Wunsch nach `rahmen`.
2. Ordnername bilden: `daten/bewerbungen/<JJJJ-MM-TT>_<firma>_<stelle>/`. Firma und Stelle in Kleinbuchstaben, Umlaute als ae/oe/ue/ss, alles andere als `-`, ohne Rechtsform (GmbH, AG …) und ohne Zusatz wie (w/m/d), höchstens etwa 40 Zeichen je Teil.
3. In `entwurf/bewerbung.yaml` `datum` auf heute und `status` auf `freigegeben` setzen. Gibt es ein Anschreiben, renderst du nur dieses neu, damit es das Datum der Freigabe trägt: `python render.py --nur-anschreiben entwurf`. Der Lebenslauf wird nicht neu gerendert. In `entwurf/lebenslauf.yaml` steht danach immer ein Feld `template` mit dem verwendeten Template (fehlt es, trägst du es unter `schwerpunkt:` ein). So bleibt die Bewerbung bei ihrem Aussehen, auch wenn sich das Standard-Template später ändert.
4. Verschieben: `git mv` geht nicht (der Entwurf ist gitignoriert), also `mkdir -p <ordner> && mv entwurf/* <ordner>/`. Der Ordner enthält danach `lebenslauf.yaml`, `lebenslauf.pdf` (eingefroren, nicht neu rendern), `stellenausschreibung.md`, `bewerbung.yaml` und, falls es eins gibt, `anschreiben.yaml` und `anschreiben.pdf` (ebenfalls eingefroren).
5. `python render.py --pruefen`, dann im Daten-Repo committen und, falls es ein Remote hat, pushen (siehe `regeln.md`, „Commits“): `Bewerbung: <Firma> – <Stelle>` (mit Anschreiben: `Bewerbung: <Firma> – <Stelle>, mit Anschreiben`), mit den übernommenen Formulierungen und Bausteinen als eigene Zeile.
6. Dauer melden: Startzeit bis jetzt, gemessen an den 15 Minuten (mit Anschreiben: 25 Minuten).

Fertig, wenn der Commit steht, `entwurf/` leer ist und der Nutzer die Dauer kennt.

## Danach

- Den `status` in `bewerbung.yaml` pflegt der Nutzer per Zuruf (zum Beispiel `versendet`, `gespraech`, `absage`, `zusage`). Du änderst nur dieses Feld und committest: `Bewerbung <ordner>: Status <status>`.
- Haben sich beim Lauf Stammdaten geändert, die ein Standardlebenslauf oder Standardanschreiben zitiert oder die zu seinem Schwerpunkt passen, schlag am Ende vor, `daten/standard/<schwerpunkt>/` nachzuziehen. Der Nutzer entscheidet.
