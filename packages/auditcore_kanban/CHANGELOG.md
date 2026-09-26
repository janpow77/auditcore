# Changelog – auditcore_kanban

## 0.1.2 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1.

## 0.1.1 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. README nach der Vorlage.

## 0.1.0 – Erste Fassung

- Framework-freies Domänenmodell (Board, Spalte, Karte, Label, Freigabe,
  Übergangsregeln), Rang-Schlüssel ohne Umnummerieren, WIP-Limits
  (`block`/`warn`), gesperrte Spalten und feste Reihenfolge.
- Filter und Suche, Fristen-Zustand, Gruppierung nach Eigenschaft
  (Datenbankansicht), Statistik und Fortschritt.
- Rechte- und Freigabemodell als reine Logik (owner/edit/read, geerbte
  Freigaben), Validierung mit den Grenzen und Meldungen aus audit_designer.
- Reine Befehle, `BoardService` mit optimistischer Versionsprüfung,
  Ereignisprotokoll (Speicher, JSON Lines), Speicher-Port mit Arbeitsspeicher-
  und Dateisystem-Implementierung.
- JSON-Format `auditcore_kanban.board/1` mit JSON-Schema; Import/Export des
  audit_designer-Formats; Board-Vorlagen (7 aus audit_designer, cockpit).
- REST-Vertrag v1: framework-freier Handler, Starlette-App (Extra `ui`),
  FastAPI-Router (Extra `fastapi`).
- Charakterisierung: 77 ausgeführte Fälle des Originals, cockpit-Regeln per
  node ausgeführt; Paritätsfixtures für `@flowaudit/kanban-core`.
