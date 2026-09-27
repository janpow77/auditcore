# auditcore_runner

## Zweck

Ephemere self-hosted GitHub-Runner auf eigenen Rechnern – isoliert, dynamisch nach Last skaliert – und eine lokale Prüfbank mit einheitlichen, baseline-gefilterten Befunden.

Für Betreiber, die CI-Läufe auf eigene Hardware verlagern, und für Entwickler
und Agenten, die vor dem Push lokal im selben Image wie die CI prüfen wollen:
unveränderter Code wird nicht erneut geprüft (Cache je Werkzeug nach
Git-Inhalt), Autofixer laufen vor jedem Modell, der Rest geht als kompaktes
Aufgabenpaket an einen Agenten. Nicht enthalten: eigene Prüfregeln für
Quellcode (die liefern ruff, mypy, zizmor & Co.) und rechnerspezifische
Einstellungen – die stehen nur im lokalen Profil.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_runner \
  --index-url https://janpow77.github.io/auditcore/simple/
# oder als Werkzeug mit eigener Umgebung:
uv tool install auditcore_runner --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (0.1.0 ist noch nicht veröffentlicht;
Direkt-URL und `sha256` stehen nach dem Release im Index unter
`https://janpow77.github.io/auditcore/simple/auditcore-runner/`):

```text
auditcore_runner @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_runner-0.1.0-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-runner
```

Extras: `[workflows]` – Workflow-Prüfung `auditcore-runner workflows pruefen`
(PyYAML); `[github-app]` – Anmeldung als GitHub App (PyJWT mit cryptography);
`[dev]` – Test- und Prüfwerkzeuge.

Für den Runner-Betrieb zusätzlich: Linux mit systemd (User-Units), Docker,
`jq`, `gh` oder ein Token; GPUs nur NVIDIA (Container Toolkit). Neuer Rechner:

```bash
auditcore-runner profil erkennen --ziel <owner>/<repo> --speichern   # Hardware messen, Profil vorschlagen
auditcore-runner profil pruefen                                      # Validierung gegen diesen Rechner
auditcore-runner runner install --trockenlauf                        # zeigt Units, Image, Netz, Befehle
auditcore-runner runner install                                      # anwenden (laufende Jobs bleiben)
sudo bash ~/.config/auditcore-runner/root/firewall-installieren.sh   # einmalig: Netzsperre (root)
```

## Schnellstart

Profil aus Hardware-Fakten vorschlagen, prüfen und die reinen Regeln fragen,
wie viele Runner bei wenig freiem Speicher laufen dürfen:

```python
from auditcore_runner import Signals, decide, validate
from auditcore_runner.hardware import HostFacts
from auditcore_runner.propose import propose

facts = HostFacts("build-01", cpu_count=16, memory_mb=64 * 1024, swap_total_mb=8192, swap_used_mb=0)
profile = propose(facts, "owner/repo")
assert validate(profile, facts) == []

ruhig = decide(profile, Signals(cpu_count=16, load_1m=0.5, memory_available_mb=48 * 1024, swap_used_mb=0))
knapp = decide(profile, Signals(cpu_count=16, load_1m=0.5, memory_available_mb=2 * 1024, swap_used_mb=0))
assert ruhig.targets == {"cpu": 5}
assert knapp.targets == {"cpu": 0} and "cpu" in knapp.urgent
```

```pycon
>>> knapp.reasons["cpu"][-1]
'nur 2 GB RAM frei'
```

## API-Überblick

