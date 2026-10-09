"""Fragenkatalog des Datenschutz-Assistenten (wizard-2026.10.3) erzeugen.

Aufbau nach dem Muster des Checklistendesigners (audit_designer, v05-Baum):
nummerierte Fragen, Entscheidungsfragen mit JA-/NEIN-Zweig, Hinweise als
Aufzählung mit vorangestellter Fundstelle; reine Eingaben enden mit Doppelpunkt.

Jede Frage nennt die zuständige Stelle (``ROLE``): Fachbereich, IT-Betrieb oder
Recht/Datenschutz. Tatsachen werden vor ihrer rechtlichen Einordnung erfragt.
HDSIG-Fundstellen sind am Gesetzeswortlaut geprüft; Auslegungshinweise stützen
sich auf die in ``GUIDANCE`` genannten Veröffentlichungen von EDSA, DSK und HBDI.

    python tools/build_wizard_catalog.py
"""

from __future__ import annotations

import json
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[1]
    / "src/auditcore_dataprotection/catalogs/wizard-2026.10.3.json"
)

YN = "ja_nein_unklar"
TEXT = "text"
CHOICE = "auswahl"
IMPL = "umsetzung"
NUMBER = "zahl"
TABLE = "tabelle"
DATE = "datum"


def q(number, text, kind=TEXT, target="", reference="", hints=(), *, required=True,
      parent=None, when=None, choices=(), justify=(), columns=(), context=None,
      task_if=()):  # fmt: skip
    """Ein Knoten des Baums; ``parent``/``when`` bilden den JA-/NEIN-Zweig."""
    item = {
        "id": number,
        "number": number,
        "text": text,
        "kind": kind,
        "target": target,
        "reference": reference,
        "hints": list(hints),
        "help": " ".join(hints),
        "required": required,
        "na_allowed": False,
        "justify_values": list(justify),
    }
    if choices:
        item["choices"] = [{"key": k, "title": t} for k, t in choices]
    if columns:
        item["columns"] = [
            {"key": c[0], "title": c[1], "required": c[2], "choices": list(c[3:] and c[3])}
            for c in columns
        ]
    if task_if:
        item["task_if"] = list(task_if)
    if parent:
        item["show_if"] = {"question": parent, "in": list(when or ["ja"])}
    if context:
        item["show_if"] = {"context": context[0], "in": list(context[1])}
    return item


