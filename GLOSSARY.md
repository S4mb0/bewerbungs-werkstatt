# Bewerbung

System, um die eigenen Bewerbungsunterlagen aus geprüften Fakten schnell an einzelne Stellenausschreibungen anzupassen. Jeder Nutzer pflegt seine eigenen Daten in `daten/`.

## Language

**Stammdaten**:
Die eine vollständige Sammlung aller Inhalte über den Nutzer: Tätigkeiten, Skills, Erfahrungen, Projekte, Ausbildung, Abschlüsse. Nur Inhalte, keine Dokumente.
_Avoid_: Master-Profil, Sammlung, Datenbank

### Stammdaten

**Arbeitgeber**:
Ein Unternehmen, bei dem der Nutzer eine oder mehrere Positionen hatte.
_Avoid_: Firma, Station

**Position**:
Ein zusammenhängender Abschnitt bei einem Arbeitgeber mit eigenem Zeitraum, Art (Praktikum, Werkstudent, Ausbildung, Festanstellung) und Titel.
_Avoid_: Stelle, Job, Rolle

**Tätigkeit**:
Eine einzelne sachliche Aussage darüber, was der Nutzer in einer Position getan hat, mit Details und optional freigegebenen Formulierungen.
_Avoid_: Aufgabe, Bullet, Stichpunkt

**Projekt**:
Ein abgegrenztes Vorhaben mit Kontext privat, Studium oder beruflich; kann mehrere Repos bündeln.
_Avoid_: Repo, Hobbyprojekt

**Abschluss**:
Ein Schulabschluss, eine Berufsausbildung, ein Studium oder ein Zertifikat, abgeschlossen oder laufend.
_Avoid_: Bildung, Qualifikation

**Skill**:
Eine Fähigkeit mit Kategorie und Niveau, darunter auch gesprochene Sprachen und Arbeitsweise.
_Avoid_: Kenntnis, Kompetenz

**Beleg**:
Der Verweis einer Tätigkeit, eines Projekts oder einer Anlage auf einen Skill, der zeigt, dass der Skill wirklich vorhanden ist.
_Avoid_: Nachweis, Referenz

**Schwerpunkt**:
Eine Richtung, in die sich der Nutzer bewirbt (z. B. devops oder embedded); jeder Nutzer legt seine eigenen an.
_Avoid_: Tag, Kategorie, Profil

**Profiltext**:
Der einleitende Absatz eines Lebenslaufs; in den Stammdaten je Schwerpunkt als Ausgangstext hinterlegt.
_Avoid_: Summary, Über mich

### Lebenslauf und Bewerbung

**Lebenslauf**:
Eine konkrete Auswahl und Formulierung aus den Stammdaten, dargestellt im Template.
_Avoid_: CV, Resume

**Standardlebenslauf**:
Ein vom Nutzer freigegebener Lebenslauf für einen Schwerpunkt, ohne Bezug zu einer bestimmten Stellenausschreibung; Ausgangspunkt jeder Anpassung.
_Avoid_: Basis-CV, Default

**Lücke**:
Eine Anforderung einer Stellenausschreibung, für die es in den Stammdaten keine Entsprechung gibt.
_Avoid_: fehlender Skill, Gap

**Stellenausschreibung**:
Die Anzeige einer konkreten Stelle, an die ein Lebenslauf angepasst wird.
_Avoid_: Stellenbeschreibung, Job-Posting

**Template**:
Das Aussehen der Bewerbungsunterlagen, unabhängig vom Inhalt: ein Grundlayout plus Parameter wie Farbe, Schrift, Foto, Überschriften und Reihenfolge der Abschnitte. Es gibt mehrere, eins davon ist das Standard-Template.
_Avoid_: Vorlage, Design, Theme

**Grundlayout**:
Die Struktur, auf der ein Template aufbaut (z. B. einspaltig, zwei Spalten mit Seitenleiste, Kopfband). Legt fest, welche Parameter ein Template setzen darf.
_Avoid_: Layout, Basis-Template

**Einstellungen**:
Die persönlichen Vorgaben in `daten/einstellungen.yaml`, u. a. das Standard-Template.
_Avoid_: Konfiguration, Config

**Daten-Repo**:
Der Ordner `daten/` mit allen persönlichen Daten als eigenes Git-Repo, lokal oder mit privatem Remote; getrennt vom System.
_Avoid_: Datenbank, Profil-Repo

**Kategorie**:
Die Gruppe, unter der ein Skill bei „Kenntnisse“ erscheint (z. B. Programmiersprachen); jeder Nutzer legt seine eigenen an, `gesprochene-sprache` und `arbeitsweise` haben eine feste Bedeutung.
_Avoid_: Bereich, Rubrik
_Avoid_: Konfiguration, Config

**Entwurf**:
Ein angepasster Lebenslauf, den der Nutzer noch nicht freigegeben hat; wird erst mit der Freigabe zur Bewerbung.
_Avoid_: Draft, Zwischenstand

**Bewerbung**:
Ein tatsächlich versendeter Lebenslauf zusammen mit seiner Stellenausschreibung, Firma und Datum.
_Avoid_: Versand, Version, Application

**Anlage**:
Ein Nachweis-Dokument (Zeugnis, Urkunde), das einer Bewerbung beiliegt. Keine Stammdaten.
_Avoid_: Zertifikat-Datei, Attachment
