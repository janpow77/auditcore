# Spezifikation auditcore_bpmn

Stand: 26.09.2026, Paketversion 0.1.2. Charakterisierung: 95 am Original
(`janpow77/audit_designer@eff41a4c`, FlowStat-Module `bpmn_analyzer.py`,
`bpmn_export.py`, `validate_bpmn_bva`) beobachtete Fälle in
`tests/fixtures/legacy_observed.json` (`tools/capture_legacy.py`),
Abweichungen in `docs/behavior-changes.md`. Prüfregeln: `docs/rules.md`.
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Das Paket liest, prüft, vergleicht, neutralisiert und berichtet
BPMN-2.0-Prozessdiagramme mit der FlowAudit-Erweiterung (Schema 1.0/1.1). Es
dient Prüfbehörden und Programmbehörden aller Fonds mit geteilter
Mittelverwaltung, die Verwaltungs- und Kontrollsysteme als Prozesse
dokumentieren: Rechtsgrundlagen, Rollen, Kontrollen, Risiken, Prüfbezüge
(Kernanforderungen, Bewertungskriterien), Prüfschritte und Feststellungen.
Kataloge je Förderperiode kommen aus Profilen, nicht aus dem Code.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `parse_xml(data, *, max_size=5_000_000, backend="auto")` | BPMN-XML als `str`/`bytes` | `ParsedXml` (Wurzel, Namensräume, Prolog, Backend) | keine; DTD, Entitäten, externe Verweise verboten |
| `parse_bpmn(xml)` | wie oben | `BpmnDocument` mit allen Elementen (Pools, Lanes, Aktivitäten, Ereignisse, Gateways, Daten, Artefakte, Flüsse) und FlowAudit-Angaben | – |
| `serialize(parsed)` | mit `parse_xml` gelesenes Dokument | XML-Text mit den deklarierten Präfixen, ohne Bedeutungsverlust | – |
| `set_extensions`, `set_diagram_info`, `remove_extensions` | XML oder Dokument, Element-ID, Angaben | neues XML; strukturierte Rechtsgrundlagen erhalten ihre ausgeschriebene Normalform als Text | Eingabe bleibt unverändert (Arbeit auf einer Kopie) |
| `validate(source, config=None, *, reference_date=None, profile=None)` | XML oder Dokument, Einstellungen, Stichtag, Profil | `ValidationReport` (Treffer mit Regel-ID `BPMN-…`, Schweregrad, zweisprachiger Meldung) | – |
| `compare(old, new)` | zwei Fassungen | `Comparison`: je Element `hinzugefuegt`, `entfallen`, `geaendert` (mit Feldern) oder `unveraendert`; Synopse, Farben | – |
| `compare_target_actual(soll, ist)` | Beschreibung des Verwaltungs- und Kontrollsystems, Durchlauftest | Abgleich erfüllt/nicht erfüllt | – |
| `neutralize(source, *, profile=None, replacements=None, keep_originals=False)` | Diagramm, optional bekannte Namen | `NeutralizationResult` (XML, Bericht je Ersetzung) | – |
| `find_citations(text)`, `parse_citation(text)`, `enrich(basis, resolver=None)` | Freitext bzw. Rechtsgrundlage | Treffer mit Fundstelle bzw. strukturierte `LegalBasis`, CELEX/ELI/URL | ohne Resolver kein Netz; `[legal]` nutzt `auditcore_legal_sources` |
| `suggest`, `apply_suggestions` | Altbestand | Vorschläge; Übernahme nur ausgewählter Vorschläge | – |
| `process_table`, `risk_control_matrix`, `finding_list`, `walkthrough_status`, `category_proposals` | Diagramm | Berichtszeilen (CSV, MyST, Excel über Extra) | – |
| `DiagramCollection`, `FileStorage`, `Storage` | Sammlung von Diagrammen | Ordner, Tags, Verweise, Freigaben mit SHA-256 | `FileStorage` schreibt nur unterhalb des angegebenen Verzeichnisses |
| `load_profile`, `ProfileRegistry`, `profile_from_dict` | Profilkennung/-datei | `Profile` (KA-Katalog, Rollen, Fonds, Artikelüberschriften, Funktionstrennung) | liest mitgelieferte JSON-Profile |