STEPS = [
    {
        "id": "W01",
        "title": "1 Gegenstand der Verarbeitung",
        "goal": "Erfasst wird die tatsächliche Verarbeitung, nicht die Software.",
        "questions": [
            q(
                "1.1",
                "Bezeichnung der Verarbeitungstätigkeit:",
                target="register:name",
                reference="Art. 30 Abs. 1 Satz 2 DSGVO; § 65 Abs. 1 HDSIG",
                hints=[
                    "Die Bezeichnung beschreibt die fachliche Tätigkeit, nicht die eingesetzte "
                    "Anwendung (z. B. „Verfolgung von Ordnungswidrigkeiten nach Gesetz X“, nicht "
                    "„Fachverfahren Y“).",
                    "Unterstützt eine Anwendung mehrere Tätigkeiten, ist jede Tätigkeit gesondert "
                    "zu erfassen.",
                ],
            ),
            q(
                "1.2",
                "Beschreibung des fachlichen Ablaufs:",
                target="register:beschreibung",
                hints=[
                    "Kurz in der Reihenfolge der Arbeitsschritte beschreiben: Eingang, "
                    "Bearbeitung, Entscheidung, Abschluss."
                ],
            ),
            q(
                "1.3",
                "Arbeitsschritte, die ausdrücklich nicht zu dieser Tätigkeit gehören:",
                target="register:abgrenzung",
                required=False,
                hints=[
                    "Die Abgrenzung verhindert, dass verschiedene Zwecke vermischt werden "
                    "(z. B. allgemeine Marktbeobachtung und konkrete Verfolgung im Einzelfall)."
                ],
            ),
            q(
                "1.4",
                "Anwendungen, Schnittstellen und manuelle Arbeitsschritte, die die Tätigkeit "
                "unterstützen:",
                target="register:anwendungen",
                hints=["Auch E-Mail, Tabellenkalkulationen und Papierakten angeben."],
            ),
            q(
                "1.5",
                "Für welche Umgebung wird die Verarbeitung beurteilt?",
                CHOICE,
                "register:umgebung",
                choices=[
                    ("entwicklung", "Entwicklung"),
                    ("test", "Test"),
                    ("produktion", "Produktion"),
                ],
                hints=[
                    "Eine Beurteilung der Test- oder Entwicklungsumgebung gilt nicht "
                    "automatisch für den Produktivbetrieb."
                ],
            ),
            q(
                "1.6",
                "Ist die Tätigkeit bereits im zentralen Verzeichnis der Dienststelle "
                "(Hausverzeichnis) erfasst?",
                YN,
                "register:im_hausverzeichnis",
                hints=["Die Frage dient der Vermeidung von Doppelerfassungen."],
            ),
            q(
                "1.6.1",
                "Kennung des Eintrags im Hausverzeichnis:",
                target="register:hausverzeichnis_referenz",
                parent="1.6",
            ),
            q(
                "1.7",
                "Werden personenbezogene Daten verarbeitet – einschließlich Benutzerkonten, "
                "Protokoll- und Supportdaten?",
                YN,
                "register:personenbezug",
                reference="Art. 4 Nr. 1 und 2 DSGVO",
                justify=["nein"],
                hints=[
                    "Personenbezug setzt keine Namensangabe voraus; es genügt, dass eine Person "
                    "bestimmbar ist.",
                    "Auch bei synthetischen Fachdaten enthalten Benutzerkonten und "
                    "Zugriffsprotokolle regelmäßig Daten der Beschäftigten.",
                    "Die Antwort „Nein“ ist zu begründen.",
                ],
            ),
        ],
    },
    {
        "id": "W02",
        "title": "2 Zwecke, Zuständigkeit und Rechtsgrundlagen",
        "goal": "Ohne geklärtes Rechtsregime und tragfähige Befugnis gibt es keinen positiven "
        "Abschluss; ein Entwurf bleibt speicherbar.",
        "questions": [
            q(
                "2.1",
                "Zweck bzw. Zwecke der Verarbeitung:",
                target="register:zweck",
                reference="Art. 5 Abs. 1 lit. b, Art. 30 Abs. 1 Satz 2 lit. b DSGVO; "
                "§ 65 Abs. 1 HDSIG",
                hints=[
                    "Zwecke konkret und je Verarbeitungsschritt angeben.",
                    "Allgemeine Angaben wie „Verwaltung“ oder „Digitalisierung“ genügen nicht.",
                ],
            ),
            q(
                "2.2",
                "Vorschrift, die der Dienststelle die Aufgabe und Zuständigkeit zuweist:",
                target="register:zustaendigkeitsnorm",
                hints=[
                    "Norm mit Fundstelle angeben; die Prüfung obliegt der fachlich zuständigen "
                    "Stelle."
                ],
            ),
            q(
                "2.3",
                "Rechtsgrundlage für die Erhebung, Speicherung und Nutzung der Daten:",
                target="register:ermaechtigungsgrundlage",
                reference="Art. 6 Abs. 1 und 3 DSGVO; im Dritten Teil HDSIG die "
                "fachgesetzliche Befugnis",
                hints=[
                    "Das Verzeichnis schafft selbst keine Befugnis zur Verarbeitung.",
                    "Übermittlungen werden gesondert unter 5.4 erfasst.",
                ],
            ),
            q(
                "2.4",
                "Welches Datenschutzrecht ist auf diese Tätigkeit anzuwenden?",
                CHOICE,
                "register:rechtsregime",
                reference="§ 40 HDSIG (Anwendungsbereich des Dritten Teils)",
                choices=[
                    ("dsgvo", "DSGVO (ergänzt durch den Zweiten Teil HDSIG)"),
                    ("hdsig_ji", "Dritter Teil HDSIG (Richtlinie (EU) 2016/680)"),
                    ("unklar", "Unklar – Prüfung erforderlich"),
                ],
                hints=[
                    "Die Einordnung erfolgt je Tätigkeit, nicht pauschal je Anwendung.",
                    "Der Dritte Teil HDSIG gilt für die Verhütung, Ermittlung, Aufdeckung, "
                    "Verfolgung oder Ahndung von Straftaten und Ordnungswidrigkeiten.",
                    "„Unklar“ erzeugt eine Prüfaufgabe; ein bestätigter Abschluss ist bis zur "
                    "Klärung nicht möglich.",
                ],
            ),
            q("2.5", "Begründung der Einordnung:", target="register:rechtsregime_begruendung"),
            q(
                "2.6",
                "Werden die Daten zusätzlich für weitere Zwecke verarbeitet (z. B. Statistik, "
                "Berichterstattung, allgemeine Aufsicht)?",
                YN,
                "register:weitere_zwecke",
                reference="Art. 5 Abs. 1 lit. b, Art. 6 Abs. 4 DSGVO",
            ),
            q(
                "2.6.1",
                "Weitere Zwecke:",
                target="register:weitere_zwecke_beschreibung",
                parent="2.6",
            ),
            q(
                "2.6.2",
                "Begründung, warum die weiteren Zwecke mit dem ursprünglichen Zweck vereinbar "
                "sind:",
                target="register:weitere_zwecke_vereinbarkeit",
                parent="2.6",
                reference="Art. 6 Abs. 4 DSGVO; § 44 HDSIG",
                hints=[
                    "Ist ein weiterer Zweck nicht vereinbar, ist er als eigene Tätigkeit zu "
                    "erfassen."
                ],
            ),
            q(
                "2.7",
                "Lässt sich der Zweck mit weniger Daten, weniger Zugriffen oder einem "
                "milderen Verfahren erreichen? Begründung:",
                target="register:erforderlichkeit",
                reference="Art. 5 Abs. 1 lit. c, Art. 25 Abs. 2 DSGVO",
                hints=["Geprüfte Alternativen und die Gründe ihrer Ablehnung angeben."],
            ),
        ],
    },
    {
        "id": "W03",
        "title": "3 Verantwortlichkeiten und Beteiligte",
        "goal": "Die oder der Datenschutzbeauftragte berät und überwacht; sie oder er ist nicht "
        "Betreiber und nicht alleinige Freigabestelle.",
        "questions": [
            q(
                "3.1",
                "In welcher Rolle handelt die Dienststelle bei dieser Tätigkeit?",
                CHOICE,
                "register:rolle",
                reference="Art. 4 Nr. 7 und 8, Art. 26, Art. 28 DSGVO",
                choices=[
                    ("verantwortlicher", "Verantwortlicher"),
                    ("auftragsverarbeiter", "Auftragsverarbeiter"),
                ],
                hints=[
                    "Die Rolle bestimmt die Vorlage des Verzeichnisses (Art. 30 Abs. 1 oder "
                    "Abs. 2 DSGVO, § 65 Abs. 1 oder 2 HDSIG).",
                    "Eine gemeinsame Verantwortlichkeit mit anderen Stellen wird unter 3.1.3 "
                    "erfasst; die Dienststelle bleibt dabei Verantwortlicher.",
                ],
            ),
            q(
                "3.1.1",
                "Verantwortlicher, in dessen Auftrag verarbeitet wird:",
                target="register:auftraggeber",
                parent="3.1",
                when=["auftragsverarbeiter"],
                reference="Art. 30 Abs. 2 lit. a DSGVO; § 65 Abs. 2 HDSIG",
            ),
            q(
                "3.1.2",
                "Kategorien von Verarbeitungen, die im Auftrag durchgeführt werden:",
                target="register:kategorien_verarbeitungen",
                parent="3.1",
                when=["auftragsverarbeiter"],
                reference="Art. 30 Abs. 2 lit. b DSGVO; § 65 Abs. 2 HDSIG",
            ),
            q(
                "3.1.3",
                "Legt die Dienststelle die Zwecke und Mittel der Verarbeitung gemeinsam mit "
                "einer anderen Stelle fest?",
                YN,
                "register:gemeinsame_verantwortlichkeit",
                parent="3.1",
                when=["verantwortlicher"],
                reference="Art. 26 DSGVO",
            ),
            q(
                "3.1.3.1",
                "Gemeinsam Verantwortliche:",
                target="register:gemeinsame_verantwortliche",
                parent="3.1.3",
                hints=[
                    "Die Vereinbarung nach Art. 26 Abs. 1 Satz 2 DSGVO ist als Nachweis zu "
                    "hinterlegen."
                ],
            ),
            q(
                "3.2",
                "Verantwortliche Stelle (Name und Kontaktdaten):",
                target="register:verantwortliche_stelle",
                reference="Art. 30 Abs. 1 Satz 2 lit. a DSGVO; § 65 Abs. 1 HDSIG",
                hints=[
                    "Verantwortlich ist die Dienststelle, nicht die entwickelnde Person oder "
                    "das bearbeitende Referat."
                ],
            ),
            q(
                "3.3",
                "Fachlich verantwortliche Funktion:",
                target="register:ansprechperson",
                hints=["Funktion angeben, keine Privatperson."],
            ),
            q(
                "3.4",
                "Vertretung der fachlich verantwortlichen Funktion:",
                target="register:vertretung",
            ),
            q(
                "3.5",
                "Stellen, die die Anwendung betreiben, administrieren und warten:",
                target="register:betrieb",
                hints=["Interne und externe Stellen sowie ihre Zuständigkeitsgrenzen angeben."],
            ),
            q(
                "3.6",
                "Wurde die oder der Datenschutzbeauftragte bereits eingebunden?",
                YN,
                "register:dsb_eingebunden",
                reference="Art. 38 Abs. 1 DSGVO; § 7 HDSIG",
                hints=[
                    "Die Einbindung soll frühzeitig erfolgen, nicht erst kurz vor Betriebsbeginn."
                ],
            ),
            q(
                "3.6.1",
                "Datum der Einbindung und zuständige Kontaktstelle:",
                target="register:dsb_beteiligung",
                parent="3.6",
            ),
            q(
                "3.7",
                "Werden externe Dienstleister eingesetzt, die Zugang zu den Daten haben oder "
                "haben können (z. B. Hosting, Wartung, Fernwartung, Support, Druck, "
                "Aktenvernichtung)?",
                YN,
                "register:auftragsverarbeitung",
                hints=[
                    "Es zählt auch die bloße Möglichkeit des Zugriffs, etwa bei Fernwartung.",
                    "Die rechtliche Einordnung der Dienstleister folgt unter 3.7.2.",
                ],
            ),
            q(
                "3.7.1",
                "Dienstleister und ihre Leistungen:",
                TABLE,
                "register:dienstleister",
                parent="3.7",
                columns=[
                    ("dienstleister", "Dienstleister", True),
                    ("leistung", "Leistung", True),
                    ("daten", "Zugängliche Daten", False),
                    ("ort", "Ort der Leistungserbringung (Staat)", False),
                ],
                hints=["Je Dienstleister eine Zeile; Unterauftragnehmer gesondert angeben."],
            ),
            q(
                "3.7.2",
                "Rechtliche Einordnung der Dienstleister:",
                TABLE,
                "register:dienstleister_einordnung",
                parent="3.7",
                reference="Art. 4 Nr. 8, Art. 28 DSGVO; § 57 HDSIG",
                columns=[
                    ("dienstleister", "Dienstleister", True),
                    (
                        "einordnung",
                        "Einordnung",
                        True,
                        [
                            "Auftragsverarbeiter",
                            "eigenständig Verantwortlicher",
                            "gemeinsam Verantwortlicher",
                        ],
                    ),
                    (
                        "vertrag",
                        "Vertrag nach Art. 28 Abs. 3 DSGVO bzw. § 57 Abs. 5 HDSIG",
                        True,
                        ["liegt vor", "in Vorbereitung", "fehlt", "nicht erforderlich"],
                    ),
                ],
                hints=[
                    "Fehlt der Vertrag mit einem Auftragsverarbeiter oder ist er in "
                    "Vorbereitung, wird ein offener Prüfpunkt geführt.",
                ],
            ),
            q(
                "3.8",
                "Stelle, die über die Aufnahme des Betriebs entscheidet:",
                target="register:entscheidungsstelle",
                hints=["Funktion angeben, z. B. „Abteilungsleitung Z“."],
            ),
            q(
                "3.9",
                "Weitere zu beteiligende Stellen:",
                target="register:beteiligte_stellen",
                required=False,
                hints=["Z. B. IT-Sicherheit, Organisation, Personalvertretung."],
            ),
        ],
    },
    {
        "id": "W04",
        "title": "4 Betroffene Personen und Daten",
        "goal": "Erfasst werden Kategorien, keine Daten einzelner Personen.",
        "questions": [
            q(
                "4.1",
                "Kategorien betroffener Personen:",
                target="register:kategorien_betroffene",
                reference="Art. 30 Abs. 1 Satz 2 lit. c DSGVO; § 65 Abs. 1 HDSIG",
                hints=[
                    "Z. B. Verfahrensbetroffene, Zeuginnen und Zeugen, Hinweisgebende, "
                    "Vertretungen, Beschäftigte."
                ],
            ),
            q(
                "4.2",
                "Kategorien personenbezogener Daten:",
                target="register:kategorien_daten",
                reference="Art. 30 Abs. 1 Satz 2 lit. c DSGVO; § 65 Abs. 1 HDSIG",
                hints=["Keine Beispieldatensätze aus echten Fällen eintragen."],
            ),
            q(
                "4.3",
                "Werden besondere Kategorien personenbezogener Daten verarbeitet "
                "(z. B. Gesundheitsdaten)?",
                YN,
                "register:besondere_kategorien",
                reference="Art. 9 Abs. 1 DSGVO; § 43 HDSIG",
            ),
            q(
                "4.3.1",
                "Welche besonderen Kategorien werden verarbeitet?",
                target="register:besondere_kategorien_art",
                parent="4.3",
                reference="Art. 9 Abs. 1 DSGVO; § 43 HDSIG",
            ),
            q(
                "4.3.2",
                "Vorschrift, die die Verarbeitung dieser Daten erlaubt, und vorgesehene Garantien:",
                target="register:besondere_kategorien_grundlage",
                parent="4.3",
                reference="Art. 9 Abs. 2 DSGVO; § 43 HDSIG",
                hints=[
                    "Im Dritten Teil HDSIG ist die Verarbeitung nur zulässig, wenn sie zur "
                    "Aufgabenerfüllung unbedingt erforderlich ist; § 43 Abs. 2 HDSIG nennt "
                    "geeignete Garantien (z. B. Zugriffsbeschränkung, Pseudonymisierung, "
                    "Verschlüsselung)."
                ],
            ),
            q(
                "4.4",
                "Werden Daten über strafrechtliche Verurteilungen, Straftaten oder einen "
                "entsprechenden Verdacht verarbeitet?",
                YN,
                "register:daten_art10",
                reference="Art. 10 DSGVO; § 40 HDSIG",
                hints=[
                    "Ist die Frage zu bejahen, ist die Einordnung unter 2.4 besonders "
                    "sorgfältig zu prüfen.",
                ],
            ),
            q(
                "4.5",
                "Werden Daten über Ordnungswidrigkeiten verarbeitet (z. B. Bußgeldverfahren)?",
                YN,
                "register:daten_owi",
                reference="§ 40 HDSIG; Art. 10 DSGVO",
                hints=[
                    "Dient die Verarbeitung der Verfolgung oder Ahndung von "
                    "Ordnungswidrigkeiten, gilt der Dritte Teil HDSIG (§ 40 HDSIG).",
                    "Ob Daten über Ordnungswidrigkeiten außerhalb dieses Bereichs unter "
                    "Art. 10 DSGVO fallen, ist nicht abschließend geklärt; der EuGH hat "
                    "Strafpunkte für Verkehrsverstöße Art. 10 DSGVO zugeordnet (Urteil vom "
                    "22.06.2021, C-439/19). Die Einordnung ist mit der oder dem "
                    "Datenschutzbeauftragten abzustimmen.",
                ],
            ),
            q(
                "4.6",
                "Herkunft der Daten:",
                target="register:herkunft",
                reference="Art. 14 Abs. 2 lit. f DSGVO",
                hints=["Quelle, Aktualität und Übernahmeverfahren angeben."],
            ),
            q(
                "4.7",
                "Voraussichtliche Zahl der betroffenen Personen je Jahr (Schätzung):",
                NUMBER,
                "register:anzahl_betroffene",
                hints=[
                    "Eine Größenordnung genügt.",
                    "Die Zahl fließt in die Vorprüfung zur Datenschutz-Folgenabschätzung ein "
                    "(Kriterium „umfangreiche Verarbeitung“).",
                ],
            ),
            q(
                "4.8",
                "Zeitraum und räumliche Reichweite der Verarbeitung:",
                target="register:umfang",
            ),
            q(
                "4.9",
                "Wie werden auf Tatsachen beruhende Daten von persönlichen Einschätzungen "
                "unterschieden?",
                target="register:tatsachen_trennung",
                context=("regime", ["hdsig_ji", "unklar"]),
                reference="Art. 7 Abs. 1 Richtlinie (EU) 2016/680",
                hints=["Nur im Anwendungsbereich des Dritten Teils HDSIG gefragt."],
            ),
        ],
    },
    {
        "id": "W05",
        "title": "5 Datenflüsse, Empfänger und Dienstleister",
        "goal": "",
        "questions": [
            q(
                "5.1",
                "Orte der Erhebung, Verarbeitung, Speicherung und Sicherung:",
                target="register:datenfluesse",
                hints=["Einschließlich Datensicherungen und temporärer Dateien."],
            ),
            q(
                "5.2",
                "Zugriffsrechte der internen Rollen (Lesen, Ändern, Exportieren, Löschen):",
                target="register:rechte_matrix",
                reference="Art. 25, Art. 32 Abs. 1 DSGVO",
                hints=["Administrative Zugriffe gesondert angeben."],
            ),
            q(
                "5.3",
                "Kategorien von Empfängern:",
                target="register:kategorien_empfaenger",
                reference="Art. 30 Abs. 1 Satz 2 lit. d DSGVO; § 65 Abs. 1 HDSIG",
                hints=["Interne Empfänger und Offenlegungen an andere Stellen unterscheiden."],
            ),
            q(
                "5.4",
                "Werden Daten an andere Stellen außerhalb der Dienststelle übermittelt, die sie "
                "für eigene Zwecke verwenden (z. B. andere Behörden, Gerichte)?",
                YN,
                "register:uebermittlung_extern",
                reference="§ 65 Abs. 1 Nr. 3 und 7 HDSIG; Art. 30 Abs. 1 Satz 2 lit. d DSGVO",
                hints=[
                    "Die Weitergabe an Auftragsverarbeiter (3.7.2) ist keine Übermittlung in "
                    "diesem Sinn und wird hier nicht erfasst.",
                ],
            ),
            q(
                "5.4.1",
                "Übermittlungen:",
                TABLE,
                "register:uebermittlungen",
                parent="5.4",
                reference="§ 65 Abs. 1 HDSIG; Art. 6 Abs. 1 DSGVO",
                columns=[
                    ("empfaenger", "Empfänger", True),
                    ("daten", "Datenkategorien", False),
                    ("zweck", "Zweck", False),
                    ("rechtsgrundlage", "Rechtsgrundlage", True),
                ],
                hints=[
                    "Je Empfänger eine Zeile.",
                    "Im Profil Dritter Teil HDSIG ist die Rechtsgrundlage je Übermittlung "
                    "Pflichtangabe; im DSGVO-Profil wird sie für die Rechtmäßigkeitsprüfung "
                    "ebenfalls verlangt.",
                ],
            ),
            q(
                "5.5",
                "Beteiligte Dienste (Hosting, Support, E-Mail, Monitoring, "
                "Fehlerberichte, Entwicklungsumgebung):",
                target="register:dienste",
                hints=["Auch Telemetrie und Dienste der Softwareentwicklung angeben."],
            ),
            q(
                "5.6",
                "Werden Daten in einem Drittland gespeichert oder dorthin übermittelt, oder "
                "ist ein Zugriff aus einem Drittland möglich?",
                YN,
                "register:drittlandtransfer",
                reference="Art. 30 Abs. 1 Satz 2 lit. e, Art. 44 bis 49 DSGVO; §§ 73 bis 76 HDSIG",
                hints=[
                    "Die Angabe „Server in der EU“ genügt nicht, wenn Support- oder "
                    "Wartungszugriffe aus einem Drittland möglich sind."
                ],
            ),
            q(
                "5.6.1",
                "Empfänger und Drittland:",
                target="register:name_empfaenger_drittland",
                parent="5.6",
            ),
            q(
                "5.6.2",
                "Garantien bzw. Rechtsgrundlage der Drittlandübermittlung:",
                target="register:drittland_garantien",
                parent="5.6",
                reference="Art. 45, 46, 49 DSGVO; §§ 73 bis 76 HDSIG",
            ),
            q(
                "5.7",
                "Vorliegende Verträge, Weisungen und Vereinbarungen:",
                target="register:vertraege",
                required=False,
            ),
        ],
    },
    {
        "id": "W06",
        "title": "6 Speicherdauer und Rechte der betroffenen Personen",
        "goal": "",
        "questions": [
            q(
                "6.1",
                "Lösch- oder Überprüfungsfristen je Datenkategorie:",
                TABLE,
                "register:speicherdauer",
                reference="Art. 5 Abs. 1 lit. e, Art. 30 Abs. 1 Satz 2 lit. f DSGVO; "
                "§ 65 Abs. 1 Nr. 8, § 70 Abs. 4 HDSIG",
                columns=[
                    ("kategorie", "Datenkategorie", True),
                    ("frist", "Frist und auslösendes Ereignis", False),
                    ("begruendung", "Begründung, falls noch keine Frist", False),
                    ("pruefstelle", "Stelle, die die Frist klärt", False),
                ],
                hints=[
                    "Je Datenkategorie eine Zeile, z. B. „Verfahrensakte: 5 Jahre nach "
                    "rechtskräftigem Abschluss“.",
                    "Das Gesetz verlangt die Angabe „wenn möglich“. Fehlt die Frist, sind "
                    "Begründung und klärende Stelle anzugeben; die Zeile bleibt als offene "
                    "Aufgabe bestehen.",
                ],
            ),
            q(
                "6.1.1",
                "Vorschriften oder Regelungen, aus denen sich die Fristen ergeben:",
                target="register:loeschfrist_rechtsgrundlage",
            ),
            q(
                "6.2",
                "Zu beachtende Aufbewahrungs-, Beweissicherungs- und Archivierungspflichten:",
                target="register:aufbewahrung",
                required=False,
            ),
            q(
                "6.3",
                "Umsetzung der Löschung in Datenbanken, Anhängen, Exporten, Zwischenspeichern "
                "und Datensicherungen:",
                target="register:loeschkonzept",
                reference="Art. 17 DSGVO",
            ),
            q(
                "6.4",
                "Art und Zeitpunkt der Information der betroffenen Personen:",
                target="register:information",
                reference="Art. 13, 14 DSGVO; §§ 50 ff. HDSIG",
            ),
            q(
                "6.5",
                "Bearbeitung von Anträgen auf Auskunft, Berichtigung, Löschung und "
                "Einschränkung (Zuständigkeit, Fristen, Identitätsprüfung):",
                target="register:betroffenenrechte",
                reference="Art. 12, 15 bis 18 DSGVO; §§ 50 bis 54 HDSIG",
            ),
            q(
                "6.6",
                "Sollen Rechte der betroffenen Personen beschränkt werden?",
                YN,
                "register:beschraenkung",
                reference="Art. 23 DSGVO mit den Vorschriften des Zweiten Teils HDSIG; "
                "§§ 51, 52 HDSIG",
            ),
            q(
                "6.6.1",
                "Beschränkte Rechte und die Vorschrift, auf die sich die Beschränkung stützt:",
                target="register:beschraenkungen",
                parent="6.6",
                hints=[
                    "Eine pauschale Beschränkung (z. B. „Ordnungswidrigkeitenverfahren: keine "
                    "Auskunft“) genügt nicht.",
                    "Im Dritten Teil HDSIG sind die Gründe für ein Absehen von der Auskunft zu "
                    "dokumentieren (§ 52 Abs. 8 HDSIG); über das Absehen von der "
                    "Benachrichtigung entscheidet die Leitung (§ 51 HDSIG).",
                ],
            ),
        ],
    },
    {
        "id": "W07",
        "title": "7 Sicherheit der Verarbeitung",
        "goal": "Nur umgesetzte und nachweislich wirksame Maßnahmen mindern das Risiko.",
        "questions": [
            q(
                "7.1",
                "Schäden, die betroffenen Personen durch Verlust, Fehlzuordnung, Offenlegung "
                "oder unzulässige Nutzung entstehen können:",
                target="register:schadensszenarien",
                reference="Art. 32 Abs. 2 DSGVO; Erwägungsgrund 75 DSGVO",
                hints=[
                    "Schäden aus Sicht der betroffenen Personen beschreiben, nicht aus Sicht "
                    "der Dienststelle."
                ],
            ),
            q(
                "7.2",
                "Absicherung von Identitäten, Berechtigungen, privilegierten Zugriffen und "
                "Vertretungen:",
                target="register:zugriffsschutz",
                reference="Art. 32 Abs. 1 lit. b DSGVO; § 59 HDSIG",
            ),
            q(
                "7.3",
                "Kann eine allgemeine Beschreibung der technischen und organisatorischen "
                "Maßnahmen angegeben werden?",
                YN,
                "register:tom_bestimmt",
                reference="Art. 30 Abs. 1 Satz 2 lit. g, Art. 32 Abs. 1 DSGVO; § 59 HDSIG",
                hints=["Auch diese Angabe verlangt das Gesetz „wenn möglich“."],
            ),
            q(
                "7.3.1",
                "Allgemeine Beschreibung der technischen und organisatorischen Maßnahmen:",
                target="register:tom",
                parent="7.3",
                hints=[
                    "Keine Passwörter, Schlüssel oder sicherheitskritischen Details "
                    "eintragen; auf das Sicherheitskonzept verweisen."
                ],
            ),
            q(
                "7.3.2",
                "Begründung, warum die Beschreibung noch nicht vorliegt:",
                target="register:tom_begruendung",
                parent="7.3",
                when=["nein"],
            ),
            q(
                "7.3.3",
                "Stelle, die die Beschreibung erstellt:",
                target="register:tom_pruefstelle",
                parent="7.3",
                when=["nein"],
            ),
            q(
                "7.4",
                "Protokollierte Verarbeitungsvorgänge, Zweck und Aufbewahrung der Protokolle:",
                target="register:protokollierung",
                reference="§ 71 HDSIG",
                hints=[
                    "Im Dritten Teil HDSIG sind insbesondere Erhebung, Veränderung, Abfrage, "
                    "Offenlegung, Kombination und Löschung zu protokollieren.",
                    "Die Änderungshistorie des Verzeichnisses ersetzt diese Protokollierung nicht.",
                ],
            ),
            q(
                "7.5",
                "Organisation von Updates, Schwachstellenbehandlung, Datensicherung, "
                "Wiederherstellung und Notbetrieb:",
                target="register:betriebssicherheit",
                reference="Art. 32 Abs. 1 lit. c und d DSGVO",
            ),
            q(
                "7.6",
                "Stelle, die Verletzungen des Schutzes personenbezogener Daten bewertet und "
                "die erforderlichen Meldungen veranlasst:",
                target="register:vorfallmeldung",
                reference="Art. 33, 34 DSGVO; § 60 HDSIG",
            ),
        ],
    },
    {
        "id": "W08",
        "title": "8 Testbetrieb, KI und Veröffentlichung",
        "goal": "",
        "questions": [
            q(
                "8.1",
                "Welche Testdaten werden verwendet?",
                CHOICE,
                "register:testdaten",
                reference="Erwägungsgrund 26 DSGVO",
                choices=[
                    ("keine", "keine Testdaten"),
                    ("synthetisch", "ausschließlich synthetische Daten"),
                    ("anonymisiert", "anonymisierte Daten"),
                    ("pseudonymisiert", "pseudonymisierte Daten (personenbezogen)"),
                    ("echt", "Echtdaten (personenbezogen)"),
                ],
                hints=[
                    "Pseudonymisierte Daten sind personenbezogene Daten; sie gelten nicht als "
                    "anonym."
                ],
            ),
            q(
                "8.2",
                "Maßnahmen zur Trennung von Test- und Produktivbetrieb:",
                target="register:testtrennung",
                required=False,
                hints=["Insbesondere Zugänge, Schnittstellen, Datensicherungen und Protokolle."],
            ),
            q(
                "8.3",
                "Wird künstliche Intelligenz eingesetzt?",
                CHOICE,
                "register:ki_einsatz",
                choices=[
                    ("keine", "nein"),
                    ("entwicklung", "nur in der Softwareentwicklung"),
                    ("fachverfahren", "im Fachverfahren"),
                    ("bewertung", "in der Datenschutzbewertung"),
                    ("mehrere", "in mehreren der genannten Bereiche"),
                ],
            ),
            q(
                "8.3.1",
                "Daten, die KI-Dienste erhalten, und Umgang mit Eingaben, Ausgaben und "
                "Protokollen:",
                target="register:ki_daten",
                parent="8.3",
                when=["entwicklung", "fachverfahren", "bewertung", "mehrere"],
            ),
            q(
                "8.4",
                "Findet Profiling statt, also eine automatisierte Bewertung persönlicher "
                "Aspekte einer Person?",
                YN,
                "register:profiling",
                reference="Art. 4 Nr. 4, Art. 22 DSGVO; § 49 HDSIG; § 65 Abs. 1 HDSIG",
                hints=[
                    "Profiling liegt vor, wenn persönliche Aspekte einer Person automatisiert "
                    "bewertet werden, insbesondere um Verhalten, Zuverlässigkeit oder "
                    "Leistung zu analysieren oder vorherzusagen.",
                    "Eine Sortierung von Vorgängen ohne Bewertung der Person ist kein Profiling.",
                    "Im Profil Dritter Teil HDSIG ist die Angabe Pflicht.",
                ],
            ),
            q(
                "8.4.1",
                "Beschreibung des Profilings und der menschlichen Kontrolle:",
                target="register:profiling_beschreibung",
                parent="8.4",
            ),
            q(
                "8.5",
                "Sollen Inhalte veröffentlicht werden (z. B. Quellcode in einem öffentlichen "
                "Repository)?",
                YN,
                "register:veroeffentlichung_geplant",
            ),
            q(
                "8.5.1",
                "Zu veröffentlichende Inhalte:",
                target="register:veroeffentlichung",
                parent="8.5",
                hints=[
                    "Quellcode, Muster, Metadaten und Verfahrensunterlagen getrennt "
                    "betrachten; keine internen Konfigurationen oder Geheimnisse."
                ],
            ),
            q(
                "8.5.2",
                "Stelle, die die Veröffentlichung freigegeben hat:",
                target="register:veroeffentlichung_verantwortung",
                parent="8.5",
            ),
        ],
    },
    {
        "id": "W09",
        "title": "9 Vorprüfung zur Datenschutz-Folgenabschätzung",
        "goal": "Begründete Vorprüfung nach Art. 35 DSGVO bzw. § 62 HDSIG. Die Kriterien 9.1.x "
        "stammen aus dem gewählten Regelprofil.",
        "questions": [
            q(
                "9.2",
                "Bezug auf eine bestehende Folgenabschätzung oder eine einschlägige Ausnahme:",
                target="register:dsfa_bezug",
                required=False,
                hints=["Fundstelle, Reichweite und Abweichungen angeben."],
            ),
        ],
    },
    {
        "id": "W10",
        "title": "10 Datenschutz-Folgenabschätzung",
        "goal": "Nur wenn die Vorprüfung eine Pflicht ergibt oder die Folgenabschätzung "
        "freiwillig durchgeführt wird.",
        "show_if": {"context": "dsfa", "in": ["pflicht", "freiwillig"]},
        "questions": [
            q(
                "10.1",
                "Verarbeitungsvorgänge und Varianten, die die Folgenabschätzung abdeckt:",
                target="register:dsfa_geltungsbereich",
                reference="Art. 35 Abs. 1 Satz 2, Abs. 7 lit. a DSGVO",
            ),
            q(
                "10.2",
                "Begründung der Notwendigkeit der Verarbeitung:",
                target="assessment:necessity",
                reference="Art. 35 Abs. 7 lit. b DSGVO; § 62 Abs. 4 Nr. 2 HDSIG",
            ),
            q(
                "10.3",
                "Begründung der Verhältnismäßigkeit und verworfene Alternativen:",
                target="assessment:proportionality",
                reference="Art. 35 Abs. 7 lit. b DSGVO; § 62 Abs. 4 Nr. 2 HDSIG",
            ),
            q(
                "10.4",
                "Standpunkt der betroffenen Personen oder ihrer Vertretungen:",
                target="assessment:data_subject_view",
                reference="Art. 35 Abs. 9 DSGVO",
                hints=["Wurde kein Standpunkt eingeholt, sind die Gründe anzugeben."],
            ),
            q(
                "10.5",
                "Anlässe und Termine für die Überprüfung der Folgenabschätzung:",
                target="register:dsfa_ueberpruefung",
                reference="Art. 35 Abs. 11 DSGVO; § 62 Abs. 5 HDSIG",
            ),
        ],
    },
    {
        "id": "W11",
        "title": "11 Konsultation und fachliche Prüfung",
        "goal": "Kein Automatismus durch Fristablauf und kein allgemeiner Knopf „trotzdem "
        "starten“.",
        "questions": [
            q(
                "11.1",
                "Wurde die Aufsichtsbehörde konsultiert?",
                YN,
                "register:konsultiert",
                reference="Art. 36 DSGVO; § 64 HDSIG",
                hints=[
                    "Ob eine Konsultation erforderlich ist, ergibt sich aus der Bewertung "
                    "(Status „Konsultation“)."
                ],
            ),
            q(
                "11.1.1",
                "Datum der Einleitung der Konsultation:",
                DATE,
                "register:konsultation_eingeleitet_am",
                parent="11.1",
            ),
            q(
                "11.1.2",
                "Eingereichte Unterlagen und Rückmeldungen der Aufsichtsbehörde:",
                target="register:konsultation_unterlagen",
                parent="11.1",
            ),
            q(
                "11.1.3",
                "Noch umzusetzende Empfehlungen, Auflagen oder Einschränkungen:",
                target="register:konsultation_massnahmen",
                parent="11.1",
                required=False,
            ),
            q(
                "11.2",
                "Sind alle fachlichen Einwände geklärt?",
                YN,
                "register:einwaende_geklaert",
                task_if=["nein"],
            ),
            q(
                "11.3",
                "Sind widersprüchliche Angaben bereinigt?",
                YN,
                "register:widersprueche_geklaert",
                task_if=["nein"],
            ),
            q(
                "11.4",
                "Liegen alle erforderlichen Nachweise vor?",
                YN,
                "register:nachweise_vollstaendig",
                task_if=["nein"],
                hints=["Fehlende Nachweise werden in der Prüfliste geführt."],
            ),
        ],
    },
    {
        "id": "W12",
        "title": "12 Abschluss, Übernahme und Pflege",
        "goal": "Ergebnis ist eine bestätigte Dokumentation und eine gesonderte "
        "Betriebsentscheidung, kein Konformitätszertifikat.",
        "questions": [
            q(
                "12.1",
                "Sind die Angaben vollständig und aktuell?",
                YN,
                "register:angaben_vollstaendig",
                task_if=["nein"],
            ),
            q(
                "12.2",
                "Hat die fachlich zuständige Stelle die Angaben bestätigt?",
                YN,
                "register:angaben_bestaetigt",
                task_if=["nein"],
                hints=[
                    "Mit der Beantwortung wird der Bearbeitungsstand dokumentiert; die "
                    "Freigabe erfolgt gesondert im Vier-Augen-Prinzip."
                ],
            ),
            q(
                "12.3",
                "Stelle, die Verzeichnis, Folgenabschätzung, Verträge und Maßnahmen im "
                "Betrieb aktuell hält:",
                target="register:pflege_zustaendigkeit",
            ),
            q(
                "12.4",
                "Vertretung dieser Stelle:",
                target="register:pflege_vertretung",
            ),
            q(
                "12.5",
                "Verfahren bei Änderungen, Störungen, Außerbetriebnahme und Aufbewahrung "
                "der Dokumentation:",
                target="register:lebenszyklus",
            ),
        ],
    },
]

