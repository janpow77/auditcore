# Changelog – auditcore_runner

## 0.1.0 – Erste Fassung

- Versioniertes Runner-Profil (Schema 2, Migration aus Version 1) mit gemeinsamer
  Validierung für CLI und Oberfläche; neutrale Vorlagen `workstation-2gpu`,
  `server-cpu`; `profil erkennen|pruefen|anwenden|schema`, Konflikterkennung über
  `--erwartete-version`.
- Runner-Verwaltung: systemd-User-Units je Klasse, Supervisor mit JIT-Registrierung
  je Job (Backend `jit` hinter `RunnerBackend`), eigenes Docker-Netz mit
  root-Skript zur Netzsperre, Runner-Image mit gepinnten Werkzeugen,
  `image pruefen|aktualisieren` (Mindestversion, 30-Tage-Frist), vollständiges
  `uninstall`.
- Dynamik: Soll-Quellen `statisch`, `lokal` (Autoskalierer) und `datei` (externer
  Regler, JSON-Schema); reine Regeln in `regeln` mit Hysterese, Speichernot über
  Einlagerungsrate, Thermik-Quelle mit Feldzuordnung, Vorrang interaktiver
  Nutzung, Prioritäten; GPU-Karte je Job nach freiem VRAM, sofortiges Räumen bei
  Nutzer-Vorrang.
- Status-JSON, Prometheus-Metriken, Warnung bei unbekannten registrierten
  Runnern; lokale JSON-API (`ui`).
- Prüfbank: Werkzeugkatalog (ruff, mypy, pytest, gitleaks, eslint, zizmor,
  actionlint, codegate), einheitliche Befunde mit SARIF, Fingerabdruck und
  Baseline, Cache je Werkzeug nach Git-Inhalt, Prüfprofile mit
  `.auditcore-runner.toml`, Aufgabenpaket für headless-Agentenläufe,
  `workflows pruefen`, `messen`, prek-Hook.
