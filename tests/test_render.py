"""Tests für render.py mit den Beispieldaten und absichtlich kaputten Varianten davon.

Aufruf: .venv/Scripts/python -m unittest discover -s tests -v
"""

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import render  # noqa: E402

BEISPIEL = REPO / "beispiel"


class KaputteDaten(unittest.TestCase):
    """Jeder Test kopiert die Beispieldaten, macht genau eine Stelle kaputt und erwartet eine klare Meldung."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="render-test-"))
        shutil.copytree(BEISPIEL / "stammdaten", self.tmp / "stammdaten")
        shutil.copy(BEISPIEL / "einstellungen.yaml", self.tmp / "einstellungen.yaml")
        shutil.copytree(BEISPIEL / "standard" / "devops", self.tmp / "lebenslauf",
                        ignore=shutil.ignore_patterns("*.pdf", "*.html"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ersetze(self, datei: str, alt: str, neu: str):
        pfad = self.tmp / datei
        text = pfad.read_text(encoding="utf-8")
        self.assertIn(alt, text, f"Testvorlage passt nicht mehr zu {datei}")
        pfad.write_text(text.replace(alt, neu, 1), encoding="utf-8")

    def pruefen(self) -> tuple[int, str]:
        aus = io.StringIO()
        with contextlib.redirect_stdout(aus):
            code = render.main(["--daten", str(self.tmp), "--pruefen", str(self.tmp / "lebenslauf")])
        return code, aus.getvalue()

    def erwarte_fehler(self, meldung: str):
        code, aus = self.pruefen()
        self.assertEqual(code, 1, aus)
        self.assertIn(meldung, aus)

    def test_unbekannte_kategorie(self):
        self.ersetze("stammdaten/skills.yaml", "kategorie: programmiersprache", "kategorie: zauberei")
        self.erwarte_fehler("unbekannte Kategorie 'zauberei'")

    def test_feste_kategorie_fehlt(self):
        self.ersetze("stammdaten/kategorien.yaml", "  - {id: arbeitsweise, name: Arbeitsweise}\n", "")
        self.erwarte_fehler("die Kategorie 'arbeitsweise' fehlt")

    def test_beispiel_ist_gueltig(self):
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)

    def test_unbekannte_id_im_lebenslauf(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-pipelines}", "{quelle: taet-gibts-nicht}")
        self.erwarte_fehler("unbekannte ID 'taet-gibts-nicht'")

    def test_aussage_ohne_quelle(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-pipelines}", '"Frei erfundene Aussage"')
        self.erwarte_fehler("Aussage ohne Quelle")

    def test_aussage_nur_mit_text(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-pipelines}", '{text: "Ohne Quelle"}')
        self.erwarte_fehler("Aussage ohne Quelle")

    def test_umformulierung_nicht_gekennzeichnet(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-pipelines}",
                     '{quelle: taet-pipelines, text: "Pipelines gebaut"}')
        self.erwarte_fehler("Text weicht von den Stammdaten zu 'taet-pipelines' ab")

    def test_freigegebener_text_als_umformuliert_markiert(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-pipelines}",
                     '{quelle: taet-pipelines, text: "Entwicklung von **GitLab-CI/CD-Pipelines** bis zum produktiven Deployment", umformuliert: true}')
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertIn("Text zu 'taet-pipelines' ist inzwischen freigegeben", aus)

    def test_nur_fett_geaendert_ist_keine_umformulierung(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-pipelines}",
                     '{quelle: taet-pipelines, text: "Entwicklung von GitLab-**CI/CD**-Pipelines bis zum produktiven Deployment"}')
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)

    # Alle fett gesetzten Begriffe im Beispiel-Lebenslauf (Profil, Tätigkeiten, Projekte)
    FETT_BEISPIEL = '["CI/CD", "Kubernetes", "GitLab-CI/CD-Pipelines", "Terraform", "Prometheus und Grafana", ' \
                    '"Java", "Bash", "Python"]'

    def setze_fett(self, liste: str):
        self.ersetze("lebenslauf/lebenslauf.yaml", "schwerpunkt: devops\n", f"schwerpunkt: devops\nfett: {liste}\n")

    def test_fett_liste_passt(self):
        self.setze_fett(self.FETT_BEISPIEL.replace('"Kubernetes"', '"kubernetes"'))  # Groß-/Kleinschreibung egal
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertNotIn(".fett", aus)

    def test_fett_begriff_fehlt(self):
        self.setze_fett(self.FETT_BEISPIEL.replace('"Java"', '"Java", "Jira"'))
        self.erwarte_fehler("'Jira' steht in 'fett', ist aber nirgends fett")

    def test_fett_ohne_treffer(self):
        self.setze_fett(self.FETT_BEISPIEL.replace('"Terraform", ', ""))
        self.erwarte_fehler("'Terraform' ist fett (taet-terraform), steht aber nicht in 'fett'")

    def test_fett_doppelt_im_bereich(self):
        self.setze_fett(self.FETT_BEISPIEL)
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-pipelines}",
                     '{quelle: taet-pipelines, text: "Entwicklung von **GitLab-CI/CD-Pipelines** für **Kubernetes**", '
                     'umformuliert: true}')
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertIn("'Kubernetes' ist in der Berufserfahrung 2-mal fett", aus)

    def test_fett_in_erfahrung_und_projekten_je_einmal(self):
        self.setze_fett(self.FETT_BEISPIEL)
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: proj-deploy-tool}",
                     '{quelle: proj-deploy-tool, text: "Deployment-Werkzeug für **Kubernetes**", umformuliert: true}')
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertNotIn("2-mal fett", aus)

    def test_taetigkeit_beim_falschen_arbeitgeber(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: taet-migrationen}", "{quelle: taet-terraform}")
        self.erwarte_fehler("gehört nicht zum Arbeitgeber 'muster-systemhaus'")

    def test_falscher_typ_als_quelle(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "{quelle: proj-deploy-tool}", "{quelle: skill-bash}")
        self.erwarte_fehler("ID 'skill-bash' ist ein(e) skill, erwartet: projekt")

    def test_arbeitsweise_ohne_beleg(self):
        self.ersetze("lebenslauf/lebenslauf.yaml", "  - skill-scrum", "  - skill-scrum\n  - skill-teamfaehigkeit")
        self.erwarte_fehler("'skill-teamfaehigkeit' (Arbeitsweise) hat keinen Beleg")

    def test_pflichtfeld_fehlt(self):
        self.ersetze("stammdaten/berufserfahrung.yaml",
                     "            kernaussage: Mitarbeit in einem Scrum-Team\n", "")
        self.erwarte_fehler("Pflichtfeld 'kernaussage' fehlt")

    def test_unbekanntes_feld(self):
        self.ersetze("stammdaten/projekte.yaml", "    kontext: privat\n", "    kontext: privat\n    kontekst: privat\n", )
        self.erwarte_fehler("unbekanntes Feld 'kontekst'")

    def test_doppelte_id(self):
        self.ersetze("stammdaten/berufserfahrung.yaml", "- id: taet-terraform", "- id: taet-k8s-betrieb")
        self.erwarte_fehler("ID 'taet-k8s-betrieb': doppelt vergeben")

    def test_unbekannter_skill_verweis(self):
        self.ersetze("stammdaten/projekte.yaml", "skills: [skill-bash]", "skills: [skill-cobol]")
        self.erwarte_fehler("unbekannte ID 'skill-cobol'")

    def test_ungueltiges_datum(self):
        self.ersetze("stammdaten/berufserfahrung.yaml", 'von: "2018-04"', 'von: "04/2018"')
        self.erwarte_fehler("ungültiges Datum '04/2018'")

    def test_position_mit_anlage(self):
        # Eine Position darf auf ein Arbeitszeugnis verweisen; fehlt die Datei, gibt es nur eine Warnung.
        self.ersetze("stammdaten/berufserfahrung.yaml", '        bis: "2017-08"\n',
                     '        bis: "2017-08"\n        anlage: anlagen/gibts-nicht.pdf\n')
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertIn("Position 'muster-festanstellung': Anlage 'anlagen/gibts-nicht.pdf' nicht gefunden", aus)

    def test_kaputtes_yaml(self):
        self.ersetze("stammdaten/skills.yaml", "skills:", "skills: [")
        self.erwarte_fehler("kein gültiges YAML")

    # ---------------------------------------------------------------- Anschreiben

    BEWERBUNG = ('firma: Beispiel AG\nstelle: DevOps Engineer (m/w/d)\ndatum: "2026-03-05"\nschwerpunkt: devops\n'
                 'status: entwurf\nkennziffer: DO-42\nempfaenger:\n  ansprechperson: Frau Dr. Erika Beispiel\n'
                 '  strasse: Hauptstraße 5\n  plz: "54321"\n  ort: Beispielstadt\n  anrede: Sehr geehrte Frau Dr. Beispiel\n')

    def als_bewerbung(self):
        """Macht aus dem Standardanschreiben eine Bewerbung: bewerbung.yaml dazu, Platzhalter ersetzt."""
        (self.tmp / "lebenslauf" / "bewerbung.yaml").write_text(self.BEWERBUNG, encoding="utf-8")
        self.ersetze("lebenslauf/anschreiben.yaml", "als [Stelle] bei [Firma]", "als DevOps Engineer bei der Beispiel AG")

    def test_anschreiben_beispiel_ist_gueltig(self):
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertIn("(mit Anschreiben)", aus)
        self.assertNotIn("Wörter", aus)

    def test_anschreiben_ist_optional(self):
        (self.tmp / "stammdaten" / "anschreiben.yaml").unlink()
        (self.tmp / "lebenslauf" / "anschreiben.yaml").unlink()
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertNotIn("(mit Anschreiben)", aus)

    def test_anschreiben_absatz_ohne_herkunft(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "  - art: motivation\n    quellen: [baust-motivation-produkt]",
                     "  - art: motivation\n    text: Frei erfundene Begeisterung.")
        self.erwarte_fehler("Absatz ohne Herkunft")

    def test_anschreiben_hauptteil_braucht_quellen(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "quellen: [taet-monitoring, taet-lasttests, proj-deploy-tool]",
                     "herkunft: nutzer")
        self.erwarte_fehler("ein Absatz 'hauptteil' braucht mindestens eine Quelle")

    def test_anschreiben_unbekannte_quelle(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "taet-terraform]", "taet-gibts-nicht]")
        self.erwarte_fehler("unbekannte ID 'taet-gibts-nicht'")

    def test_anschreiben_falsche_art_als_quelle(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "[baust-motivation-produkt]", "[beispiel-technik]")
        self.erwarte_fehler("ID 'beispiel-technik' ist ein(e) arbeitgeber und kann keine Quelle eines Absatzes sein")

    def test_anschreiben_umformulierung_nicht_gekennzeichnet(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "    umformuliert: true\n", "")
        self.erwarte_fehler("Text weicht von den Stammdaten zu baust-einstieg-betrieb ab")

    def test_anschreiben_freigegebener_text_braucht_keine_kennzeichnung(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "  - art: schluss\n    quellen: [baust-schluss-gespraech]",
                     "  - art: schluss\n    quellen: [baust-schluss-gespraech]\n    text: >-\n      Ich freue mich "
                     "darauf, Sie in einem persönlichen Gespräch davon zu überzeugen, dass ich gut zu Ihrem Team passe.")
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)

    def test_anschreiben_ohne_text_nur_mit_einer_quelle(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "    quellen: [baust-schluss-gespraech]",
                     "    quellen: [baust-schluss-gespraech, taet-pipelines]")
        self.erwarte_fehler("Absatz ohne 'text' – geht nur mit genau einer Quelle")

    def test_anschreiben_kein_fett(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "auf Kubernetes und", "auf **Kubernetes** und")
        self.erwarte_fehler("im Anschreiben gibt es kein Fett")

    def test_anschreiben_baustein_hauptteil_gibt_es_nicht(self):
        self.ersetze("stammdaten/anschreiben.yaml", "art: motivation", "art: hauptteil")
        self.erwarte_fehler("'hauptteil' ist nicht erlaubt")

    def test_anschreiben_baustein_falsche_art(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "  - art: schluss\n    quellen: [baust-schluss-gespraech]",
                     "  - art: einstieg\n    quellen: [baust-schluss-gespraech]")
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertIn("Baustein 'baust-schluss-gespraech' ist für 'schluss' gedacht", aus)

    def test_anschreiben_rahmen_braucht_text(self):
        self.ersetze("lebenslauf/anschreiben.yaml", "  - art: schluss\n",
                     "  - art: rahmen\n    quellen: [rahmen]\n  - art: schluss\n")
        self.erwarte_fehler("Absatz ohne 'text' – geht nur mit genau einer Quelle")

    def test_anschreiben_zu_kurz(self):
        (self.tmp / "lebenslauf" / "anschreiben.yaml").write_text(
            "absaetze:\n  - {art: hauptteil, quellen: [taet-pipelines]}\n  - {art: schluss, quellen: [baust-schluss-gespraech]}\n",
            encoding="utf-8")
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        self.assertIn("Wörter im Brieftext – Ziel sind etwa 250–350", aus)

    def test_anschreiben_unterschrift_fehlt(self):
        self.ersetze("stammdaten/person.yaml", "unterschrift: unterschrift.svg", "unterschrift: gibts-nicht.png")
        self.erwarte_fehler("Unterschrift 'gibts-nicht.png' nicht gefunden")

    def test_anschreiben_platzhalter_in_bewerbung(self):
        (self.tmp / "lebenslauf" / "bewerbung.yaml").write_text(self.BEWERBUNG, encoding="utf-8")
        self.erwarte_fehler("Platzhalter [Stelle] ist noch nicht ersetzt")

    def test_anschreiben_bewerbung_unbekanntes_feld(self):
        self.als_bewerbung()
        (self.tmp / "lebenslauf" / "bewerbung.yaml").write_text(self.BEWERBUNG + "gehalt: viel\n", encoding="utf-8")
        self.erwarte_fehler("unbekanntes Feld 'gehalt'")

    def test_anschreiben_kontext(self):
        self.als_bewerbung()
        code, aus = self.pruefen()
        self.assertEqual(code, 0, aus)
        b = render.Befunde()
        sd = render.lade_stammdaten(self.tmp / "stammdaten", b)
        ordner = self.tmp / "lebenslauf"
        ab = render.pruefe_anschreiben(sd, ordner, b)
        ll = render.pruefe_lebenslauf(sd, ordner, b)
        k = render.baue_anschreiben_kontext(sd, ll, ab["anschreiben"], ab["bewerbung"], render.date(2030, 1, 1))
        self.assertEqual(k["betreff"], "Bewerbung als DevOps Engineer")   # ohne (m/w/d)
        self.assertEqual(k["kennziffer"], "DO-42")
        self.assertEqual(k["anrede"], "Sehr geehrte Frau Dr. Beispiel,")
        self.assertEqual(k["ort_datum"], "Musterstadt, 5. März 2026")      # Datum aus bewerbung.yaml
        self.assertEqual(k["empfaenger"], ["Beispiel AG", "Frau Dr. Erika Beispiel", "Hauptstraße 5", "54321 Beispielstadt"])
        self.assertEqual(k["person"]["adresse"], ["Musterweg 1", "12345 Musterstadt"])
        self.assertEqual(k["ruecksende"], "Max Mustermann · Musterweg 1 · 12345 Musterstadt")
        self.assertTrue(k["unterschrift"])
        self.assertEqual(k["absaetze"][-1]["text"], sd.obj("baust-schluss-gespraech")["text"])
        # Platzhalter-Datum im Entwurf: heute
        ab["bewerbung"]["datum"] = "<JJJJ-MM-TT>"
        k = render.baue_anschreiben_kontext(sd, ll, ab["anschreiben"], ab["bewerbung"], render.date(2030, 1, 1))
        self.assertEqual(k["ort_datum"], "Musterstadt, 1. Januar 2030")
        # Standardanschreiben (ohne bewerbung.yaml): Platzhalter
        k = render.baue_anschreiben_kontext(sd, ll, ab["anschreiben"], None, render.date(2030, 1, 1))
        self.assertEqual((k["betreff"], k["empfaenger"]), ("Bewerbung als [Stelle]", ["[Firma]"]))


@unittest.skipUnless(any(k and Path(k).exists() for k in render.CHROME_KANDIDATEN), "kein Chrome/Edge gefunden")
class Kontext(unittest.TestCase):

    def test_abschluesse_neueste_zuerst(self):
        b = render.Befunde()
        sd = render.lade_stammdaten(BEISPIEL / "stammdaten", b)
        ll = render.pruefe_lebenslauf(sd, BEISPIEL / "standard" / "devops", b)
        kontext = render.baue_kontext(sd, ll)
        # laufende zuerst, dann nach Enddatum absteigend, unabhängig von der Reihenfolge in ausbildung.yaml
        self.assertEqual([a["quelle"] for a in kontext["abschluesse"]],
                         ["abschluss-msc", "abschluss-zertifikat-cloud", "abschluss-bsc", "abschluss-fiae"])


class Rendern(unittest.TestCase):

    def test_beispiel_pdf(self):
        with tempfile.TemporaryDirectory(prefix="render-test-") as tmp:
            ordner = Path(tmp) / "lebenslauf"
            shutil.copytree(BEISPIEL / "standard" / "devops", ordner, ignore=shutil.ignore_patterns("*.pdf", "*.html"))
            for schalter in ("zusammengefasst", "einzeln"):
                yaml_pfad = ordner / "lebenslauf.yaml"
                yaml_pfad.write_text(yaml_pfad.read_text(encoding="utf-8")
                                     .replace("positionen: zusammengefasst", f"positionen: {schalter}"),
                                     encoding="utf-8")
                aus = io.StringIO()
                with contextlib.redirect_stdout(aus):
                    code = render.main(["--daten", str(BEISPIEL), "--html", str(ordner)])
                self.assertEqual(code, 0, aus.getvalue())
                pdf = render.PdfReader(ordner / "lebenslauf.pdf")
                self.assertLessEqual(len(pdf.pages), render.MAX_SEITEN)
                text = " ".join(p.extract_text() for p in pdf.pages)
                self.assertIn("Max Mustermann", text)
                self.assertIn("Beispiel Technik GmbH", text)
                html = (ordner / "lebenslauf.html").read_text(encoding="utf-8")
                self.assertIn('data-quelle="taet-monitoring" data-umformuliert="ja"', html)
                self.assertNotIn("data-quelle", text)
                if schalter == "einzeln":
                    self.assertIn("Werkstudent Softwareentwicklung", text)

    def test_anschreiben_pdf(self):
        with tempfile.TemporaryDirectory(prefix="render-test-") as tmp:
            ordner = Path(tmp) / "bewerbung"
            shutil.copytree(BEISPIEL / "standard" / "devops", ordner, ignore=shutil.ignore_patterns("*.pdf", "*.html"))
            (ordner / "bewerbung.yaml").write_text(KaputteDaten.BEWERBUNG, encoding="utf-8")
            pfad = ordner / "anschreiben.yaml"
            pfad.write_text(pfad.read_text(encoding="utf-8").replace("als [Stelle] bei [Firma]", "bei der Beispiel AG"),
                            encoding="utf-8")
            aus = io.StringIO()
            with contextlib.redirect_stdout(aus):
                code = render.main(["--daten", str(BEISPIEL), "--html", "--nur-anschreiben", str(ordner)])
            self.assertEqual(code, 0, aus.getvalue())
            self.assertFalse((ordner / "lebenslauf.pdf").exists(), "--nur-anschreiben darf den Lebenslauf nicht rendern")
            pdf = render.PdfReader(ordner / "anschreiben.pdf")
            self.assertEqual(len(pdf.pages), 1)
            text = pdf.pages[0].extract_text()
            for erwartet in ("Max Mustermann", "Beispiel AG", "54321 Beispielstadt", "Bewerbung als DevOps Engineer",
                             "Kennziffer: DO-42", "Musterstadt, 5. März 2026", "Sehr geehrte Frau Dr. Beispiel,",
                             "Mit freundlichen Grüßen"):
                self.assertIn(erwartet, text)
            self.assertNotIn("(m/w/d)", text)
            self.assertNotIn("data-quelle", text)
            html = (ordner / "anschreiben.html").read_text(encoding="utf-8")
            self.assertIn('data-quelle="taet-k8s-betrieb taet-pipelines taet-terraform" data-umformuliert="ja"', html)
            self.assertIn('data-herkunft="anzeige"', html)
            self.assertIn('alt="Unterschrift"', html)


class Templates(unittest.TestCase):
    """Arbeitet auf einer Kopie von templates/ und einstellungen.yaml, damit kaputte Varianten das Repo nicht berühren."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="render-test-"))
        shutil.copytree(REPO / "templates", self.tmp / "system" / "templates")
        shutil.copytree(BEISPIEL / "stammdaten", self.tmp / "stammdaten")
        shutil.copytree(BEISPIEL / "standard" / "devops", self.tmp / "lebenslauf",
                        ignore=shutil.ignore_patterns("*.pdf", "*.html"))
        self.schreibe("einstellungen.yaml", "template: klassisch\n")
        self.alt = {k: getattr(render, k) for k in
                    ("TEMPLATE_ORDNER", "GRUNDLAYOUT_ORDNER", "SCHRIFTEN_ORDNER", "DATEN")}
        self.sys = self.tmp / "system" / "templates"
        render.TEMPLATE_ORDNER = self.sys
        render.GRUNDLAYOUT_ORDNER = self.sys / "grundlayouts"
        render.SCHRIFTEN_ORDNER = self.sys / "schriften"

    def tearDown(self):
        for k, v in self.alt.items():
            setattr(render, k, v)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def schreibe(self, datei: str, text: str):
        if datei == "einstellungen.yaml":
            text = f"schemaversion: {render.SCHEMAVERSION}\n" + text
        (self.tmp / datei).write_text(text, encoding="utf-8")

    def variante(self, name: str, ersetzungen: dict[str, str]):
        text = (self.sys / "klassisch.yaml").read_text(encoding="utf-8")
        for alt, neu in ersetzungen.items():
            self.assertIn(alt, text)
            text = text.replace(alt, neu)
        self.schreibe(f"system/templates/{name}.yaml", text)

    def lauf(self, *argumente) -> tuple[int, str]:
        aus = io.StringIO()
        with contextlib.redirect_stdout(aus):
            code = render.main(["--daten", str(self.tmp), *argumente, str(self.tmp / "lebenslauf")])
        return code, aus.getvalue()

    def erwarte_fehler(self, meldung: str):
        code, aus = self.lauf("--pruefen")
        self.assertEqual(code, 1, aus)
        self.assertIn(meldung, aus)

    def test_klassisch_ist_gueltig(self):
        code, aus = self.lauf("--pruefen")
        self.assertEqual(code, 0, aus)

    def test_unbekanntes_template_im_lebenslauf(self):
        self.ersetze_lebenslauf("schwerpunkt:", "template: gibtsnicht\nschwerpunkt:")
        self.erwarte_fehler("unbekanntes Template 'gibtsnicht'")

    def test_unbekanntes_template_in_einstellungen(self):
        self.schreibe("einstellungen.yaml", "template: gibtsnicht\n")
        self.erwarte_fehler("einstellungen.yaml.template: unbekanntes Template 'gibtsnicht'")

    def test_veraltetes_template_warnt(self):
        self.variante("alt", {"reihenfolge:": "veraltet: true\nreihenfolge:"})
        self.ersetze_lebenslauf("schwerpunkt:", "template: alt\nschwerpunkt:")
        code, aus = self.lauf("--pruefen")
        self.assertEqual(code, 0, aus)
        self.assertIn("Template 'alt' ist als veraltet markiert", aus)

    def test_unbekanntes_grundlayout(self):
        self.variante("x", {"grundlayout: klassisch": "grundlayout: gibtsnicht"})
        self.erwarte_fehler("unbekanntes Grundlayout 'gibtsnicht'")

    def test_ungueltige_farbe(self):
        self.variante("x", {'farbe: "#1f4e79"': "farbe: blau"})
        self.erwarte_fehler("ungültige Farbe 'blau'")

    def test_reihenfolge_unvollstaendig(self):
        self.variante("x", {"kenntnisse, projekte]": "kenntnisse]"})
        self.erwarte_fehler("muss jeden Abschnitt genau einmal nennen")

    def test_unbekannte_schrift(self):
        self.variante("x", {"schrift: source-sans-3": "schrift: comic"})
        self.erwarte_fehler("unbekannte Schrift 'comic'")

    def test_schrift_ohne_lizenz_und_datei(self):
        pfad = self.sys / "schriften" / "schriften.yaml"
        pfad.write_text(pfad.read_text(encoding="utf-8") + "  - id: frei\n    name: Frei\n    stack: Frei, sans-serif\n"
                        "    dateien:\n      - {datei: frei.woff2, gewicht: 400, stil: normal}\n", encoding="utf-8")
        self.erwarte_fehler("braucht 'lizenz'")
        self.erwarte_fehler("Datei 'frei.woff2' fehlt")

    def test_eigenes_template_aus_daten(self):
        (self.tmp / "templates").mkdir()
        text = (self.sys / "klassisch.yaml").read_text(encoding="utf-8").replace('"#1f4e79"', '"#2d5016"')
        (self.tmp / "templates" / "gruen.yaml").write_text(text, encoding="utf-8")
        self.schreibe("einstellungen.yaml", "template: gruen\n")
        code, aus = self.lauf("--pruefen")
        self.assertEqual(code, 0, aus)

    def test_eigenes_template_mit_vergebenem_namen(self):
        (self.tmp / "templates").mkdir()
        shutil.copy(self.sys / "kopfband.yaml", self.tmp / "templates" / "kopfband.yaml")
        self.erwarte_fehler("Template-Name 'kopfband' gibt es schon")

    def test_aufhellen(self):
        self.assertEqual(render.aufhellen("#000000", 0.5), "#808080")
        self.assertEqual(render.aufhellen("#1f4e79", 0), "#1f4e79")

    def test_kontrast(self):
        self.assertAlmostEqual(render.kontrast("#000000", "#ffffff"), 21, places=1)
        self.assertAlmostEqual(render.kontrast("#ffffff", "#ffffff"), 1, places=1)

    def test_kopfband_zu_helle_farbe(self):
        pfad = self.sys / "kopfband.yaml"
        pfad.write_text(pfad.read_text(encoding="utf-8").replace('"#22344f"', '"#9fc5e8"'), encoding="utf-8")
        self.erwarte_fehler("ist zu hell für weißen Text")

    def test_fotoposition_nicht_erlaubt(self):
        pfad = self.sys / "grundlayouts" / "klassisch.yaml"
        pfad.write_text(pfad.read_text(encoding="utf-8").replace("[rechts, links]", "[rechts]"), encoding="utf-8")
        self.variante("x", {"position: rechts": "position: links"})
        self.erwarte_fehler("'links' ist bei Grundlayout 'klassisch' nicht möglich")

    def test_grundlayout_ohne_anschreiben_gegenstueck(self):
        (self.sys / "grundlayouts" / "kopfband.anschreiben.html.j2").unlink()
        self.erwarte_fehler("Grundlayout-Datei kopfband.anschreiben.html.j2 fehlt")

    def test_grundlayout_spalten_unvollstaendig(self):
        pfad = self.sys / "grundlayouts" / "zwei-spalten.yaml"
        pfad.write_text(pfad.read_text(encoding="utf-8").replace("seite: [kenntnisse]", "seite: [projekte]"),
                        encoding="utf-8")
        self.erwarte_fehler("jeder Abschnitt muss genau einmal vorkommen")

    def test_spaltenpruefung(self):
        def ausgabe(hoehen):
            aus = io.StringIO()
            with contextlib.redirect_stdout(aus):
                render.pruefe_spalten(hoehen)
            return aus.getvalue()
        self.assertEqual(ausgabe({}), "")
        self.assertNotIn("Spalte 'seite'", ausgabe({"haupt": 200, "seite": 150}))
        self.assertIn("HINWEIS  Spalte 'seite' ist 50 mm länger", ausgabe({"haupt": 100, "seite": 150}))
        self.assertIn("WARNUNG  Spalte 'seite' ist 20 mm länger als die Hauptspalte und braucht eine Seite mehr",
                      ausgabe({"haupt": 270, "seite": 290}))

    @unittest.skipUnless(any(k and Path(k).exists() for k in render.CHROME_KANDIDATEN), "kein Chrome/Edge gefunden")
    def test_grundlayouts_rendern_mit_lesereihenfolge(self):
        """Jedes mitgelieferte Template rendert; der Name steht im Text vorn, die Berufserfahrung vor den Kenntnissen."""
        for name in ("klassisch", "zwei-spalten", "kopfband"):
            with self.subTest(template=name):
                pfad = self.tmp / "lebenslauf" / "lebenslauf.yaml"
                text = pfad.read_text(encoding="utf-8")
                text = "\n".join(z for z in text.splitlines() if not z.startswith("template:"))
                pfad.write_text(f"template: {name}\n{text}\n", encoding="utf-8")
                code, aus = self.lauf()
                self.assertEqual(code, 0, aus)
                text = " ".join(p.extract_text() for p in render.PdfReader(self.tmp / "lebenslauf" / "lebenslauf.pdf").pages)
                self.assertTrue(text.lstrip().startswith("Max Mustermann"), text[:80])
                self.assertLess(text.index("Beispiel Technik GmbH"), text.index("Programmiersprachen"))
                if name == "zwei-spalten":
                    self.assertIn("SPALTEN  haupt", aus)
                # Das Anschreiben im selben Ordner nimmt dasselbe Template: 1 Seite, Name vorn
                self.assertIn(f"ANSCHREIBEN {name} (Grundlayout {name})", aus)
                pdf = render.PdfReader(self.tmp / "lebenslauf" / "anschreiben.pdf")
                self.assertEqual(len(pdf.pages), 1)
                self.assertTrue(pdf.pages[0].extract_text().lstrip().startswith("Max Mustermann"))

    @unittest.skipUnless(any(k and Path(k).exists() for k in render.CHROME_KANDIDATEN), "kein Chrome/Edge gefunden")
    def test_parameter_wirken(self):
        self.variante("bunt", {'"#1f4e79"': '"#8a1538"', 'linienfarbe: "#c9d3de"\n': "", "form: eckig": "form: rund",
                               "position: rechts": "position: links", "ueberschriften: linie": "ueberschriften: balken",
                               "[berufserfahrung, ausbildung, kenntnisse, projekte]":
                                   "[projekte, berufserfahrung, ausbildung, kenntnisse]"})
        self.ersetze_lebenslauf("schwerpunkt:", "template: bunt\nschwerpunkt:")
        code, aus = self.lauf("--html")
        self.assertEqual(code, 0, aus)
        self.assertIn("TEMPLATE bunt (Grundlayout klassisch)", aus)
        html = (self.tmp / "lebenslauf" / "lebenslauf.html").read_text(encoding="utf-8")
        self.assertIn("--acc: #8a1538; --line: #e2c4cd;", html)
        self.assertIn("border-radius: 50%; object-position: 50% 15%", html)
        self.assertIn("flex-direction: row-reverse", html)
        self.assertIn("border-left: 2.5pt solid", html)
        self.assertLess(html.index("<h2>Projekte</h2>"), html.index("<h2>Berufserfahrung</h2>"))
        self.assertIn('font-family: "Source Sans 3"', html)
        self.assertIn("@font-face", html)

    @unittest.skipUnless(any(k and Path(k).exists() for k in render.CHROME_KANDIDATEN), "kein Chrome/Edge gefunden")
    def test_vorschau_aendert_den_lebenslauf_nicht(self):
        alt_vorschau = render.VORSCHAU
        render.VORSCHAU = self.tmp / "vorschau"
        try:
            yaml_vorher = (self.tmp / "lebenslauf" / "lebenslauf.yaml").read_text(encoding="utf-8")
            code, aus = self.lauf("--vorschau", "kopfband")
            self.assertEqual(code, 0, aus)
            self.assertIn("TEMPLATE kopfband", aus)
            self.assertIn("1 Seite, in Ordnung", aus)
            self.assertTrue((self.tmp / "vorschau" / "lebenslauf" / "lebenslauf.pdf").exists())
            self.assertFalse((self.tmp / "lebenslauf" / "lebenslauf.pdf").exists())
            self.assertEqual(yaml_vorher, (self.tmp / "lebenslauf" / "lebenslauf.yaml").read_text(encoding="utf-8"))
            code, aus = self.lauf("--vorschau", "gibtsnicht")
            self.assertEqual(code, 1, aus)
        finally:
            render.VORSCHAU = alt_vorschau

    def ersetze_lebenslauf(self, alt: str, neu: str):
        pfad = self.tmp / "lebenslauf" / "lebenslauf.yaml"
        text = pfad.read_text(encoding="utf-8")
        self.assertIn(alt, text)
        pfad.write_text(text.replace(alt, neu, 1), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
