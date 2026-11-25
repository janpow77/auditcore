# Changelog – auditcore_runner

## 0.1.11 – 2026-11-25

- CUDA-Prozesse eines laufenden GPU-Runners werden anhand der Host-PID dem Container zugeordnet.
- Die gebündelte Oberfläche (`data/web/runner-elements.js`) enthält die Stile von `@auditcore/ui-core` 0.5.0 (zusätzlich „PDF schwärzen“).

## 0.1.10 – 2026-11-25

- Überwachung der Runner beginnt auch dann, wenn Docker den Container beim ersten Abruf noch anlegt.

## 0.1.9 – 2026-11-25

- Das Linux-Image enthält FFmpeg und FFprobe für Medienprüfungen im lokalen Pool.

## 0.1.8 – 2026-11-25

- Bei externem Sollwert meldet der JIT-Status die wartenden Jobs pro Klasse aus demselben Cache wie die Repo-Auswahl an FlowAgent.

## 0.1.7 – 2026-11-25

- Repo-Routing erfasst wartende Jobs in laufenden Workflows. Alle Runnerklassen teilen sich einen nach Repoanzahl bemessenen Queue-Cache.

## 0.1.6 – 2026-11-25

- Das JIT-Registrierungsziel bleibt für die Überwachung und Abmeldung eines Runner-Slots erhalten. Freie Runner können dadurch das Repository wechseln und FlowAgent-Sollwerte umsetzen.

## 0.1.5 – 2026-11-16

- Runner-Image enthält die Tauri-v2-Buildabhängigkeiten und `en_US.UTF-8`;
  dadurch laufen der Desktop-Build und Bash-Integrationstests ohne
  Paketinstallation mit `sudo` im ephemeren Jobcontainer.
- Installiert Rust 1.98.1 mit `clippy` und `rustfmt` aus einem Digest-gepinnten
  Image und speichert Cargo-Abhängigkeiten in einem NVMe-Volume je Runner-Instanz.
- Exitcode 127 in einem Shell-Befehl (`sh`, `bash`, `dash`, auch `/bin/sh`,
  `bash -lc`, `sh -euc`) meldet „Programm im Befehl nicht gefunden
  (Exitcode 127)“, statt die Shell als fehlend zu melden, mit der
  aussagekräftigsten Zeile: einer mit „not found“, „no such file“ oder „nicht
  gefunden“, sonst der letzten; Docker-Zeilen „Run '…“ werden übersprungen,
  ohne stderr gilt stdout (#330).
- Runner-Image: Playwright lädt Chromium und FFmpeg beim Bau über einen
  lokalen Proxy (`werkzeuge/playwright_download_proxy.py`), der nur die
  Playwright-Pfade auf die offiziellen Downloadquellen umschreibt; der Bau
  wartet, bis der Proxy erreichbar ist (#335).

## 0.1.4 – 2026-11-16

- Supervisor-CLI-Aufruf auf Hosts ohne `~/.local/bin` im systemd-PATH korrigiert;
  installiertes Console-Script wird relativ zum aktiven Python-Interpreter gesucht.
- Regressionstests für explizite und nicht verfügbare Console-Script-Pfade ergänzt.

## 0.1.3 – 2026-11-16

- Repo-Runner-Pools können mehrere persönliche Repositories bedienen. JIT-Slots
  wählen anhand passender wartender Jobs ein Ziel, freie Slots verteilen sich
  stabil und wechseln bei Bedarf ohne laufende Jobs abzubrechen.
- Runner-Status und Warteschlangen werden über alle Repo-Ziele zusammengeführt;
  das Scale-Set-Backend weist Mehrrepo-Profile zurück.

## 0.1.2 – 2026-11-04

- `befunde`: Der Pfad des letzten Laufs wird beidseitig mit `resolve()`
  verglichen; ein Lauf über einen Symlink oder relativen Pfad wird nicht mehr
  als fremdes Repository abgewiesen.

## 0.1.1 – 2026-10-11

- Nichts geprüft ist rot: Ein JUnit-Bericht ohne ausgeführten Testfall (fehlt,
  leer oder alles übersprungen) ergibt Status und Befund `nichts_geprueft` mit
  der Skip-Meldung statt „ok“; die Baseline blendet ihn nicht aus. Das
  Ergebnisdokument trägt `gesamt` (`gruen`/`rot`) und `probleme`; `lokal` und
  `befunde` enden bei Rot (auch bei `fehlt`, `fehler`, `zeitlimit`, `unlesbar`)
  mit Exitcode 1. Neuer Profilschalter `leer_erlaubt` (Standard aus), neue Route
  `GET /api/ergebnis`. Alte Berichtsdateien werden vor jedem Lauf gelöscht,
  überschriebene `befehl` nicht mehr zwischengespeichert, unlesbares JUnit-XML
  ergibt `unlesbar` statt eines Tracebacks.
- Prüfprofile dürfen Werkzeuge ohne Katalogeintrag mit eigenem `befehl` deklarieren
  (etwa `compose` mit `docker compose config --quiet`): Exitcode als Befund, mit
  `{ausgabe}` JUnit-Bericht, ohne Cache. Unbekannte Werkzeuge ohne `befehl` melden
  Status `unbekannt` und Exitcode 2 statt eines Tracebacks oder stillen Auslassens.
- Oberfläche: Klassen hinzufügen/umbenennen, Art je Klasse, Anmeldeart im Status (Bündel neu gebaut).
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
