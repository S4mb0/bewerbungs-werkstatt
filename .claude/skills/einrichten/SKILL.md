---
name: einrichten
description: Richtet die Bewerbungs-Werkstatt für einen neuen Nutzer ein - Umgebung prüfen, Daten-Repo anlegen, Person und Foto erfassen, den bisherigen Lebenslauf importieren, Schwerpunkte, Kategorien und Template festlegen und die ersten Standardlebensläufe erstellen. Verwenden beim ersten Start, wenn daten/ fehlt oder unvollständig ist, oder wenn der Nutzer sagt „richte mich ein“ bzw. eine abgebrochene Einrichtung fortsetzen will.
---

# Einrichten

Ein neuer Nutzer hat das System geklont. Am Ende hat er ein eigenes Daten-Repo `daten/` mit geprüften Stammdaten und mindestens einem freigegebenen Standardlebenslauf, und kann mit `lebenslauf-anpassen` loslegen.

Vor dem ersten Schritt liest du [`../regeln.md`](../regeln.md). Sie gilt für jeden Eintrag, jede ID und jeden Commit. Begriffe: `GLOSSARY.md`. Alle Befehle laufen im Repo-Wurzelordner. Zuerst die Update-Prüfung aus `regeln.md` (Abschnitt „Umgebung“), einmal pro Gespräch. Unter macOS/Linux heißt Python meist `python3`.

Das Ziel ist Faktentreue: In die Stammdaten kommt nur, was der Nutzer bestätigt. Was du aus Dokumenten liest, ist ein **Vorschlag**, bis er es freigibt.

## 0. Wo stehen wir?

Die Einrichtung lässt sich jederzeit abbrechen und später fortsetzen. Stell anhand der Dateien fest, wo es weitergeht, und sag es dem Nutzer in einem Satz:

| Zustand | weiter mit |
|---|---|
| `daten/` fehlt | 1 |
| `daten/stammdaten/person.yaml` fehlt | 2 |
| `berufserfahrung.yaml` oder `ausbildung.yaml` fehlt | 3 |
| `daten/stammdaten/offen.md` hat Punkte unter „Nachfragen beim Einrichten“ | 4 |
| `profil.yaml` oder `kategorien.yaml` fehlt | 5 |
| kein `daten/standard/*/lebenslauf.yaml` | 6 |
| ein Schwerpunkt ohne Standardlebenslauf | 7 |
| alles da | fertig, siehe „Danach“ |

## 1. Umgebung und Daten-Repo

1. `python einrichten.py`. Es prüft Python, git und einen Browser und legt `.venv` an. Fehlt etwas, nenn dem Nutzer die ausgegebenen Befehle und warte, bis er sie ausgeführt hat. Installiere nichts auf Systemebene selbst.
2. Frag in einer Nachricht:
   - **Name und E-Mail für Git**, nur für die Versionsgeschichte von `daten/`. Sie verlassen den Rechner nur, wenn er später ein Remote einrichtet. Ist global schon etwas eingestellt (`git config --global user.name`), schlag das vor. Wer keine E-Mail angeben will, nimmt `lokal@bewerbungs-werkstatt`.
   - **Wo die Daten liegen sollen:** nur lokal (Standard) oder zusätzlich in einem **privaten** GitHub-Repo (Sicherung, mehrere Rechner; braucht einen GitHub-Account und `gh`).
3. `python einrichten.py --daten-anlegen --git-name "<Name>" --git-email "<E-Mail>"`. Es legt `daten/` als eigenes Git-Repo mit leerem Gerüst an und committet.
4. Nur bei „privates GitHub-Repo“:
   - `gh auth status` muss angemeldet sein, sonst bittet der Nutzer selbst um `gh auth login`.
   - `gh repo create <name> --private --source daten --push`. Schlag als Namen `bewerbungsdaten` vor.
   - Prüf danach `gh repo view <name> --json visibility`: Es muss `PRIVATE` sein. Sonst halt an und lass es den Nutzer umstellen.

Fertig, wenn `daten/` ein Git-Repo mit einem ersten Commit ist.

## 2. Person und Foto

Frag in einer Nachricht nach: Name, Wohnort (nur Ort, keine Straße), Telefon, E-Mail, Web-Links (z. B. LinkedIn, GitHub, Portfolio), optional Geburtsdatum und -ort, und ob ein **Foto** in den Lebenslauf soll. In Deutschland ist es üblich, aber freiwillig.

