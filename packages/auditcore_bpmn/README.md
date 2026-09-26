# auditcore_bpmn

## Zweck

BPMN 2.0 mit der FlowAudit-Erweiterung (Schema 1.1) sicher lesen, prüfen, vergleichen, neutralisieren und berichten – für Prozessdiagramme von Verwaltungs- und Kontrollsystemen aller Fonds mit geteilter Mittelverwaltung.

Für Anwendungen der Prüfbehörden und Programmbehörden (audit_designer,
FlowStat, künftig der BPMN-Editor `@auditcore/bpmn-flowaudit`). Framework-frei,
ohne Datenbank und ohne Pflichtabhängigkeiten. Nicht enthalten: Editor,
Oberfläche, Rechteprüfung und Speicherung in einer Datenbank (dafür gibt es den
Speicher-Port `Storage`).

| Bereich | Modul | Inhalt |
|---|---|---|
| Sicheres Parsen | `safe_xml`, `serialize` | DTD/Entitäten/externe Verweise verboten (defusedxml oder gehärteter Expat), rundlauftreues Schreiben |
| Elementmodell | `model` | alle BPMN-2.0-Elemente: Pools, Lanes (verschachtelt), Aktivitäten, Ereignisse, Gateways, Daten, Artefakte, Flüsse |
| Erweiterung | `extensions`, `writer` | Schema 1.0 (Freitext-Rechtsgrundlage, interne Notiz) und 1.1 (Diagramm-Infos, strukturierte Rechtsgrundlagen, Akteure, Kennzeichen, Prüfbezüge, Kontrollen, Risiken, Nachweise, Fristen, Verweise, Prüfschritte, Feststellungen, Quellen) |
| Profile | `profiles` | Kataloge je Förderperiode: KA nach Anhang XI VO (EU) 2021/1060 bzw. Anhang IV Delegierte VO (EU) Nr. 480/2014, Rollen, Fonds, Artikelüberschriften, Funktionstrennung, Vorlagen |
| Prüfregeln | `validation` | 70+ Regeln mit stabilen IDs (`BPMN-S…`, `BPMN-F…`, `BPMN-P…`, `BPMN-FT…`), Meldungen deutsch/englisch |
| Sammlung | `collection` | Ordner, Tags, Reihenfolge, Verweise, Übersichten, KA-Abdeckung, Schlüsselabfrage, Freigaben (SHA-256), Speicher-Port und Dateiablage |
| Vergleich | `comparison` | Versionsvergleich mit Synopse, Soll/Ist-Abgleich (erfüllt/nicht erfüllt), Einfärben |
| Neutralisieren | `neutralize` | Rollen statt Namen; E-Mail, Beträge, Firmen, Personen, Kennnummern, Befunde entfernt; Bericht |
| Anreichern | `enrichment` | Vorschläge aus Altbestand: Normzitate, Fundstellen, BK, Feststellungsbezüge, Prüffelder, Register, Rollen, Farben |
| Berichte | `reports` | Prozesstabelle, Risiko-Kontroll-Matrix, Feststellungsliste, Durchlauftest, KA-Kategorievorschlag; CSV, MyST, Excel |
| Legacy | `legacy` | legacy-treue Übernahme von `bpmn_analyzer.py`, `validate_bpmn_bva` und `bpmn_export.py` aus audit_designer |
| Normen | `citations`, `legal` | Zitate erkennen, CELEX/ELI/URL ableiten; Extra `legal` mit auditcore_legal_sources |

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_bpmn \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.1 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-bpmn/`):

```text
auditcore_bpmn @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_bpmn-0.1.1-py3-none-any.whl#sha256=3707df29a78341a5c16e469364203d86d0b430635a0ff0804ada7b17658cd72f
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-bpmn
```

Extras:

- `[xml]` – defusedxml als Parser (ohne Extra: gleichwertig gehärteter Expat), Debian `python3-defusedxml`;
- `[excel]` – Legacy-Excelbericht und Berichte als xlsx über openpyxl, Debian `python3-openpyxl`;
- `[pdf]` – Legacy-PDF-Bericht über reportlab, Debian `python3-reportlab`;
- `[legal]` – Normauflösung mit `auditcore_legal_sources`, Debian `python3-auditcore-legal-sources`;
- `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Ein synthetischer Ablauf mit strukturierter Rechtsgrundlage wird gelesen,
geprüft, als Prozesstabelle ausgegeben und neutralisiert:

```python
from datetime import date

from auditcore_bpmn import neutralize, parse_bpmn, process_table, validate

xml = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:flowaudit="https://flowaudit.de/bpmn/schema/1.0" id="Defs_1">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="Start_1" name="Antrag eingegangen"/>
    <bpmn:task id="Task_1" name="Antrag prüfen">
      <bpmn:extensionElements>
        <flowaudit:rechtsgrundlage norm="Verordnung (EU) 2021/1060" artikel="74" absatz="2"/>
      </bpmn:extensionElements>
    </bpmn:task>
    <bpmn:endEvent id="End_1" name="Antrag geprüft"/>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_1"/>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="End_1"/>
  </bpmn:process>
</bpmn:definitions>"""

document = parse_bpmn(xml)
basis = document.elements["Task_1"].extensions.legal_bases[0]
assert basis.citation() == "Artikel 74 Absatz 2 der Verordnung (EU) 2021/1060"

report = validate(document, reference_date=date(2026, 9, 25))
assert report.is_valid
assert [issue.rule_id for issue in report.issues] == ["BPMN-F002"]

rows = process_table(document)
assert rows[0]["rechtsgrundlage"] == "Art. 74 Abs. 2 VO (EU) 2021/1060"
assert "Antrag prüfen" in neutralize(document).xml
```

```pycon
>>> report.issues[0].message()
'Das Diagramm hat keine Diagramm-Infos (flowaudit:diagrammInfo).'
>>> report.issues[0].message("en")
'The diagram has no diagram information (flowaudit:diagrammInfo).'
```