#: Hinweise zu Folgeeingaben in den JA-/NEIN-Zweigen (ergänzt zum Baum oben).
EXTRA_HINTS = {
    "1.6.1": ["Kennung so angeben, wie sie im Hausverzeichnis geführt wird."],
    "2.5": [
        "Kurz darlegen, welcher Zweck die Einordnung trägt (z. B. Verfolgung einer "
        "Ordnungswidrigkeit im Einzelfall)."
    ],
    "2.6.1": ["Jeden weiteren Zweck einzeln benennen."],
    "3.4": [
        "Die Vertretung stellt sicher, dass Rückfragen und Änderungen auch bei "
        "Abwesenheit bearbeitet werden."
    ],
    "3.6.1": ["Datum und Form der Einbindung (z. B. Stellungnahme per E-Mail) angeben."],
    "4.8": ["Z. B. „laufende Verfahren seit 2026, landesweit“."],
    "5.6.1": ["Jeden Empfänger mit Land angeben; Unterauftragnehmer eingeschlossen."],
    "5.7": [
        "Bezeichnung, Datum und Ablageort angeben; die Dokumente selbst werden als "
        "Nachweis hinterlegt."
    ],
    "6.1.1": ["Norm, Verwaltungsvorschrift oder Hausregelung angeben."],
    "6.2": [
        "Konflikte zwischen Löschung und Aufbewahrung sowie die Übergabe an das Archiv angeben."
    ],
    "7.3.2": ["Die Begründung macht nachvollziehbar, warum die Beschreibung noch fehlt."],
    "7.3.3": ["Der Punkt bleibt als offene Aufgabe bestehen, bis die Beschreibung vorliegt."],
    "8.3": [
        "Entwicklung, Fachverfahren und Datenschutzbewertung sind getrennte Einsatzarten "
        "mit eigenen Risiken.",
        "Aus dem Einsatz von KI folgt nicht automatisch eine Pflicht zur "
        "Folgenabschätzung; die Bewertung erfolgt unter 9.",
    ],
    "8.3.1": [
        "Anbieter, Speicherort und Speicherdauer sowie den Ausschluss der Nutzung für "
        "Training angeben."
    ],
    "8.4.1": [
        "Beschreiben, welche Merkmale bewertet werden und wie eine Person das Ergebnis "
        "prüft, bevor es Wirkung entfaltet."
    ],
    "8.5": [
        "Veröffentlichter Quellcode ist nicht per se datenschutzwidrig; Konfigurationen, "
        "Verfahrensunterlagen und Metadaten der Versionsverwaltung sind gesondert zu "
        "prüfen."
    ],
    "8.5.2": ["Freigabe einschließlich Prüfung auf Geheimnisse und Lizenzrechte angeben."],
    "11.1.1": [
        "Bei einer laufenden Konsultation bleibt die Betriebsentscheidung gesperrt; "
        "ausgenommen ist nur der Dringlichkeitsfall nach § 64 Abs. 4 HDSIG."
    ],
    "11.1.2": ["Unterlagen mit Version und Datum angeben."],
    "11.1.3": ["Jede Auflage wird als Maßnahme mit Zuständigkeit geführt."],
    "12.4": ["Die Zuständigkeit darf nicht an eine einzelne Person ohne Vertretung gebunden sein."],
    "12.5": [
        "Relevante Änderungen (neuer Zweck, neuer Empfänger, neue Technik) lösen eine "
        "erneute Prüfung aus; eine frühere Freigabe gilt nicht weiter."
    ],
}

