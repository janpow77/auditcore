---
name: refactoring
description: Refactoring in auditcore mit deterministischer Absicherung – betroffene Pakete bestimmen, Verhalten charakterisieren, ändern, verify und Befundbericht. Nutzen bei Umbenennen, Verschieben, Duplikate nach auditcore_common, Aufteilen zu großer Funktionen/Module.
---

# Refactoring mit Absicherung

1. **Umfang bestimmen:** `python scripts/ci_affected_packages.py --base origin/main` und
   `auditcore-codegate check --package <paket> --skip-mypy` (Ausgangswerte der Metriken).
2. **Öffentliche API festhalten:** Vor der Änderung nichts tun; der Befundbericht vergleicht
   später mit `--api-compare-ref origin/main`. API-Brüche nur mit neuer Version.
3. **Ändern** – mechanisch und klein. Duplikate nach `auditcore_common` verschieben und per
   Import ersetzen (exakter Pin im `pyproject.toml` des Pakets).
4. **Bei App-Repositorys:** `auditcore-refactor verify` (Charakterisierung im separaten
   Interpreter) vor und nach der Änderung.
5. **Prüfen:** `pytest -n auto --junitxml=j.xml` im Paket, dann
   `auditcore-codegate check --output gate.json` und
   `auditcore-codegate report --junit j.xml --gate gate.json --api-compare-ref origin/main`.
   Nur die dort genannten `datei:zeile`-Stellen öffnen.
6. **Baseline absenken**, wenn eine Metrik gesunken ist:
   `auditcore-codegate check --update-baseline` und die Änderung committen.