Weitere Beispiele (Sammlung, Soll/Ist, Berichte, Einbindung in Anwendungen):
[`docs/consumer-integration.md`](docs/consumer-integration.md); alle Regeln:
[`docs/rules.md`](docs/rules.md).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_bpmn.__all__` (73):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `FLOWAUDIT_NAMESPACE` | Konstante | Unveränderter Namensraum seit Schema 1.0; die Version 1.1 steht im Attribut ``schemaVersion`` von ``flowaudit:diagrammInfo``. | `namespaces` |
| `FLOWAUDIT_PREFIX` | Konstante | – | `namespaces` |
| `FLOWAUDIT_SCHEMA_VERSION` | Konstante | – | `namespaces` |
| `STANDARD_PROFILE` | Konstante | – | `profiles.loader` |
| `Actor` | Datenklasse | ``flowaudit:akteur`` an Pool oder Lane. | `extensions.types` |
| `AuditFinding` | Datenklasse | ``flowaudit:feststellung``: Prüffeststellung (formell oder finanziell). | `extensions.types` |
| `AuditReference` | Datenklasse | XML-Element `flowaudit:pruefbezug`: Kernanforderung (KA) und Bewertungskriterium (BK). | `extensions.types` |
| `AuditStep` | Datenklasse | XML-Element `flowaudit:pruefschritt`: Durchlauf- oder Kontrolltest an einem Element. | `extensions.types` |
| `BpmnAnalyzer` | Klasse | BPMN-XML-Analyse der FlowStat-Attribute (legacy-treu). | `legacy.analyzer` |
| `BpmnDocument` | Datenklasse | Gelesenes BPMN-Dokument; der XML-Baum bleibt für gezielte Änderungen zugänglich. | `model.elements` |
| `BpmnElement` | Datenklasse | Ein BPMN-Element mit Kennung. | `model.elements` |
| `BpmnError` | Ausnahme | Basisklasse aller Fehler dieses Pakets. | `errors` |
| `BpmnXmlError` | Ausnahme | BPMN-XML ist nicht wohlgeformt. | `errors` |
| `CatalogError` | Ausnahme | Unbekannter oder fehlerhafter Katalog. | `errors` |
| `CitationMatch` | Datenklasse | Ein erkanntes Zitat mit Fundstelle im Text. | `citations` |
| `CollectionError` | Ausnahme | Unzulässige Änderung oder unzulässiger Inhalt einer Diagrammsammlung. | `errors` |
| `Comparison` | Datenklasse | Ergebnis des Versionsvergleichs. | `comparison.diff` |
| `Control` | Datenklasse | ``flowaudit:kontrolle`` an Aktivitäten und Gateways. | `extensions.types` |
| `CrossReference` | Datenklasse | ``flowaudit:verweis``: stabiler fachlicher Schlüssel (Prüffeld, Feststellungsbezug, Register). | `extensions.types` |
| `Deadline` | Datenklasse | ``flowaudit:frist`` an Zeitgeber-Ereignissen und Aufgaben. | `extensions.types` |
| `DiagramCollection` | Klasse | Veränderliche Sammlung; jede Änderung prüft die Integrität sofort. | `collection.collection` |
| `DiagramInfo` | Datenklasse | ``flowaudit:diagrammInfo`` am Hauptelement (Kollaboration oder erster Prozess). | `extensions.types` |
| `EsiRequirement` | Datenklasse | Eine ESI-Anforderung mit Kriterien. | `extensions.types` |
| `EsiRequirements` | Datenklasse | ``flowaudit:esiAnforderungen`` bzw. Altattribute ``esiProfile``/``esiCoreRequirements``. | `extensions.types` |
| `EuActResolver` | Klasse | Syntaktische Auflösung von EU-Rechtsakten ohne Katalog. | `citations` |
| `Evidence` | Datenklasse | ``flowaudit:nachweis`` an Datenobjekten und Datenspeichern (Prüfpfad). | `extensions.types` |
| `Extensions` | Datenklasse | Alle FlowAudit-Angaben an einem BPMN-Element. | `extensions.element` |
| `FileStorage` | Klasse | Ablage: ``sammlung.json``, ``diagramme/<id>.bpmn``, ``freigaben/<id>/<version>.bpmn``. | `collection.storage` |
| `LegalBasis` | Datenklasse | Rechtsgrundlage; ``article``/``section``/``annex`` enthalten nur die Kennung. | `extensions.legal_basis` |
| `Marker` | Datenklasse | ``flowaudit:kennzeichen``: fachliches Kennzeichen (Overlay-Symbol). | `extensions.types` |
| `NeutralizationResult` | Datenklasse | Neutralisiertes XML und Bericht. | `neutralize` |
| `NormResolution` | Datenklasse | Ergebnis der Auflösung eines Normnamens. | `citations` |
| `NormResolver` | Protokoll | Port zur Normauflösung (z. B. :class:`auditcore_bpmn.legal.LegalSourcesNormResolver`). | `citations` |
| `OptionalDependencyError` | Ausnahme | Ein optionales Extra ist nicht installiert. | `errors` |
| `Profile` | Datenklasse | Profil: Kataloge und Regeln einer Förderperiode. | `profiles.model` |
| `ProfileRegistry` | Klasse | Mitgelieferte und von der Anwendung registrierte Profile. | `profiles.loader` |
| `Risk` | Datenklasse | ``flowaudit:risiko``; ``controls`` verweist auf ``flowaudit:kontrolle/@id``. | `extensions.types` |
| `Source` | Datenklasse | ``flowaudit:quelle``: Beleg der Darstellung (Handbuch, Interview, Durchlauftest …). | `extensions.types` |
| `Storage` | Protokoll | Port für Laden und Speichern; die Anwendung liefert eine Umsetzung (Datei, Datenbank, REST). | `collection.storage` |
| `Suggestion` | Datenklasse | Vorschlag für eine Erweiterung eines Elements samt Fundstelle im Text. | `enrichment` |
| `TargetActualComparison` | Datenklasse | Ergebnis des Soll/Ist-Abgleichs. | `comparison.target_actual` |
| `UnsafeXmlError` | Ausnahme | Abgewiesenes Dokument: DTD, Entitäten oder externe Verweise. | `errors` |
| `ValidationConfig` | Datenklasse | Einstellungen der Prüfung; alle Angaben optional. | `validation.context` |
| `ValidationIssue` | Datenklasse | Treffer einer Prüfregel an einem Element, am Diagramm oder an der Sammlung. | `validation.issues` |
| `ValidationReport` | Datenklasse | Ergebnis einer Prüfung mit Profil, Stichtag und Regelwerksversion. | `validation.issues` |
| `XmlTooLargeError` | Ausnahme | Das Dokument überschreitet die zulässige Größe. | `errors` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `analyze_bpmn` | Funktion | Kurzform wie im Original (``db_session`` → ``personnel_rate``). | `legacy.analyzer` |
| `apply_colors` | Funktion | Setzt ``bioc:fill``/``bioc:stroke`` und ``color:background-color``/``color:border-color``. | `comparison.coloring` |
| `apply_suggestions` | Funktion | Übernimmt ausgewählte Vorschläge; vorhandene Angaben bleiben, Doppeltes entfällt. | `enrichment` |
| `category_proposals` | Funktion | Vorschlag je KA aus Feststellungen und Prüfschritten (ausdrücklich nur Vorschlag). | `reports.findings` |
| `colors_from_markers` | Funktion | Füllung und Rand je Element aus farbgebenden Kennzeichen (Vorrang: ``COLOR_PRIORITY``). | `comparison.coloring` |
| `compare` | Funktion | Elementweiser Vergleich: hinzugefügt, entfallen, geändert (mit Feldern), unverändert. | `comparison.diff` |
| `compare_target_actual` | Funktion | Soll (Beschreibung des Verwaltungs- und Kontrollsystems) gegen Ist (Durchlauftest). | `comparison.target_actual` |
| `enrich` | Funktion | Füllt fehlende CELEX-/ELI-/URL-/Kurzbezeichnung; vorhandene Angaben bleiben. | `citations` |
| `find_citations` | Funktion | Normzitate in Freitext (z. B. ``bpmn:documentation``), überlappungsfrei, nach Position. | `citations` |
| `finding_list` | Funktion | Alle Prüffeststellungen an Elementen und am Diagramm. | `reports.findings` |
| `load_profile` | Funktion | Mitgeliefertes Profil; ohne ``version`` die neueste Fassung. | `profiles.loader` |
| `neutralize` | Funktion | Neutralisiert ein Diagramm; ``replacements`` ergänzt Namen, die die Anwendung kennt. | `neutralize` |
| `parse_bpmn` | Funktion | Liest BPMN-XML gehärtet in das Elementmodell. | `model.parse` |
| `parse_citation` | Funktion | Ein einzelnes Zitat strukturiert lesen; ohne eindeutigen Treffer bleibt es Freitext. | `citations` |
| `parse_xml` | Funktion | Parst BPMN-XML gehärtet. | `safe_xml` |
| `process_table` | Funktion | Prozessbeschreibung in Ablaufreihenfolge. | `reports.process_table` |
| `profile_from_dict` | Funktion | Profil aus JSON-Daten (Schema ``auditcore_bpmn.profile/1``). | `profiles.parsing` |
| `remove_extensions` | Funktion | Entfernt die genannten FlowAudit-Elemente (lokale XML-Namen) an einem Element. | `writer` |
| `risk_control_matrix` | Funktion | Risiken mit Bewertung, zugeordnete Kontrollen und Testergebnisse der Prüfschritte. | `reports.risk_control_matrix` |
| `serialize` | Funktion | Schreibt ein mit :func:`auditcore_bpmn.safe_xml.parse_xml` gelesenes Dokument zurück. | `serialize` |
| `set_diagram_info` | Funktion | Schreibt ``flowaudit:diagrammInfo`` (Schema 1.1) an das Hauptelement; genau ein Vorkommen. | `writer` |
| `set_extensions` | Funktion | Schreibt FlowAudit-Angaben an ein Element. | `writer` |
| `suggest` | Funktion | Alle Vorschläge (das Diagramm bleibt unverändert); Duplikate je Element entfallen. | `enrichment` |
| `validate` | Funktion | Prüft ein Diagramm (XML oder Modell) gegen alle registrierten Regeln. | `validation.engine` |
| `validate_bpmn_bva` | Funktion | Start/Ende vorhanden, IDs eindeutig, Flussreferenzen, max. 3 Gateway-Ausgänge, Namen. | `legacy.validation` |
| `walkthrough_status` | Funktion | Ergebnisse je Prüfschritt und nicht durchlaufene Aktivitäten. | `reports.walkthrough` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_bpmn.citations` | Normzitate erkennen und EU-Rechtsakte auflösen (CELEX, ELI, EUR-Lex-URL). |
| `auditcore_bpmn.collection` | Diagrammsammlung: Ordner, Tags, Reihenfolge, Verweise, Übersichten, Freigaben, Speicher. |
| `auditcore_bpmn.comparison` | Versionsvergleich, Soll/Ist-Abgleich und Einfärben von Diagrammen. |
| `auditcore_bpmn.enrichment` | Altbestand anreichern: Vorschläge aus Beschriftungen, Dokumentation und Farben. |
| `auditcore_bpmn.errors` | Fehlerklassen von auditcore_bpmn. |
| `auditcore_bpmn.extensions` | FlowAudit-Erweiterung (Schema 1.0/1.1): Datenklassen, Lesen und Schreiben. |
| `auditcore_bpmn.jsondata` | Geprüfter Zugriff auf eingelesene JSON-Daten (ohne ``Any``). |
| `auditcore_bpmn.legacy` | Legacy-treue Übernahmen aus audit_designer (FlowStat): Kennzahlen, BVA-Validierung, Berichte. |
| `auditcore_bpmn.legal` | Normauflösung mit ``auditcore_legal_sources`` (Extra ``legal``). |
| `auditcore_bpmn.model` | Elementmodell eines BPMN-2.0-Dokuments einschließlich FlowAudit-Erweiterungen. |
| `auditcore_bpmn.namespaces` | XML-Namensräume von BPMN 2.0 und der FlowAudit-Erweiterung. |
| `auditcore_bpmn.neutralize` | Neutralisieren: Export ohne Stellen-, Personen- und Befundbezug. |
| `auditcore_bpmn.optional` | Hilfe für optionale Extras. |
| `auditcore_bpmn.profiles` | Profile: gebündelte, versionierte Kataloge je Förderperiode. |
| `auditcore_bpmn.reports` | Berichtsexporte für Prüfbehörden: Prozesstabelle, RCM, Feststellungen, Durchlauftest, KA-Vorschlag. |
| `auditcore_bpmn.safe_xml` | Gehärtetes Parsen von BPMN-XML. |
| `auditcore_bpmn.serialize` | Zurückschreiben eines geparsten Dokuments ohne Bedeutungsverlust. |
| `auditcore_bpmn.templates` | – |
| `auditcore_bpmn.validation` | Prüfregeln mit stabilen IDs und zweisprachigen Meldungen. |
| `auditcore_bpmn.vocabulary` | Kontrollierte Vokabulare des FlowAudit-Schemas 1.1 (Deutsch und Englisch). |
| `auditcore_bpmn.writer` | Gezielte Änderungen an BPMN-Dokumenten (FlowAudit-Erweiterungen). |
<!-- api-overview:end -->