# Amtliche Auslegungshilfen (Quellenkürzel siehe SOURCES); werden an die Hinweise angehängt.
DSK_VVT = "DSK, Hinweise zum Verzeichnis von Verarbeitungstätigkeiten (Stand 02/2018)"
DSK_KP5 = "DSK, Kurzpapier Nr. 5 Datenschutz-Folgenabschätzung (Stand 17.12.2018)"
DSK_KP10 = "DSK, Kurzpapier Nr. 10 Informationspflichten (Stand 16.01.2018)"
DSK_KP13 = "DSK, Kurzpapier Nr. 13 Auftragsverarbeitung (Stand 17.12.2018)"
DSK_KP16 = "DSK, Kurzpapier Nr. 16 Gemeinsam Verantwortliche (Stand 19.03.2018)"
EDSA_0720 = "EDSA, Leitlinien 07/2020 zu Verantwortlichem und Auftragsverarbeiter, v2.1"
EDSA_0521 = "EDSA, Leitlinien 05/2021 zu Art. 3 und Kapitel V DSGVO, v2.0"
EDSA_0122 = "EDSA, Leitlinien 01/2022 zum Auskunftsrecht, v2.1"
EDSA_0922 = "EDSA, Leitlinien 9/2022 zur Meldung von Datenschutzverletzungen, v2.0"
EDSA_0125 = "EDSA, Leitlinien 01/2025 zur Pseudonymisierung (Konsultationsfassung)"
EDSA_0419 = "EDSA, Leitlinien 4/2019 zu Art. 25 DSGVO, v2.0"
WP251 = "Art.-29-Gruppe, WP251 rev.01 (vom EDSA bestätigt)"
WP248 = "Art.-29-Gruppe, WP248 rev.01 (vom EDSA bestätigt)"
HBDI_DSFA = "HBDI, Liste der Verarbeitungsvorgänge nach Art. 35 Abs. 4 DSGVO"
HBDI_POL = "HBDI, Meldung von Datenschutzpannen bei der Polizei (Stand 31.03.2023)"

