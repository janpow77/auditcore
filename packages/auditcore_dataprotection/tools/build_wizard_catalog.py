"""Fragenkatalog des Datenschutz-Assistenten (wizard-2026.10.2) erzeugen.

Aufbau nach dem Muster des Checklistendesigners (audit_designer, v05-Baum):
nummerierte Fragen, Entscheidungsfragen mit JA-/NEIN-Zweig, Hinweise als
Aufzählung mit vorangestellter Fundstelle; reine Eingaben enden mit Doppelpunkt.

Fundstellen sind vor der Freigabe gegen die amtlichen Fassungen zu prüfen.

    python tools/build_wizard_catalog.py
"""

from __future__ import annotations

import json
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[1]
    / "src/auditcore_dataprotection/catalogs/wizard-2026.10.2.json"
)

YN = "ja_nein_unklar"
TEXT = "text"
CHOICE = "auswahl"
IMPL = "umsetzung"
NUMBER = "zahl"
TABLE = "tabelle"


def q(number, text, kind=TEXT, target="", reference="", hints=(), *, required=True,
      parent=None, when=None, choices=(), justify=(), columns=(), context=None):  # fmt: skip
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
        item["columns"] = [{"key": k, "title": t, "required": r} for k, t, r in columns]
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
                    ("dsgvo", "DSGVO"),
                    ("hdsig_ji", "Dritter Teil HDSIG"),
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
                "Weitere Zwecke und Begründung ihrer Vereinbarkeit mit dem ursprünglichen Zweck:",
                target="register:weitere_zwecke_beschreibung",
                parent="2.6",
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
                    ("gemeinsam_verantwortlicher", "Gemeinsam Verantwortlicher"),
                ],
                hints=[
                    "Die Rolle bestimmt die Vorlage des Verzeichnisses (Art. 30 Abs. 1 oder "
                    "Abs. 2 DSGVO, § 65 Abs. 1 oder 2 HDSIG)."
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
                "Werden Dienstleister eingesetzt, die personenbezogene Daten im Auftrag "
                "verarbeiten?",
                YN,
                "register:auftragsverarbeitung",
                reference="Art. 28 DSGVO",
                hints=[
                    "Nicht jeder Dienstleister ist Auftragsverarbeiter; maßgeblich ist die "
                    "weisungsgebundene Verarbeitung."
                ],
            ),
            q("3.7.1", "Auftragsverarbeiter:", target="register:auftragsverarbeiter", parent="3.7"),
            q(
                "3.7.2",
                "Liegt mit jedem Auftragsverarbeiter ein Vertrag nach Art. 28 Abs. 3 DSGVO vor?",
                YN,
                "register:avv_besteht",
                parent="3.7",
                reference="Art. 28 Abs. 3 DSGVO",
                hints=["Ein fehlender Vertrag wird als offener Prüfpunkt geführt."],
            ),
            q(
                "3.8",
                "Werden die Zwecke und Mittel gemeinsam mit einer anderen Stelle festgelegt?",
                YN,
                "register:gemeinsame_verantwortlichkeit",
                reference="Art. 26 DSGVO",
            ),
            q(
                "3.8.1",
                "Gemeinsam Verantwortliche:",
                target="register:gemeinsame_verantwortliche",
                parent="3.8",
                hints=[
                    "Die Vereinbarung nach Art. 26 Abs. 1 Satz 2 DSGVO ist als Nachweis zu "
                    "hinterlegen."
                ],
            ),
            q(
                "3.9",
                "Stelle, die über die Aufnahme des Betriebs entscheidet, und weitere zu "
                "beteiligende Stellen:",
                target="register:entscheidungsstelle",
                hints=["Z. B. IT-Sicherheit, Organisation, gegebenenfalls Personalvertretung."],
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
                "Welche besonderen Kategorien, und auf welche Ausnahme stützt sich die "
                "Verarbeitung?",
                target="register:besondere_kategorien_grundlage",
                parent="4.3",
                reference="Art. 9 Abs. 2 DSGVO; § 43 HDSIG",
            ),
            q(
                "4.4",
                "Werden Daten über Straftaten, Ordnungswidrigkeiten, Verdachtsmomente oder "
                "Sanktionen verarbeitet?",
                YN,
                "register:daten_art10",
                reference="Art. 10 DSGVO; Dritter Teil HDSIG",
                hints=[
                    "Ist die Frage zu bejahen, ist die Einordnung unter 2.4 besonders "
                    "sorgfältig zu prüfen."
                ],
            ),
            q(
                "4.5",
                "Herkunft der Daten:",
                target="register:herkunft",
                reference="Art. 14 Abs. 2 lit. f DSGVO",
                hints=["Quelle, Aktualität und Übernahmeverfahren angeben."],
            ),
            q(
                "4.6",
                "Voraussichtliche Zahl der betroffenen Personen (Schätzung):",
                NUMBER,
                "register:anzahl_betroffene",
                hints=[
                    "Eine Größenordnung genügt.",
                    "Die Zahl fließt in die Vorprüfung zur Datenschutz-Folgenabschätzung ein "
                    "(Kriterium „umfangreiche Verarbeitung“).",
                ],
            ),
            q(
                "4.7",
                "Zeitraum und räumliche Reichweite der Verarbeitung:",
                target="register:umfang",
            ),
            q(
                "4.8",
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
                "Werden Daten an Stellen außerhalb der verantwortlichen Dienststelle übermittelt?",
                YN,
                "register:uebermittlung_extern",
                reference="§ 65 Abs. 1 HDSIG (Rechtsgrundlage einschließlich Übermittlungen)",
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
                "Kann für jede Datenkategorie eine Lösch- oder Überprüfungsfrist angegeben werden?",
                YN,
                "register:frist_bestimmt",
                reference="Art. 5 Abs. 1 lit. e, Art. 30 Abs. 1 Satz 2 lit. f DSGVO; "
                "§ 65 Abs. 1 HDSIG",
                hints=[
                    "Das Gesetz verlangt die Angabe „wenn möglich“. Ohne konkrete Frist sind "
                    "Begründung und Prüfstelle anzugeben; der Punkt bleibt als offene Aufgabe "
                    "bestehen."
                ],
            ),
            q(
                "6.1.1",
                "Fristen je Datenkategorie und auslösendes Ereignis:",
                target="register:speicherdauer",
                parent="6.1",
            ),
            q(
                "6.1.2",
                "Grundlage der Fristen:",
                target="register:loeschfrist_rechtsgrundlage",
                parent="6.1",
            ),
            q(
                "6.1.3",
                "Begründung, warum noch keine Frist angegeben werden kann:",
                target="register:speicherdauer_begruendung",
                parent="6.1",
                when=["nein"],
            ),
            q(
                "6.1.4",
                "Stelle, die die Frist klärt:",
                target="register:speicherdauer_pruefstelle",
                parent="6.1",
                when=["nein"],
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
                reference="Art. 23 DSGVO; § 70 HDSIG",
            ),
            q(
                "6.6.1",
                "Beschränkte Rechte und die Vorschrift, auf die sich die Beschränkung stützt:",
                target="register:beschraenkungen",
                parent="6.6",
                hints=[
                    "Eine pauschale Beschränkung (z. B. „Ordnungswidrigkeitenverfahren: keine "
                    "Auskunft“) genügt nicht."
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
                "Umsetzungsstand der Schutzmaßnahmen insgesamt:",
                IMPL,
                "register:massnahmen_stand",
                hints=[
                    "Der Stand je Maßnahme wird in der Maßnahmenliste geführt.",
                    "Geplante Maßnahmen gelten nicht als wirksam.",
                ],
            ),
            q(
                "7.7",
                "Stelle, die Verletzungen des Schutzes personenbezogener Daten bewertet und "
                "die erforderlichen Meldungen veranlasst:",
                target="register:vorfallmeldung",
                reference="Art. 33, 34 DSGVO",
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
                    ("synthetisch", "synthetisch"),
                    ("anonymisiert", "anonymisiert"),
                    ("pseudonymisiert", "pseudonymisiert"),
                    ("echt", "echte Daten"),
                    ("keine", "keine Testdaten"),
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
        "goal": "Begründete Vorprüfung nach Art. 35 DSGVO bzw. § 62 HDSIG. Die Kriterien 9.2 "
        "stammen aus dem gewählten Regelprofil.",
        "questions": [
            q(
                "9.1",
                "Einschlägige gesetzliche oder aufsichtsbehördliche Fallgruppe:",
                target="register:dsfa_fallgruppe",
                required=False,
                reference="Art. 35 Abs. 3 und 4 DSGVO; § 62 Abs. 1 HDSIG",
                hints=["„Noch nicht geprüft“ ist eine zulässige Angabe."],
            ),
            q(
                "9.3",
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
                target="register:konsultation_eingeleitet_am",
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
                "Sind fachliche Einwände, widersprüchliche Angaben und fehlende Nachweise geklärt?",
                YN,
                "register:einwaende_geklaert",
                hints=["Offene Punkte werden in der Prüfliste geführt."],
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
                "Sind die Angaben vollständig, aktuell und von der fachlich zuständigen "
                "Stelle bestätigt?",
                YN,
                "register:angaben_bestaetigt",
                hints=[
                    "Mit der Beantwortung wird der Bearbeitungsstand dokumentiert; die "
                    "Freigabe erfolgt gesondert im Vier-Augen-Prinzip."
                ],
            ),
            q(
                "12.2",
                "Stelle, die Verzeichnis, Folgenabschätzung, Verträge und Maßnahmen im "
                "Betrieb aktuell hält, und ihre Vertretung:",
                target="register:pflege_zustaendigkeit",
            ),
            q(
                "12.3",
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
    "3.4": [
        "Die Vertretung stellt sicher, dass Rückfragen und Änderungen auch bei "
        "Abwesenheit bearbeitet werden."
    ],
    "3.6.1": ["Datum und Form der Einbindung (z. B. Stellungnahme per E-Mail) angeben."],
    "3.7.1": ["Name des Dienstleisters und Gegenstand des Auftrags angeben."],
    "4.7": ["Z. B. „laufende Verfahren seit 2026, landesweit“."],
    "5.6.1": ["Jeden Empfänger mit Land angeben; Unterauftragnehmer eingeschlossen."],
    "5.7": [
        "Bezeichnung, Datum und Ablageort angeben; die Dokumente selbst werden als "
        "Nachweis hinterlegt."
    ],
    "6.1.1": [
        "Je Datenkategorie Frist und auslösendes Ereignis angeben (z. B. „Verfahrensakte: "
        "5 Jahre nach rechtskräftigem Abschluss“)."
    ],
    "6.1.2": ["Norm, Verwaltungsvorschrift oder Hausregelung angeben."],
    "6.1.3": ["Die Begründung macht nachvollziehbar, warum die Frist noch offen ist."],
    "6.1.4": ["Der Punkt bleibt als offene Aufgabe bestehen, bis die Frist feststeht."],
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
    "12.2": ["Die Zuständigkeit darf nicht an eine einzelne Person ohne Vertretung gebunden sein."],
    "12.3": [
        "Relevante Änderungen (neuer Zweck, neuer Empfänger, neue Technik) lösen eine "
        "erneute Prüfung aus; eine frühere Freigabe gilt nicht weiter."
    ],
}


def main() -> None:
    for step in STEPS:
        for item in step["questions"]:
            if not item["hints"] and item["id"] in EXTRA_HINTS:
                item["hints"] = EXTRA_HINTS[item["id"]]
                item["help"] = " ".join(item["hints"])
    catalog = {
        "schema": "auditcore_dataprotection.wizard/1",
        "version": "2026.10.2",
        "source": "Prüfkatalog VVT/DSFA vom 08.10.2026, Abschnitt 7; Aufbau nach dem "
        "Checklistendesigner (Fragenbaum mit Hinweisen und Fundstellen). Arbeitsgrundlage, "
        "keine Rechtsquelle; Fundstellen vor Freigabe gegen amtliche Fassungen prüfen.",
        "answer_values": {"ja_nein_unklar": ["ja", "nein", "unklar"]},
        "steps": STEPS,
    }
    TARGET.write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n")
    count = sum(len(s["questions"]) for s in STEPS)
    print(f"{TARGET.name}: {len(STEPS)} Kapitel, {count} Fragen")


if __name__ == "__main__":
    main()