Profile: `foerderperiode-2021-2027` (Standard; KA 1–15 nach Anhang XI VO (EU)
2021/1060) und `foerderperiode-2014-2020` (KA 1–18 nach Anhang IV Delegierte
VO (EU) Nr. 480/2014). Bewertungskriterien liefert die Anwendung.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Lesen–Schreiben ist nach dem ersten Rundlauf ein Fixpunkt: `serialize(parse_xml(serialize(parse_xml(x))))` ist bytegleich mit dem ersten Ergebnis; Elementkennungen, -typen und -namen bleiben gleich. | `test_i1_serialize_is_a_fixed_point_after_one_round_trip` |
| I2 | Der Vergleich eines Diagramms mit sich selbst enthält nur `unveraendert`. | `test_i2_comparison_with_itself_has_no_differences` |
| I3 | Der Vergleich ist spiegelbildlich: `hinzugefuegt` (alt→neu) = `entfallen` (neu→alt), `geaendert` gleich viele in beide Richtungen. | `test_i3_comparison_is_mirror_symmetric` |
| I4 | Neutralisieren entfernt E-Mail-Adressen der Form `lokal@domain.tld` und ist idempotent: ein zweiter Lauf ändert das Ergebnis nicht. | `test_i4_neutralization_is_idempotent_and_removes_mail_addresses` |
| I5 | Die Prüfung ist deterministisch (XML oder Modell, gleicher Stichtag → gleicher Bericht); ein Bericht ist gültig genau dann, wenn er keinen Treffer mit Schweregrad Fehler enthält; alle Regel-IDs beginnen mit `BPMN-`. | `test_i5_validation_is_deterministic_and_valid_means_no_errors` |
| I6 | Dokumente mit DTD oder Entitätsdeklaration werden mit `UnsafeXmlError`, Dokumente über `max_size` mit `XmlTooLargeError` abgewiesen. | `test_i6_hardened_parser_rejects_dtd_and_oversize` |
| I7 | Die ausgeschriebene Normalform einer strukturierten Rechtsgrundlage zu einer EU-Verordnung (Artikel, Absatz, Buchstabe) wird von `parse_citation` gleich strukturiert zurückgelesen; `normalized()` ist idempotent. Ausnahme: Befund B1. | `test_i7_structured_citation_round_trip`, `test_i7_befund_b1_declined_delegated_act` (xfail) |
| I8 | Treffer von `find_citations` sind nach Position sortiert, überlappen nicht und geben genau den Textausschnitt wieder. | `test_i8_found_citations_do_not_overlap` |
| I9 | Dieselben FlowAudit-Angaben zweimal zu schreiben ergibt dasselbe XML wie einmal; die Rechtsgrundlage trägt danach ihre Normalform als Text. | `test_i9_writing_extensions_is_idempotent` |

### Befunde aus den Eigenschaftstests

- **B1** – `parse_citation("Artikel 1 der Delegierten Verordnung (EU) Nr. 480/2014")`
  liest die Norm als „Delegierten Verordnung (EU) Nr. 480/2014“ (gebeugte
  Form). Die daraus erzeugte Normalform lautet „Artikel 1 Delegierten
  Verordnung …“ (ohne „der“) und stimmt nicht mehr mit dem Ausgangszitat
  überein. Nicht korrigiert; als erwarteter Fehlschlag festgehalten
  (`xfail(strict=True)`), damit eine Korrektur auffällt.
- **B2** – Richtlinien in der bis 2014 üblichen Zitierform „Jahr/Nummer/EU“
  („Artikel 1 der Richtlinie 2014/24/EU“) werden von `find_citations` nicht
  erkannt und bleiben in `parse_citation` Freitext; die Form „Richtlinie (EU)
  2019/1937“ wird erkannt. Nicht korrigiert, nur festgehalten.