GUIDANCE = {
    "1.1": [
        f"{DSK_VVT}, S. 1: Eine Verarbeitungstätigkeit ist in der Regel ein "
        "Geschäftsprozess auf geeignetem Abstraktionsniveau; jeder neue Zweck begründet "
        "eine eigene Tätigkeit."
    ],
    "2.1": [
        f"{DSK_VVT}, Abschn. 6.2: Die Zwecke sind vorab festzulegen und so aussagekräftig "
        "zu beschreiben, dass die Zulässigkeit vorläufig eingeschätzt werden kann."
    ],
    "2.7": [
        f"{EDSA_0419}, Rn. 74–76: Zu prüfen ist, ob der Zweck mit weniger, gröberen oder "
        "aggregierten Daten oder ganz ohne Personenbezug erreichbar ist."
    ],
    "3.7": [
        f"{DSK_KP13}, S. 3: Wartung, Fernwartung und Support mit Zugriff oder "
        "Zugriffsmöglichkeit auf personenbezogene Daten sind Auftragsverarbeitung; rein "
        "technische Wartung der Infrastruktur (z. B. Strom, Kühlung) ist es nicht."
    ],
    "3.7.2": [
        f"{EDSA_0720}, Rn. 82: Nicht jeder Dienstleister ist Auftragsverarbeiter; maßgeblich "
        "ist die konkrete Tätigkeit, nicht die Art der Stelle.",
        f"{DSK_KP13}, S. 1: Der Auftragsverarbeiter ist kein Dritter; seine Verarbeitung "
        "wird dem Verantwortlichen zugerechnet.",
    ],
    "3.1.3": [
        f"{DSK_KP16}, S. 1: Gemeinsame Verantwortung liegt vor, wenn mehrere Stellen "
        "gemeinsam über Zwecke und Mittel entscheiden; sie privilegiert die Weitergabe "
        "der Daten nicht."
    ],
    "5.3": [
        f"{EDSA_0720}, Rn. 90: Empfänger ist jede Stelle, der Daten offengelegt werden, "
        "auch ein Auftragsverarbeiter.",
        f"{DSK_VVT}, Abschn. 6.4: Auch Organisationseinheiten derselben Behörde können "
        "Empfänger sein; Zugriffsberechtigte nach Rollen oder Funktionen angeben, nicht "
        "namentlich.",
    ],
    "5.6": [
        f"{EDSA_0521}, Beispiel 11: Ein Fernzugriff aus einem Drittland ist eine "
        "Übermittlung, auch wenn Daten nur angezeigt werden (z. B. Support).",
        f"{DSK_VVT}, Abschn. 6.4: Zum Drittlandbezug ist stets eine Aussage zu treffen, "
        "auch „keine Übermittlung vorgesehen“.",
    ],
    "6.1": [
        f"{DSK_VVT}, Abschn. 6.6: Ein allgemeiner Verweis auf Aufbewahrungspflichten "
        "genügt nicht; die Fristen sind je Datenkategorie präzise anzugeben."
    ],
    "6.4": [
        f"{DSK_KP10}, S. 3: Bei Erhebung bei der betroffenen Person ist zum Zeitpunkt der "
        "Erhebung zu informieren, sonst innerhalb angemessener Frist, höchstens eines "
        "Monats."
    ],
    "6.5": [
        f"{EDSA_0122}, Zusammenfassung: Auskunft unverzüglich, spätestens binnen eines "
        "Monats; Verlängerung um zwei Monate nur mit Begründung gegenüber der betroffenen "
        "Person."
    ],
    "7.3": [
        f"{DSK_VVT}, Abschn. 6.7: Trotz „wenn möglich“ ist die allgemeine Beschreibung der "
        "Regelfall; die vollständige Darstellung gehört in das Sicherheitskonzept "
        "(z. B. nach Standard-Datenschutzmodell oder BSI-IT-Grundschutz)."
    ],
    "7.6": [
        f"{EDSA_0922}, Rn. 31: Die 72-Stunden-Frist beginnt, sobald mit hinreichender "
        "Sicherheit feststeht, dass personenbezogene Daten betroffen sind; auch nicht "
        "meldepflichtige Verletzungen sind zu dokumentieren.",
        f"{HBDI_POL}: Die Meldepflicht nach § 60 HDSIG trifft auch Bußgeldstellen und "
        "Kommunen bei der Verfolgung von Ordnungswidrigkeiten.",
    ],
    "8.1": [
        f"{EDSA_0125}, Rn. 22: Pseudonymisierte Daten bleiben personenbezogen, auch wenn "
        "die Zuordnungsinformationen bei einer anderen Stelle liegen."
    ],
    "8.4": [
        f"{WP251}, Abschn. II.A und II.B: Profiling setzt eine automatisierte Bewertung "
        "persönlicher Aspekte voraus; eine ausschließlich automatisierte Entscheidung "
        "ergeht ohne menschliche Beteiligung und ist davon zu unterscheiden."
    ],
    "9.2": [
        "Im Dritten Teil HDSIG entscheidet allein, ob die Verarbeitung voraussichtlich ein hohes "
        "Risiko für die Rechte und Freiheiten natürlicher Personen zur Folge hat (§ 62 Abs. 1 "
        "HDSIG); Listen und Kriterien zur DSGVO sind dort nur Anhaltspunkte.",
        f"Nur DSGVO – {WP248}, S. 11: Sind zwei Kriterien erfüllt, ist in den meisten Fällen "
        "eine Folgenabschätzung erforderlich; im Zweifel ist sie durchzuführen.",
        f"Nur DSGVO – {HBDI_DSFA}: Fehlt ein Vorgang auf der Liste, ist die "
        "Folgenabschätzung nicht automatisch entbehrlich.",
    ],
    "10.4": [
        f"{DSK_KP5}, S. 1–3: Der Standpunkt der Betroffenen kann z. B. über Gremien der "
        "Mitbestimmung eingeholt werden; die oder der Datenschutzbeauftragte berät."
    ],
}