## Verbindliches Schema

[`docs/bpmn/flowaudit-schema-1.1.md`](../../docs/bpmn/flowaudit-schema-1.1.md)
im Repository und `src/auditcore_bpmn/schemas/flowaudit-1.1.xsd`.
JSON-Schemata: `diagram-collection-1`, `validation-report-1`, `profile-1`.
Namensraum unverändert `https://flowaudit.de/bpmn/schema/1.0`, Version im
Attribut `schemaVersion="1.1"` von `flowaudit:diagrammInfo`.

## Profile und Konfiguration

Profile sind benannte JSON-Dateien unter `src/auditcore_bpmn/profiles/data/`:
`foerderperiode-2021-2027` (Standard, wenn `diagrammInfo/@profil` leer ist) und
`foerderperiode-2014-2020`. Sie enthalten den KA-Katalog (1–15 nach Anhang XI
VO (EU) 2021/1060 bzw. 1–18 nach Anhang IV Delegierte VO (EU) Nr. 480/2014,
erzeugt aus den amtlichen EUR-Lex-Texten mit SHA-256 je Quelldatei,
`tools/build_profiles.py`), Rollen mit Periodenbindung, Fonds,
Artikelüberschriften und Regeln zur Funktionstrennung. Bewertungskriterien
stehen in keinem Rechtstext; die Anwendung speist sie mit
`Profile.with_assessment_criteria` ein. Eigene Profile: `load_profile(path)`,
`profile_from_dict`, `ProfileRegistry`; eigene Rollen über `custom_roles`.
`ValidationConfig` steuert Regelgruppen, Schweregrade und Stichtag.
Umgebungsvariable nur für Tests: `AUDITCORE_BPMN_LOCAL_FIXTURES` (lokale
Nutzerdiagramme, werden nicht mitgeliefert).

