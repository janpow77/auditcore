---
paths:
  - "tests/**"
  - "packages/*/tests/**"
---

# Tests

- Nur synthetische Daten und Fake-Provider; keine echten Dienste, kein Netz ohne Marker `network`.
- Tests müssen unter `pytest -n auto` isoliert laufen: keine geteilten Dateien außerhalb von
  `tmp_path`, keine Reihenfolgeabhängigkeit, stabile Parametrierungs-IDs (nie `id(obj)`).
- Marker: `slow` (> ~5 s), `gpu` (torch/Donut), `network`; unbekannte Marker scheitern
  (`--strict-markers`). Zeitlimit 120 s je Test.
- Charakterisierungs- und Golden-Tests nicht „reparieren“, indem die Erwartung angepasst wird;
  erst klären, ob das Verhalten sich ändern darf.
- Architekturtests (`test_architecture.py`) prüfen Importgrenzen per AST; neue Abhängigkeiten
  dort bewusst freigeben, nicht umgehen.