#: Quellen der Auslegungshinweise (Fundstellen im Netz).
SOURCES = [
    (DSK_VVT, "https://www.datenschutzkonferenz-online.de/media/ah/"
     "201802_ah_verzeichnis_verarbeitungstaetigkeiten.pdf"),
    (DSK_KP5, "https://www.datenschutzkonferenz-online.de/media/kp/dsk_kpnr_5.pdf"),
    (DSK_KP10, "https://www.datenschutzkonferenz-online.de/media/kp/dsk_kpnr_10.pdf"),
    (DSK_KP13, "https://www.datenschutzkonferenz-online.de/media/kp/dsk_kpnr_13.pdf"),
    (DSK_KP16, "https://www.datenschutzkonferenz-online.de/media/kp/dsk_kpnr_16.pdf"),
    (EDSA_0720, "https://www.edpb.europa.eu/system/files/2023-10/"
     "EDPB_guidelines_202007_controllerprocessor_final_en.pdf"),
    (EDSA_0521, "https://www.edpb.europa.eu/system/files/2023-02/edpb_guidelines_05-2021_"
     "interplay_between_the_application_of_art3-chapter_v_of_the_gdpr_v2_en_0.pdf"),
    (EDSA_0122, "https://www.edpb.europa.eu/system/files/2023-04/"
     "edpb_guidelines_202201_data_subject_rights_access_v2_en.pdf"),
    (EDSA_0922, "https://www.edpb.europa.eu/system/files/2023-04/"
     "edpb_guidelines_202209_personal_data_breach_notification_v2.0_en.pdf"),
    (EDSA_0125, "https://www.edpb.europa.eu/system/files/2025-01/"
     "edpb_guidelines_202501_pseudonymisation_en.pdf"),
    (EDSA_0419, "https://www.edpb.europa.eu/system/files/documents/files/file1/"
     "edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf"),
    (WP251, "https://ec.europa.eu/newsroom/article29/redirection/document/49826"),
    (WP248, "https://ec.europa.eu/newsroom/article29/redirection/document/47711"),
    (HBDI_DSFA, "https://datenschutz.hessen.de/datenschutz/it-und-datenschutz/"
     "datenschutz-folgenabschaetzung"),
    (HBDI_POL, "https://datenschutz.hessen.de/datenschutz/polizei-und-justiz/"
     "meldung-von-datenschutzpannen-bei-der-polizei"),
]  # fmt: skip