## Herkunft und Charakterisierung

Legacy-treu übernommen aus `janpow77/audit_designer@eff41a4c`
(`backend/app/modules/flowstat/services/bpmn_analyzer.py`,
`services/bpmn_export.py`, `api/bpmn.py` – `validate_bpmn_bva`); Pfade,
Symbole und Blob-SHAs stehen in `provenance.json`. Charakterisiert mit
`tools/capture_legacy.py` gegen die Originale (pandas 2.1.4, openpyxl 3.1.2,
reportlab 4.0.8): 95 Fälle (35 gezielt, 60 zufällig mit Seed 20260925) in
`tests/fixtures/legacy_observed.json`; Kennzahlen, ESI-Auszug, Personalkosten,
Excel-Zellen und PDF-Bytes stimmen überein. Schema 1.1, Prüfregeln, Profile,
Sammlung, Vergleich, Neutralisieren, Anreichern und Berichte sind
Neuimplementierungen; alle Testdiagramme sind synthetisch.

## Bewusste Verhaltensabweichungen

Eine Abweichung: `validate_bpmn_bva` weist ein XML mit `<!DOCTYPE …>` auch ohne
Entitäten ab (Original: erlaubt). Dazu deterministische Reihenfolge der
`unique_*`-Listen, Personalkosten über einen Port statt einer Datenbankabfrage
und Excel ohne pandas bei gleicher Ausgabe. Vollständig in
[`docs/behavior-changes.md`](docs/behavior-changes.md).

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Extras:
`defusedxml>=0.7.1` (`xml`), `openpyxl>=3.0.9,<4` (`excel`),
`reportlab>=3.6.12,<6` (`pdf`), `auditcore_legal_sources==0.1.5` (`legal`).
Bewusst keine Abhängigkeit: pandas, lxml, Pydantic, FastAPI.

## Sicherheit und Datenschutz

Kein Netzwerkzugriff. XML wird gehärtet gelesen: DTD, Entitäten und externe
Verweise werden abgewiesen, Größenlimit 5 000 000 Zeichen. Diagramme können
Namen, E-Mail-Adressen, Beträge und Feststellungen enthalten; `neutralize`
ersetzt Anzeigenamen durch Rollen, entfernt E-Mail, Beträge, Firmen- und
Personennamen, Kennnummern, Feststellungsbezüge sowie alle mit
`vertraulich="true"` markierten Elemente und berichtet jede Ersetzung. Die
Neutralisierung ist heuristisch und keine Anonymisierung im Sinne der DSGVO;
vor der Weitergabe ist eine Sichtprüfung nötig. Nutzerdiagramme sind nicht
im Paket; Testdaten sind synthetisch. `FileStorage` schreibt nur unterhalb
des angegebenen Verzeichnisses.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Der Rechteinhaber hat die Übernahme aus audit_designer unter
MIT freigegeben (`USER_AUTHORIZED_MIT`). Quellen und Erklärung: `NOTICE` und
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
