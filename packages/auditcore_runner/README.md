# auditcore_runner

## Zweck

Self-hosted GitHub-Actions-Runner auf eigenen Rechnern – sicher isoliert, dynamisch
nach Last skaliert – und eine lokale Prüfbank, die Werkzeuge wie ruff, mypy, pytest,
gitleaks, eslint, zizmor und actionlint ausführt und ihre Befunde einheitlich,
dedupliziert und gegen eine Baseline gefiltert liefert.

Ziel ist, GitHub-Läufe und LLM-Tokens zu sparen: Prüfungen laufen vor dem Push
lokal im selben Image wie in der CI, unveränderter Code wird nicht erneut
geprüft (Cache je Werkzeug nach Git-Inhalt), Autofixer laufen vor jedem Modell,
und was übrig bleibt, geht als kompaktes Aufgabenpaket mit exakten Stellen an
einen Agenten.

## Installation

Voraussetzungen: Linux mit systemd (User-Units), Docker, `gh` bzw. ein Token,
`jq`. GPUs nur NVIDIA (Container Toolkit).

```bash
python -m pip install auditcore_runner --index-url https://janpow77.github.io/auditcore/simple/
# oder als Werkzeug:
uv tool install auditcore_runner --index-url https://janpow77.github.io/auditcore/simple/
```

## Neuer Rechner in 5 Befehlen

```bash
auditcore-runner profil erkennen --ziel besitzer/repo --speichern   # Hardware messen, Profil vorschlagen
auditcore-runner profil pruefen                                      # Validierung gegen diesen Rechner
auditcore-runner runner install --trockenlauf                        # zeigt Units, Image, Netz, Befehle
auditcore-runner runner install                                      # anwenden (laufende Jobs bleiben)
sudo bash ~/.config/auditcore-runner/root/firewall-installieren.sh   # einmalig: Netzsperre (root)
```

Vorlagen statt Vorschlag: `profil erkennen --vorlage workstation-2gpu` bzw.
`--vorlage server-cpu` (an die erkannten Karten angepasst). Status:
`auditcore-runner runner status`, Oberfläche und JSON-API:
`auditcore-runner ui` (127.0.0.1:7860).

## Konzepte

- **Profil** (`~/.config/auditcore-runner/profil.json`, JSON-Schema:
  `auditcore-runner profil schema`): nur Grenzen – Klassen (`cpu`, `cpu-gross`,
  `gpu-16gb`, `gpu-8gb`) mit Min/Max, CPU/RAM je Runner, Labels, erlaubte
  GPUs mit VRAM-Bedarf, Prioritäten. Versioniert (`version`, `aenderung`),
  mit Migration älterer Fassungen. Referenz: [docs/konfiguration.md](docs/konfiguration.md).
- **Soll-Quelle**: `statisch` (Maximum), `lokal` (eingebauter Autoskalierer) oder
  `datei` (externer Regler schreibt die Soll-Datei, Vertrag
  `data/schemas/runner-pool.schema.json`). Die Regeln stehen als reine
  Funktionen in `auditcore_runner.regeln` und sind für externe Regler dieselben.
- **Dynamisch**: Last je Kern, freier RAM, Einlagerungsrate (nicht belegter
  Swap), Temperatur, optionale Thermik-Quelle, Warteschlange je Klasse,
  optionaler Vorrang interaktiver Nutzung; Hysterese beim Absenken. GPU-Runner
  wählen die Karte je Job (UUID, freies VRAM, Teilen mit Diensten); nutzt der
  Nutzer eine Karte, wird sie sofort geräumt.
- **Supervisor/Backend**: je Instanz eine JIT-Registrierung und ein frischer
  Container; hinter der Schnittstelle `RunnerBackend` austauschbar.
- **Prüfbank**: `auditcore-runner lokal <prüfprofil>`, `befunde`,
  `workflows pruefen`, Prüfprofile in `.auditcore-runner.toml`.
  Siehe [docs/werkzeuge.md](docs/werkzeuge.md).

## Sicherheit

Kurzfassung (ausführlich: [docs/sicherheit.md](docs/sicherheit.md)): ephemere
Runner, `--cap-drop ALL`, `no-new-privileges`, kein Docker-Socket, eigenes Netz
mit Sperre privater Netze und des Hosts, JIT-Konfiguration als Datei statt
Umgebungsvariable, Tokens nur als Dateipfad, Warnung bei unbekannten
registrierten Runnern, Workflow-Prüfung auf Fork-Schutz.

## Schnittstellen

JSON-API der lokalen Oberfläche, Status-Datei für externe Werkzeuge,
maschinenlesbare CLI: [docs/api.md](docs/api.md).

## Lizenz

MIT, Teil von auditcore. Externe Werkzeuge im Runner-Image: [THIRD_PARTY.md](THIRD_PARTY.md).