F, IT, R = "fachbereich", "it_betrieb", "recht"
#: Zuständigkeit je Kapitel und abweichend je Frage.
CHAPTER_ROLE = {"W01": F, "W02": R, "W03": F, "W04": F, "W05": IT, "W06": F, "W07": IT,
                "W08": IT, "W09": R, "W10": R, "W11": R, "W12": F}  # fmt: skip
ROLE = {
    "1.4": IT, "1.5": IT, "1.7": R,
    "2.1": F, "2.6": F, "2.6.1": F, "2.7": F,
    "3.1": R, "3.1.1": R, "3.1.2": R, "3.5": IT, "3.7": IT, "3.7.1": IT, "3.7.2": R,
    "3.1.3": R, "3.1.3.1": R,
    "4.3.2": R,
    "5.3": F, "5.4": F, "5.4.1": R, "5.6.2": R, "5.7": R,
    "6.1.1": R, "6.2": R, "6.3": IT, "6.6": R, "6.6.1": R,
    "7.1": F, "7.6": F,
    "8.4": F, "8.4.1": F,
    "10.1": F,
}  # fmt: skip


def closing(step: dict) -> list[dict]:
    """Abschlussfrage je Kapitel; „Ja“ hinterlässt eine offene Aufgabe."""
    chapter = step["title"].split()[0]
    top = [int(i["number"].split(".")[1]) for i in step["questions"]]
    number = f"{chapter}.{max(top) + 1}"
    return [
        q(
            number,
            f"Bestehen zu Kapitel {chapter} noch offene Punkte?",
            YN,
            task_if=["ja"],
            hints=["Offene Punkte bleiben als Aufgabe bestehen, bis sie erledigt sind."],
        ),
        q(
            f"{number}.1",
            "Offene Punkte und zuständige Stelle:",
            parent=number,
        ),
    ]


