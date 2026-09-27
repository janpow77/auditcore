# CLAUDE.md

Für dieses Repository gelten die Arbeitsregeln in [AGENTS.md](AGENTS.md).
Kurz das Wichtigste für Claude Code:

1. **Erst den Befundbericht lesen**, nicht den Code: Step-Summary bzw.
   `report.md` aus `code-quality-gate`/`domain-packages`, lokal mit
   `auditcore-codegate report`. Nur die dort genannten Stellen öffnen.
2. **Architektur-Doku nur gezielt** (ADR-001 für Paketgrenzen,
   `docs/quality/code-quality.md` für Maßstäbe). Nicht vorsorglich alle
   Pläne unter `docs/architecture/` lesen.
3. **Vor dem Commit:** `pytest -n auto`, `ruff check .`, `mypy src`,
   `auditcore-codegate check --skip-mypy`. Die Baseline darf nicht steigen.
4. **Kleine, logische Commits**, kein Force-Push, keine Umschreibung der Historie.
5. **Deutsch** in Doku, Meldungen und PR-Texten; Bezeichner englisch.