## Fehlerfälle

| Eingabe | Ergebnis |
|---|---|
| kein `str`/`bytes` | `TypeError` |
| größer als `max_size` (Vorgabe 5 000 000 Zeichen) | `XmlTooLargeError` |
| DTD, Entitäten, externe Verweise | `UnsafeXmlError` (Unterklasse von `xml.etree.ElementTree.ParseError`) |
| nicht wohlgeformt, leer | `BpmnXmlError` |
| unbekanntes oder fehlerhaftes Profil | `CatalogError` |
| unzulässige Kennung, Integritätsverstoß der Sammlung, Überschreiben oder Fehlen eines freigegebenen Stands | `CollectionError` |
| Element-ID fehlt beim Schreiben, Dokument ohne Kollaboration/Prozess | `BpmnError` |
| fehlendes Extra (`xml`, `excel`, `pdf`, `legal`) bei Nutzung | `OptionalDependencyError` |
| fachliche Mängel im Diagramm | kein Fehler, sondern Treffer im `ValidationReport` |

## Abgrenzung

- Kein Editor, keine Oberfläche (dafür `@auditcore/bpmn-editor`,
  `@auditcore/bpmn-flowaudit`), keine Rechteprüfung, keine Datenbank; Speicher
  über den Port `Storage`.
- Die Neutralisierung ist heuristisch und keine Anonymisierung im Sinne der
  DSGVO; vor Weitergabe ist eine Sichtprüfung nötig.
- `category_proposals` schlägt Kategorien nur vor; die Bewertung der
  Kernanforderungen trifft die Prüfbehörde.
- Zitaterkennung: EU-Rechtsakte in der Form „Verordnung/Richtlinie (EU)
  Jahr/Nummer“ (auch Delegierte und Durchführungsverordnungen), Paragrafen
  nationaler Gesetze und Verwaltungsvorschriften; Richtlinien in der Altform
  „2014/24/EU“ bleiben Freitext (B2).
  Keine Auflösung über das Netz ohne ausdrücklichen Resolver.
- Bewertungskriterien stehen in keinem Rechtstext; die Anwendung speist sie ein.

## Bewusste Abweichungen vom Altverhalten

| Altverhalten | Gewolltes Verhalten | Nachweis |
|---|---|---|
| `validate_bpmn_bva` nimmt `<!DOCTYPE …>` ohne Entitäten hin | abgewiesen („BPMN-XML ist nicht wohlgeformt: …“) | `docs/behavior-changes.md`, I6 |
| `unique_owners`/`unique_departments`/`unique_systems` in zufälliger Reihenfolge (`list(set(...))`) | Reihenfolge des ersten Auftretens | `tests/test_legacy_characterization.py` |
| Personalkosten aus Datenbankabfrage (im Original stets leer) | Port `personnel_rate(grade)` | `tests/test_legacy_characterization.py` |
| Excel über pandas | openpyxl direkt, gleiche Zellen und Formate | `tests/test_legacy_characterization.py` |

Beibehaltene Altfunktionen (Legacy-Varianten; für neue Aufrufer gilt
`validate` mit den Regeln aus `docs/rules.md`):

| Legacy-Variante | Verhalten |
|---|---|
| `validate_bpmn_bva` | Altprüfung: Start/Ende, eindeutige IDs, Flussreferenzen, höchstens drei Gateway-Ausgänge, Namen – ohne Profile und ohne Schweregrade |
| `BpmnAnalyzer` | FlowStat-Kennzahlen aus Attributen (legacy-treu, einschließlich Rundung der Personalkosten) |
| `analyze_bpmn` | Kurzform wie im Original |
| `export_bpmn_to_excel` | Excelbericht im Altformat (Extra `excel`) |
| `export_bpmn_to_pdf` | PDF-Bericht im Altformat (Extra `pdf`) |