def main() -> None:
    for step in STEPS:
        step["questions"].extend(closing(step))
        for item in step["questions"]:
            hints = item["hints"] or EXTRA_HINTS.get(item["id"], [])
            item["hints"] = [*hints, *GUIDANCE.get(item["id"], [])]
            item["help"] = " ".join(item["hints"])
            item["role"] = ROLE.get(item["id"], CHAPTER_ROLE[step["id"]])
    catalog = {
        "schema": "auditcore_dataprotection.wizard/1",
        "version": "2026.10.3",
        "source": "Prüfkatalog VVT/DSFA vom 08.10.2026, Abschnitt 7; Aufbau nach dem "
        "Checklistendesigner (Fragenbaum mit Hinweisen und Fundstellen). HDSIG-Fundstellen "
        "am Gesetzeswortlaut geprüft; Auslegungshinweise nach den unter „sources“ "
        "genannten Veröffentlichungen von EDSA, DSK und HBDI. Arbeitsgrundlage, keine "
        "Rechtsquelle.",
        "sources": [{"title": t, "url": u} for t, u in SOURCES],
        "answer_values": {"ja_nein_unklar": ["ja", "nein", "unklar"]},
        "steps": STEPS,
    }
    TARGET.write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n")
    count = sum(len(s["questions"]) for s in STEPS)
    print(f"{TARGET.name}: {len(STEPS)} Kapitel, {count} Fragen")


if __name__ == "__main__":
    main()