Die CLI `auditcore-runner` ist die Hauptschnittstelle (`--help` je Befehl);
JSON-API der lokalen Oberfläche, Status-Datei und Exit-Codes:
[docs/api.md](docs/api.md). Python-Einstieg:

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_runner.__all__` (10):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `ThermalState` | Datenklasse | Snapshot of the optional thermal/throttling source. | `regeln` |
| `Decision` | Datenklasse | – | `regeln` |
| `Problem` | Datenklasse | A finding; ``field`` is the path in the profile file. | `validation` |
| `Profile` | Datenklasse | – | `profile` |
| `RunnerClass` | Datenklasse | – | `profile` |
| `Signals` | Datenklasse | Everything the rules look at; ``None`` means "unknown", never "zero". | `regeln` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `decide` | Funktion | Target per enabled class; disabled classes get 0. | `regeln` |
| `smooth` | Funktion | Hysteresis: raise at once, lower only after the lower value held long enough. | `regeln` |
| `validate` | Funktion | All findings; an empty list means the profile may be applied. | `validation` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_runner.anwenden` | Check and apply a profile – shared by the CLI, the web API and external tools. |
| `auditcore_runner.auth_setup` | Which credentials a new profile uses (RUN-022): GitHub App, then fine-grained PAT, then ``gh``. |
| `auditcore_runner.autoscaler` | Built-in autoscaler for target source ``lokal``: signals → rules → pool file. |
| `auditcore_runner.backend` | How a runner instance obtains jobs – behind one interface. |
| `auditcore_runner.cli` | Command line ``auditcore-runner``. |
| `auditcore_runner.codemods` | Transactional ast-grep and LibCST codemods guarded by auditcore-refactor. |
| `auditcore_runner.commands_scaleset` | CLI group ``scaleset``: listener, JIT configuration and clean-up for the scale set backend. |
| `auditcore_runner.commands_tools` | CLI commands for checks: ``lokal``, ``befunde``, ``workflows``, ``image``, ``messen``, ``hook``. |
| `auditcore_runner.github` | Minimal GitHub REST client: credentials, runners and queued jobs per label. |
| `auditcore_runner.gpu` | Dynamic GPU assignment: a GPU runner takes whichever allowed card is free when a job starts. |
| `auditcore_runner.hardware` | Detect the host resources a runner profile is sized against. |
| `auditcore_runner.image` | Runner image: version check against GitHub's runner releases and rebuild. |
| `auditcore_runner.install` | Turn a profile into systemd user units, Docker network/image and root scripts. |
| `auditcore_runner.measure` | Repeatable baseline measurement: CI durations (via ``gh``) and LLM token usage. |
| `auditcore_runner.nachfrage` | Demand file: jobs waiting per class, written by the scale set listener or the local regulator. |
| `auditcore_runner.pool` | Target instance counts per class – the contract with an external regulator. |
| `auditcore_runner.profile` | Runner profile of one machine: classes, limits, target source and scaling rules. |
| `auditcore_runner.profile_io` | Profile file format (JSON, German keys) with schema versions and migration. |
| `auditcore_runner.profile_migration` | Migration of older profile files to the current schema (one step per version). |
| `auditcore_runner.profile_reader` | Typed, path-aware access to JSON objects of the profile file. |
| `auditcore_runner.propose` | Suggest runner classes and limits from measured hardware. |
| `auditcore_runner.regeln` | Pure scaling rules: signals + profile → target instances per class. |
| `auditcore_runner.scaleset` | Client for GitHub's runner scale set API (backend ``scaleset``). |
| `auditcore_runner.scaleset_listener` | Scale set listener: one long-poll session per runner class (backend ``scaleset``). |
| `auditcore_runner.signals` | Collect the local signals the scaling rules need. Every probe is failure-tolerant: an unavailable source yields ``None`` (unknown) rather than an optimistic value. |
| `auditcore_runner.status` | Machine status for humans, the web UI and external regulators (JSON file + Prometheus). |
| `auditcore_runner.validation` | One validation for CLI and web UI: a profile must be consistent and fit its machine. |
| `auditcore_runner.web` | Local web UI: status, settings of this machine and tool switches (stdlib HTTP server). |
| `auditcore_runner.werkzeuge` | Tool catalog, unified findings, check profiles and local execution. |
| `auditcore_runner.workflows` | Check GitHub workflow files for safe use of self-hosted runners. |
<!-- api-overview:end -->

## Profile und Konfiguration

- **Runner-Profil** `~/.config/auditcore-runner/profil.json` (Schema
  `auditcore-runner/profil/3`, ausgeben mit `auditcore-runner profil schema`):
  Ziel (Repository oder Organisation), Anmeldung (GitHub App empfohlen und
  Standard, sobald konfiguriert; sonst Token-Datei; `gh` nur für
  Einzelrechner), frei benennbare Klassen der Art `cpu` oder `gpu` mit Min/Max,
  CPU/RAM je Runner, erlaubte GPUs, Prioritäten, Netz, Soll-Quelle. Versioniert
  (`version`, `aenderung`) mit Migration älterer Fassungen. Neutrale Vorlagen
  mit den Standardklassen `cpu`, `cpu-gross`, `gpu-16gb`, `gpu-8gb`:
  `profil erkennen --vorlage workstation-2gpu|server-cpu`.
- **Backend** `jit` (Standard, REST-JIT je Job) oder `scaleset` (Runner-Scale-Set
  je Klasse mit Listener; `runs-on: <praefix>-<klasse>`), siehe
  [docs/backends.md](docs/backends.md). GPU-Zugriff per CDI.
