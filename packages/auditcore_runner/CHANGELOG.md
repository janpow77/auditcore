# Changelog – auditcore_runner

## Unreleased

- Oberfläche enthalten: `auditcore-runner ui` liefert die Runner-Konsole aus `@auditcore/ui` (Gruppe `runner`) als `data/web/runner-elements.js` aus; Paketseite ohne Platzhaltertext.
- Vollständiger Werkzeugkatalog im Runner-Image, fest gepinnt (Binärdateien mit
  SHA-256, Python und Node mit Lockfile, Dependabot pip/npm): pyrefly, Opengrep,
  osv-scanner v2, syft, grype, trivy (nur per Prüfsumme), vulture, deptry,
  import-linter, codespell, typos, mutmut, diff-cover, pytest-testmon/-split,
  jscpd, ast-grep, libcst, tsc, prettier, stylelint, vitest, knip, size-limit,
  Playwright mit Chromium und festen Schriften, axe, Lighthouse CI,
  markdownlint, lychee, betterleaks, reviewdog, prek.
- Parser je Werkzeug auf das einheitliche Befundmodell, getestet mit echten
  Ausgaben; Pfade relativ zum Repository; Netz nur für Werkzeuge, die es brauchen.
- Kette Autofix → Codemods (ast-grep, libcst, `[codemods]`) → Befunde;
  Aufgabenpaket mit Fix-Hinweisen je Werkzeug, geprüfter Kennung und
  Größengrenze.
- Prüfprofile mit neutraler Standardauswahl, Schema für `.auditcore-runner.toml`.
- Copyleft-Programme (Opengrep, codespell, axe-core, lightningcss) nur als
  separate Programme mit Lizenztext und Quellverweis unter `data/LICENSES/`.

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
- Backend `scaleset`: Python-Umsetzung des Protokolls von `actions/scaleset`
  (API-Version `6.0-preview`), Listener je Klasse mit Long-Poll und
  `DeleteMessage`, Soll = min(Kapazität, Minimum + zugewiesene Jobs),
  Nachfrage-Datei `nachfrage.json`; `scaleset lauschen|jit|entfernen|anzeigen|loeschen`.
- Warteschlange je Klasse im Status-JSON; der lokale Regler nutzt sie statt
  der REST-API, wenn der Listener läuft.
- GPU-Zugriff per CDI (`gpu_zugriff`), Reservierung der Karte beim Wählen.
- Egress-Allowlist im Runner-Netz (`netz.egress`), als erzeugtes root-Skript
  mit ipset und Zeitgeber.
- Überwachung unbekannter Runner: alle Seiten, Details mit passender Klasse,
  einmalige Warnung je neuer Registrierung, `runner status --streng`.
- Wiederverwendbarer Entscheidungs-Job (`workflow_call`) als Vorlage:
  `workflows vorlage runner-wahl`.
- `AUDITCORE_RUNNER_PROFILE` wird von allen Befehlen beachtet.
- Frei benennbare Klassen (RUN-011): Feld `klassen.<k>.art` (`cpu`/`gpu`)
  bestimmt das GPU-Verhalten; Profil-Schema 3 mit Migration aus Version 2;
  Soll-Datei und Schemas akzeptieren jeden gültigen Klassennamen.
- Anmeldung nach RUN-022: `profil erkennen` schlägt eine konfigurierte GitHub
  App vor, sonst ein Token, `gh` nur als Rückfall (`auth_begruendung`);
  Status-Feld `auth_art`.
- Zeitgeber `auditcore-runner-image.timer`: Runner-Image täglich prüfen und bei
  Bedarf neu bauen.