Liegt ein Foto vor:

1. Der Nutzer nennt den Pfad. Kopier die Datei nach `daten/stammdaten/foto.<endung>` (JPG oder PNG).
2. Sieh es dir mit dem Read-Tool an. Prüfe:
   - Ist es ein Porträt im Hochformat?
   - Ist das Gesicht nicht zu klein?
   - Ist die Auflösung ausreichend (mindestens etwa 400 px breit)?
   - Bei runden Fotos: Ist oben genug Platz über dem Kopf?

   Ist etwas davon nicht erfüllt, sag es und schlag vor, ein anderes zu nehmen. Bearbeite das Bild nicht selbst.

`daten/stammdaten/person.yaml` schreiben (Schema in `regeln.md`; ID: Kurzform des Namens, z. B. `lena-beispiel`), Diff zeigen, nach OK committen: `Stammdaten: Person angelegt`.

## 3. Import

Frag nach Quellen, beliebig viele:

- bisheriger **Lebenslauf** (PDF oder Word)
- **Zeugnisse**, Urkunden, Zertifikate (für Zeiträume, offizielle Bezeichnungen, Noten)
- **LinkedIn**-Profil als PDF (auf dem Profil: „Mehr“ → „Als PDF speichern“)
- eigene Notizen oder Projektseiten

Lies PDFs mit dem Read-Tool. Für Word-Dateien nimm einen Docx-Skill, falls verfügbar, sonst bitte um ein PDF. Ohne Dokumente führst du stattdessen ein **Interview**: Stationen rückwärts ab heute, je Station Zeitraum, Titel, Art und was er dort gemacht hat.

Aus den Quellen baust du einen **Entwurf** der Stammdaten, direkt in die Dateien, ohne Commit:

- `berufserfahrung.yaml`: Arbeitgeber → Positionen → Tätigkeiten. Eine Tätigkeit = eine sachliche Aussage. `kernaussage` ist ein Satz, `details` enthält alles, was die Quelle dazu hergibt. Zeiträume monatsgenau, maßgeblich ist der Nachweis.
- `ausbildung.yaml`: Abschlüsse mit offizieller Bezeichnung laut Nachweis.
- `projekte.yaml`: nur, wenn es Projekte gibt (privat, Studium, beruflich, Ehrenamt).
- `skills.yaml`: jeder Skill mit Beleg (siehe `regeln.md`). Kategorien setzt du vorläufig und bestätigst sie in Schritt 5. Niveau `Grundlagen`, `gut` oder `sehr gut`. Bei gesprochenen Sprachen frei, z. B. `Muttersprache`, `fließend`, `B2`.
- `schwerpunkte` an Tätigkeiten und Projekten: vorläufig, siehe Schritt 5.
- Was unklar ist oder sich widerspricht, kommt **nicht** in die Daten. Es kommt nach `offen.md` unter einer neuen Überschrift „Nachfragen beim Einrichten“.
- Bei Zeugnissen fragst du, ob eine bereinigte Kopie (ohne Geburtsdatum, Adresse, Unterschrift o. Ä.) als Anlage nach `daten/anlagen/` soll. Originale kopierst du nicht.

Lauf `python render.py --pruefen`. Die Prüfung meldet noch fehlende Dateien (`profil.yaml`, `kategorien.yaml`), das ist hier erwartet. Alle anderen Fehler behebst du.

Zeig dann eine **Übersicht**, nicht das ganze YAML:
- je Arbeitgeber die Positionen mit Zeitraum und die Kernaussagen der Tätigkeiten
- die Abschlüsse
- die Skills nach Kategorie
- die Zahl der offenen Fragen

Der Nutzer korrigiert, bis es stimmt. Dann committen: `Stammdaten: Import aus <Quellen>`.

## 4. Nachfragen

Geh die Punkte unter „Nachfragen beim Einrichten“ in `offen.md` durch, in **einer** Nachricht, nummeriert. Typisch:
- Lücken im Lebenslauf
- Zeiträume ohne Monat
- „verschiedene Tools“ ohne Namen
- eigener Anteil oder Team
- Widersprüche zwischen Lebenslauf und Zeugnis (das Zeugnis gilt)