- **Soll-Quelle** `statisch` (Maximum), `lokal` (eingebauter Autoskalierer
  `auditcore-runner regler`) oder `datei` (externer Regler, Vertrag
  `data/schemas/runner-pool.schema.json`).
- **Optionale Regeln**, standardmäßig aus: Thermik-Quelle mit Feldzuordnung,
  Vorrang interaktiver Nutzung, Volllast-Fenster.
- **Prüfprofile** `schnell`, `pr`, `voll`, `sicherheit`, `gui`, `gpu`, `fuell`
  über rund 45 fest gepinnte Werkzeuge im Runner-Image (Python, JS,
  Sicherheit, Doku, Struktur, GUI); Werkzeuge ohne passende Dateien entfallen.
  Im Repository anpassbar über `.auditcore-runner.toml` (Profile und Codemods,
  Schema `data/schemas/repo-konfiguration.schema.json`).
- **Verifizierte Codemods:** `codemod ast-grep <regel>` beziehungsweise
  `codemod libcst <modul>` arbeiten in einer Kopie und übernehmen Änderungen
  nur nach erfolgreichem `auditcore-refactor verify`; siehe
  [docs/werkzeuge.md](docs/werkzeuge.md#verifizierte-codemods).
- **Umgebungsvariablen:** `AUDITCORE_RUNNER_PROFILE` (Profilpfad),
  `XDG_CONFIG_HOME`/`XDG_STATE_HOME` (Ablage von Profil und Status).

Referenz: [docs/konfiguration.md](docs/konfiguration.md), Werkzeuge und
Prüfprofile: [docs/werkzeuge.md](docs/werkzeuge.md).

## Herkunft und Charakterisierung

Neuimplementierung in auditcore (`provenance.json`: `NEW_IMPLEMENTATION`).
Ausgangspunkt waren die Skripte unter `ci/runner/` im auditcore-Repository
(Commit `7b71f1c`); Supervisor und Image sind im Paket neu geschrieben,
`ci/runner/` bleibt als Kompatibilitätsschicht. Charakterisiert durch
Unit-Tests der reinen Regeln, der Profil-Validierung und -Migration, der
Parser mit Fixture-Ausgaben je Werkzeug (`tests/fixtures/`) und einen
Rauchtest des installierten Wheels (`tests/installed_smoke.py`). Das
Scale-Set-Backend setzt das Protokoll des MIT-lizenzierten Referenzclients
`actions/scaleset` in Python um (kein übernommener Code, Lizenz unter
`LICENSES/`) und ist gegen eine nachgebildete API getestet
(`tests/fake_scaleset.py`).

## Bewusste Verhaltensabweichungen

Keine – es gibt kein Vorgängerpaket. Gegenüber `ci/runner/` liegt die
JIT-Konfiguration als Datei im Container statt in einer Umgebungsvariable
(nicht in `docker inspect` sichtbar), und Einstellungen wirken ab dem nächsten
Job statt nach Neuinstallation.

## Abhängigkeiten

Python ≥ 3.11, keine Pflichtabhängigkeiten. Extras: `[workflows]` – PyYAML ≥ 6.0;
`[github-app]` – PyJWT[crypto] ≥ 2.8 (mit cryptography). Externe Programme
(Docker, systemd, `jq`, `gh`, `nvidia-smi`; für die Egress-Allowlist auf dem
Host `ipset` und `curl`) werden nur aufgerufen; die
Werkzeuge der Prüfbank stecken im Runner-Image (`data/Dockerfile`, Versionen
und Lizenzen in [THIRD_PARTY.md](THIRD_PARTY.md)).

## Sicherheit und Datenschutz

Ephemere Runner mit `--cap-drop ALL` und `no-new-privileges`, kein
Docker-Socket, eigenes Netz mit Sperre privater Netze und des Hosts
(optional Egress-Allowlist),
JIT-Konfiguration als Datei, Tokens nur als Dateipfad (nie im Profil, nie in
Ausgaben), Warnung bei unbekannten registrierten Runnern, Workflow-Prüfung auf
Fork- und Dependabot-Schutz. Netzzugriffe nur zur GitHub-API und zum
Actions-Dienst (`*.actions.githubusercontent.com`). Die lokale
Oberfläche schreibt nur über Loopback mit Kopfzeile. Personenbezogene Daten
verarbeitet das Paket nicht. Ausführlich: [docs/sicherheit.md](docs/sicherheit.md).

## Lizenz und Herkunftsnachweis

MIT, siehe [LICENSE](LICENSE) und [NOTICE](NOTICE); Herkunft in
[provenance.json](provenance.json), fremde Programme in
[THIRD_PARTY.md](THIRD_PARTY.md).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
