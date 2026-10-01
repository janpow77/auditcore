# auditcore_checklists

## Zweck

Checklisten-Kern: hierarchische Prüfbäume, Antwort- und Auswertungsvertrag sowie portabler Paketaustausch für strukturierte Prüfungsabläufe.

Die Bibliothek stellt Fachanwendungen einen framework-freien Kern für Baumstrukturen, Entscheidungsverzweigungen, Befundbewertung und den Austausch vollständiger Checklisten-Pakete bereit. Nicht enthalten sind Datenbank-ORMs, Web-Endpunkte oder grafische Oberflächen.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_checklists==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256` stehen im
Index unter `https://janpow77.github.io/auditcore/simple/auditcore-checklists/`):

```text
auditcore_checklists @ https://github.com/janpow77/auditcore/releases/download/v0.1.0/auditcore_checklists-0.1.0-py3-none-any.whl#sha256=d3adb33f
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-checklists
```

Extras: `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_checklists import (
    AnswerType,
    ChecklistTree,
    ExecutionState,
    NodeType,
    evaluate_checklist,
)

tree = ChecklistTree.create_empty(title="Prüfung Vergabeverfahren")
tree, h1 = tree.add_node(
    node_type=NodeType.HEADING,
    parent_id=tree.root_id,
    title="1. Vorprüfung",
)
tree, q1 = tree.add_node(
    node_type=NodeType.QUESTION,
    parent_id=h1.id,
    title="Liegt ein wirksamer Beschluss vor?",
    answer_type=AnswerType.BOOLEAN,
)

state = ExecutionState().record_answer(node_id=q1.id, value=True)
result = evaluate_checklist(tree, state)
assert result.is_complete is True
assert result.total_findings == 0
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_checklists.__all__` (36):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `__version__` | Wert | – | `(Paketstamm)` |
| `PACKAGE_FORMAT` | Konstante | – | `package` |
| `FORMAT_VERSION` | Konstante | – | `package` |
| `ChecklistError` | Ausnahme | Basis-Ausnahme für alle fachlichen Fehler im Checklisten-Kern. | `errors` |
| `TreeStructureError` | Ausnahme | Verletzung der Baumstruktur-Regeln. | `errors` |
| `NodeNotFoundError` | Ausnahme | Knoten wurde im Baum nicht gefunden. | `errors` |
| `CycleDetectedError` | Ausnahme | Zyklische Abhängigkeit in der Knoten-Hierarchie erkannt. | `errors` |
| `InvalidBranchError` | Ausnahme | Ungültiger Zweig für einen Unterknoten. | `errors` |
| `PackageFormatError` | Ausnahme | Fehler beim Lesen oder Schreiben eines Checklisten-Pakets. | `errors` |
| `NodeType` | Aufzählung | Arten von Knoten im Checklisten-Baum. | `models` |
| `AnswerType` | Aufzählung | Unterstützte Antworttypen für Fragen und Entscheidungen. | `models` |
| `FindingType` | Aufzählung | Art des Prüfbefunds bei der Auswertung. | `models` |
| `FindingSeverity` | Aufzählung | Schweregrad eines Prüfbefunds. | `models` |
| `NodeStatus` | Aufzählung | Bearbeitungsstatus eines Knotens. | `models` |
| `HistoryAction` | Aufzählung | Arten von Änderungen in der Knotenhistorie. | `models` |
| `TeamNote` | Datenklasse | Team-Notiz bzw. Diskussionsbeitrag zu einem Knoten. | `models` |
| `NodeContent` | Datenklasse | Fachlicher Inhalt eines Baumknotens. | `models` |
| `NodeInternal` | Datenklasse | Interne Metadaten eines Knotens (nicht für Auswertungsberichte). | `models` |
| `ChecklistNode` | Datenklasse | Ein Knoten in der Checklisten-Hierarchie. | `models` |
| `CategoryDefinition` | Datenklasse | Wiederverwendbare Antwortset-Definition. | `models` |
| `CategoryItemDefinition` | Datenklasse | Option eines Antwortsets (Kategorie). | `models` |
| `ChecklistAnswer` | Datenklasse | Erfasste Antwort zu einer Prüffrage oder Entscheidung. | `models` |
| `TreeValidationFinding` | Datenklasse | Ergebnis einer Validierungsprüfung der Baumstruktur. | `models` |
| `ProjectMetadata` | Datenklasse | Metadaten des Checklisten-Projekts. | `models` |
| `VersionSnapshot` | Datenklasse | Schnappschuss einer Checklisten-Version. | `models` |
| `ChecklistTree` | Klasse | Verwaltet einen vollständigen, hierarchischen Prüfbaum. | `tree` |
| `ExecutionState` | Klasse | Hält und verwaltet den Erfassungsstand aller Antworten eines Prüflaufs. | `answers` |
| `EvaluationResult` | Datenklasse | Gesamtergebnis der Auswertung eines Checklisten-Prüflaufs. | `evaluation` |
| `FindingSummary` | Datenklasse | Zusammenfassender Prüfbefund zu einem beantworteten Knoten. | `evaluation` |
| `evaluate_checklist` | Funktion | Wertet die Checkliste basierend auf dem aktuellen Erfassungsstand aus. | `evaluation` |
| `compute_canonical_tree` | Funktion | Extrahiert den Strukturkern eines Baums ohne volatile Metadaten. | `package` |
| `compute_package_checksum` | Funktion | Berechnet die deterministische sha256-Prüfsumme des Strukturinhalts. | `package` |
| `export_package` | Funktion | Erzeugt ein portables Checklisten-Paket (.checklist.json). | `package` |
| `import_package` | Funktion | Liest und parst ein Checklisten-Paket in Domänenobjekte. | `package` |
| `normalize_package_payload` | Funktion | Führt native Pakete, Altsicherungen und Rohbäume in das Paketschema über. | `package` |
| `validate_package` | Funktion | Validiert die Konsistenz und Struktur eines Checklisten-Pakets. | `package` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_checklists.answers` | Antwortverwaltung und Zustandserfassung für die Checklisten-Ausführung. |
| `auditcore_checklists.errors` | Fehlerklassen und JSON-Typverträge für den Checklisten-Kern. |
| `auditcore_checklists.evaluation` | Auswertungslogik für Prüfpfade, Entscheidungsverzweigungen und Befunde. |
| `auditcore_checklists.models` | Domänenmodelle für Checklisten, Baumstrukturen, Antworten und Pakete. |
| `auditcore_checklists.package` | Portabler Checklisten-Paketaustausch (.checklist.json) kompatibel zu audit_designer. |
| `auditcore_checklists.tree` | Hierarchische Baumstrukturen für Checklisten mit Validierung und Navigation. |
| `auditcore_checklists.tree_serialization` | Serialisierung und Deserialisierung von Baumknoten und Inhalten. |
| `auditcore_checklists.tree_validation` | Strukturelle Validierungsprüfungen für Checklisten-Bäume. |
<!-- api-overview:end -->

## Profile und Konfiguration

Die Bibliothek benötigt keine externen Konfigurationsdateien oder Umgebungsvariablen. Alle Baumoperationen und Auswertungsregeln arbeiten zustandslos und deterministisch auf den übergebenen Datenstrukturen. Paketprüfsummen werden über kanonische JSON-Repräsentationen ermittelt.

## Herkunft und Charakterisierung

Hervorgegangen aus den bewährten Checklisten- und Baummodellen von `audit_designer` (insbesondere `TreeService` und `ChecklistPackageService`). Charakterisiert durch 23 automatisierte Tests, die Baumkonsistenz, Pfadführung nach Entscheidungszweigen sowie vollständige Formatparität mit dem `audit-designer-checklist-package`-Standard v1 nachweisen.

## Bewusste Verhaltensabweichungen

Keine Verhaltensabweichungen gegenüber dem Referenzformat aus `audit_designer`. Die Implementierung verzichtet bewusst auf relationale Datenbankkopplungen (SQLAlchemy) und Webframeworks (FastAPI), um eine universelle Wiederverwendung im gesamten Prüfökosystem zu ermöglichen.

## Abhängigkeiten

- Pflicht: `auditcore_common==0.2.0`, Python `>=3.11`
- Optional: `[dev]` – Test- und Prüfwerkzeuge (pytest, ruff, mypy, build).
- Bewusst keine Abhängigkeit: kein SQLAlchemy, kein FastAPI/Starlette, keine Datenbanktreiber.

## Sicherheit und Datenschutz

Verarbeitung erfolgt vollständig lokal im Speicher ohne Netzwerk- oder Dateisystemzugriffe. Beim Paketaustausch werden sensible interne Diskussionsbeiträge (Team-Notizen) auf Wunsch bereinigt. Zykluserkennung und Verzweigungsvalidierung verhindern Endlosschleifen und inkonsistente Baumzustände.

## Lizenz und Herkunftsnachweis

Veröffentlicht unter der MIT-Lizenz gemäß [`LICENSE`](LICENSE) und [`NOTICE`](NOTICE).
Dokumentation der Herkunft und Charakterisierung in [`provenance.json`](src/auditcore_checklists/provenance.json).

## Änderungen

Alle Änderungen sind im [Changelog](CHANGELOG.md) verzeichnet.
