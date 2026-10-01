# Changelog – auditcore_checklists

Alle wesentlichen Änderungen dieses Pakets werden in dieser Datei dokumentiert.

## 0.1.0 (2026-10-01)

### Neu
- Erstveröffentlichung von `auditcore_checklists` als eigenständige Fachbibliothek im auditcore-Monorepo.
- Framework-unabhängiger Baum-Vertrag (`ChecklistTree`, `ChecklistNode`, `NodeContent`, `NodeInternal`):
  - Unterstützung für Knotenarten `HEADING`, `QUESTION`, `DECISION` und `HINT`.
  - Unterstützung für Antworttypen `BOOLEAN`, `BOOLEAN_JN`, `CURRENCY`, `DATE`, `CUSTOM_ENUM`, `TEXT` und `MULTI_CHOICE`.
  - Baummanipulationen mit Validierung: Hinzufügen, Aktualisieren, Löschen (rekursiv), Verschieben mit Zykluserkennung und Verzweigungsprüfung.
  - Zweigunterstützung (`JA`/`NEIN`) für Entscheidungsunterknoten mit unabhängiger Sortierung.
- Antwort- und Auswertungsvertrag (`ChecklistAnswer`, `ExecutionState`, `EvaluationResult`):
  - Erfassung von Antworten, Kennzeichnung "Entfällt" (`is_na`), Nutzerbemerkungen und Belegverweisen.
  - Befundklassifikation (`keiner`, `formell`, `finanziell`) und Schweregrad (`hinweis`, `moderat`, `wesentlich`).
  - Baumtraversierung unter Berücksichtigung aktiver Entscheidungszweige.
  - Berechnung von Fortschrittsgrad, offenen Fragen und Befundstatistiken.
- Portabler Austausch- und Paketvertrag (`ChecklistPackage`, `export_package`, `import_package`, `validate_package`):
  - Kompatibel mit `audit-designer-checklist-package` Formatversion 1.
  - Deterministische Prüfsummenberechnung (`sha256`) über kanonische Strukturdaten.
  - Normalisierung von Rohbäumen und Altsicherungen (`full_backup`).
  - Unterstützung für mitgeführte Antwortset-Kategorien (`CategoryDefinition`, `CategoryItemDefinition`).
