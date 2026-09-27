@AGENTS.md

## Nur für Claude Code

- Pfadregeln stehen in `.claude/rules/` (JS-Pakete, Tests), der Ablauf „Refactoring mit
  Absicherung“ als Skill in `.claude/skills/refactoring/`.
- Ein PostToolUse-Hook prüft jede bearbeitete Python-Datei mit ruff und mypy
  (`.claude/hooks/check_edited.py`); gemeldete Stellen sofort beheben.