Was der Nutzer beantwortet, trägst du ein und streichst es aus `offen.md`. Was er nicht weiß, verschiebst du unter „Nachreichen“. Zahlen, Ergebnisse und Verantwortungen schreibst du nur, wenn er sie nennt.

`--pruefen`, Commit: `Stammdaten: Nachfragen geklärt`.

## 5. Schwerpunkte und Kategorien

Zeig in einer Nachricht:

- **Schwerpunkte**: 1 bis 4 Richtungen, in die er sich bewirbt. Leite sie aus Stationen und Wunsch ab und frag nach dem Wunsch. Beispiele: `pflege` und `praxisanleitung`; `vertrieb-innendienst` und `kundenservice`; `devops` und `softwareentwicklung`. Je Schwerpunkt:
  - ID und ein Satz, wofür er steht
  - ein **Profiltext** nur aus Fakten der Stammdaten, 3 bis 5 Sätze, mit `**fett**` für 2 bis 4 Kernbegriffe
  - welche Tätigkeiten, Projekte und Skills ihn tragen
- **Kategorien** für die Kenntnisse, passend zum Beruf, in der Reihenfolge, in der sie im Lebenslauf erscheinen sollen. Beispiele:
  - Pflege: „Fachliche Kenntnisse“, „Dokumentation & Software“, „Arbeitsweise“, „Sprachen“
  - IT: „Programmiersprachen“, „Cloud & Betrieb“, „Tools & Systeme“, „Arbeitsweise“, „Sprachen“
  - Kaufmännisch: „Fachwissen“, „Software“, „Arbeitsweise“, „Sprachen“

  `gesprochene-sprache` und `arbeitsweise` sind Pflicht. Nur ihre Anzeigenamen sind frei.

Nach dem OK schreiben:
- `profil.yaml` und `kategorien.yaml`
- `schwerpunkte` an Tätigkeiten, Projekten und Skills
- die Kategorien der Skills

Dann `--pruefen` ohne Fehler und Commit: `Stammdaten: Schwerpunkte und Kategorien`.

## 6. Template

Zeig die mitgelieferten Templates (`templates/*.yaml`, je die `beschreibung`) und rendere den ersten Standardlebenslauf aus Schritt 7 testweise mit zwei oder drei von ihnen (`python render.py --vorschau <template>`, sobald es ihn gibt). Andernfalls nimm vorerst `klassisch`. Sind dem Nutzer Farbe oder Schrift wichtig, bietet `template-pflegen` ein eigenes Template an. Mach das erst nach der Einrichtung.

Das gewählte Template kommt als `template:` nach `daten/einstellungen.yaml`.

## 7. Standardlebensläufe

Für jeden Schwerpunkt `daten/standard/<schwerpunkt>/lebenslauf.yaml`, Aufbau wie `beispiel/standard/devops/lebenslauf.yaml`:

- jede Aussage mit `quelle`, Umformuliertes mit `umformuliert: true`
- `untertitel`: Berufsbezeichnung des Schwerpunkts, nur was die Stammdaten decken
- Berufserfahrung neueste zuerst, die stärksten Tätigkeiten für den Schwerpunkt nach vorn
- `python render.py daten/standard/<schwerpunkt>`: höchstens 2 Seiten, Ziel 1, ohne Füllwarnung und ohne `WARNUNG  Spalte …`. Kürzen wie in `lebenslauf-anpassen`, Schritt 4.
- PDF mit dem Read-Tool ansehen, dann dem Nutzer zeigen, mit einem Satz zur Auswahl

Korrekturen einarbeiten, bis er freigibt. Commit je Schwerpunkt: `Standardlebenslauf <schwerpunkt>`. Hat das Daten-Repo ein Remote, danach pushen.

Ist der erste Standardlebenslauf freigegeben und der Nutzer will Templates vergleichen, mach Schritt 6 jetzt mit `--vorschau`.

## Danach

Sag in wenigen Sätzen, wie es weitergeht:
- **Stellenanzeige** schicken (Text oder Link) → `lebenslauf-anpassen`
- **Neues** aus Beruf oder Projekten erzählen → `stammdaten-pflegen`
- anderes **Aussehen** → `template-pflegen`
- **Updates** des Systems: `python einrichten.py --aktualisieren`
- `daten/` regelmäßig sichern: Es ist ein Git-Repo, bei einem Remote genügt Pushen, sonst den Ordner kopieren.
