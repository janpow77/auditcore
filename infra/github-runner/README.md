# Lokale GitHub-Runner für auditcore und flow-agent

Die Runner werden mit `auditcore_runner` betrieben. Dieses Repo enthält keine zweite Runner-Implementierung: JIT-Registrierung, Einmal-Container, Workspace-Cleanup, GPU-Zuweisung, Cache-Volumes und Netzsperre bleiben im Paket. Die systemd-User-Units des Pakets sind der Produktionsstartweg. Der Docker-Socket ist ausschließlich für den vertrauenswürdigen Supervisor erreichbar, nie für einen Job-Container.

## Labels und Zuordnung

Es gibt genau ein `auditcore_runner`-Profil und einen gemeinsam genutzten Pool je physischem Host. Die Klassen `cpu`/`cpu-gross` und `gpu-16gb` sind Ressourcenklassen dieses Profils, keine zusätzlichen Repository-Pools. Standardjobs fordern `self-hosted`, `linux`, `x64` und `local-ci` an; `auditcore` bleibt ein Diagnose-Label:

- NUC: zusätzlich `nuc`, `always-on`.
- janpow-ai: zusätzlich `janpow-ai`.
- GPU-Aufträge: nur janpow-ai, zusätzlich `gpu-heavy` und VRAM-Klasse.

GitHub nimmt einen passenden freien Runner. Sind beide offline, bleibt der Job in der Queue. Der Fallback wird über die Repo-Variable `AUDITCORE_RUNNER` beziehungsweise `FLOW_AGENT_RUNNER` gesetzt, zum Beispiel `"ubuntu-latest"`; danach den PR-Workflow erneut starten. Fork-PRs und Dependabot werden unabhängig von der Variable auf GitHub Runnern gehalten.

## FlowAgent gemeinsam anbinden

`auditcore` (öffentlich) und `flow-agent` (privat) bleiben persönliche Repositories unter `janpow77`. Ein gemeinsamer Org-Scope und ein Repository-Transfer sind nicht erforderlich: `auditcore_runner` prüft beide Repositories, wählt für jeden freien JIT-Slot das Repo mit Queue-Bedarf und verschiebt freie Slots ohne laufende Jobs abzubrechen.

Beide Host-Profile enthalten `janpow77/flow-agent` als beobachtetes Ziel. Die Repo-Variablen `AUDITCORE_RUNNER` und `FLOW_AGENT_RUNNER` wählen dieselben `local-ci`-Pools. Fork-PRs und Dependabot bleiben auf gehosteten Runnern.

`FLOW_AGENT_RUNNER` ist bereits gesetzt. Die Workflow-Änderungen aktivieren das Routing, sobald sie in den FlowAgent-Zielbranch übernommen sind. Wenn beide lokalen Hosts aus sind, kann `workflow_dispatch` den Lauf manuell auf `ubuntu-latest` zwingen; ein fehlender Repo-Variablenwert fällt ebenfalls auf `ubuntu-latest` zurück.

## NUC in Betrieb nehmen

1. Das bestehende NUC-Profil ist auf `auditcore` ausgerichtet und beobachtet zusätzlich `flow-agent`.
2. `auditcore_runner` 0.1.4 ist installiert; sechs CPU-Worker laufen als ephemere JIT-Runner.
3. `auditcore-runner runner status` prüft Soll, Registrierungen und Cache-Status. Runner erscheinen repoübergreifend nach Queue-Bedarf.
4. Bei Änderungen zuerst Profil validieren und einen leerlaufenden Slot neu starten; laufende Jobs bleiben unangetastet.

Der aktuelle NUC-Rollout ist abgeschlossen. Das Profil-Backup liegt lokal auf der NUC unter `~/.config/auditcore-runner/profil.json.bak-multirepo-20261116`.

## janpow-ai und GPUs

1. Das vorhandene Profil für `auditcore` beobachtet `flow-agent`; es bleibt der einzige Pool dieses Hosts und bedient beide Repositories.
2. Nur die GPU-Klasse erhält `gpu-heavy`; sie wird über CDI genau einer GPU zugeordnet. Die interaktive GPU-Nutzung hat Vorrang.
3. Das erkannte System meldet eine RTX 5070 Ti 16 GB und RTX 5060 Ti 16 GB. GPU-Tests bleiben optional und laufen nicht als Voraussetzung der schnellen CPU-PR-Prüfung.
4. GPU-Passthrough, Firewall und Ressourcenlimits mit `auditcore-runner profil pruefen`, `auditcore-runner runner install --trockenlauf` und anschließend einem synthetischen GPU-Job prüfen.

## flow-agent anbinden

`flow-agent` ist privat; die geänderten Python-, Dashboard-, Desktop- und integrierten Jobs nutzen `FLOW_AGENT_RUNNER`, wenn die Workflow-Änderungen im Zielbranch aktiv sind. Forks und Dependabot bleiben gehostet. Der Docker-Build bleibt auf `ubuntu-24.04`, weil er BuildKit/GitHub Actions Cache benötigt und das vorhandene Job-Image keinen Docker-Socket bekommt. Die aktuellen Workflows starten keine PostgreSQL/pgvector-, Ollama-, OCR- oder Vision-Services; vorhandene KI-Steuerungstests sind lokale Unit-Tests. Ein GPU-Integrationstest-Job wird erst ergänzt, wenn es dafür einen echten, isolierbaren Testsatz gibt.

## MacBook M4 als Zusatz-Runner

Das MacBook Air M4 (10 CPU-Kerne, 16 GB RAM, ARM64) ist ein sinnvoller Zusatz für macOS-spezifische Checks und kurze Jobs. Es ist kein Ersatz für die Linux-Pools: dessen Runner können Jobs mit `linux`/`x64` nicht annehmen. Für Python-Tests mit hoher Parallelität, Docker-/PostgreSQL-Services und GPU-Tests bleiben NUC beziehungsweise `janpow-ai` zuständig.

Empfohlenes Zielprofil nach Einrichtung eines gemeinsamen Organisations-Scope:

- eigener macOS-Runner mit Labels `self-hosted`, `macOS`, `ARM64`, `mac-m4`;
- höchstens ein gleichzeitiger Job und zunächst 2–4 pytest-xdist-Worker;
- nur macOS-spezifische oder leichte Jobs explizit auf `mac-m4` routen (zum Beispiel macOS-Client- und Frontend-Smokes);
- keine Fork-PRs, Dependabot-Läufe oder Jobs mit produktiven Geheimnissen;
- eigener unprivilegierter macOS-Benutzer, isoliertes Arbeitsverzeichnis und Cleanup nach jedem Job.

Auf dem geprüften Mac waren Docker und `act` nicht installiert. `auditcore_runner` betreibt Linux-Runner in ephemeren Docker-Containern; FlowAgents Pool-Aktion steuert diese Linux-Worker und kann einen nativen macOS-GitHub-Runner noch nicht starten oder stoppen. Der Mac ist deshalb noch kein durch FlowAgent schaltbarer Runner.

Für den Mac wäre ein nativer, ephemerer launchd-Adapter nötig, der dieselbe repoübergreifende JIT-Routing-Logik verwendet. Bis dieser Adapter vorhanden ist, bleibt das MacBook ein optionales Entwicklungsgerät und übernimmt keine CI-Jobs.

## Auth und Rotation

Empfohlen ist eine GitHub App mit nur für die jeweiligen Repositories nötigen Runner-Administrationsrechten und lesendem Actions-Zugriff. Der private Schlüssel liegt getrennt von Git und Compose, Modus `0600`; kurzlebige JIT-Konfigurationen werden nach dem Job verworfen. Als Rückfall eignet sich ein fein granularer PAT nur für ein Repository und nur mit erforderlichen Runner-Rechten. Nach Rotation neue Registrierung testen und anschließend alte App-Schlüssel beziehungsweise PAT widerrufen.

## FlowAgent-Fernsteuerung: aktueller Betrieb

Der FlowAgent-Agent ist auf NUC und janpow-ai für Runner-Pool-Aktionen aktiviert. Beide schreiben in den Soll-Dateivertrag ihres `auditcore_runner`-Supervisors. Ausgangswerte sind NUC `cpu=6` und janpow-ai `cpu-gross=2`, `gpu-16gb=2`; diese Soll-Zahlen wurden bei der Aktivierung beibehalten. Die FlowAgent-Oberfläche kann alle gemeldeten Linux-Klassen befristet auf 0 setzen oder ihre Overrides wieder freigeben. Das beendet keine laufenden Jobs.

Diese Steuerung verwaltet die gemeinsamen NUC- und janpow-ai-Pools für beide Repositories. Die Repo-Variable ist gesetzt; FlowAgent-Jobs werden lokal ausgeführt, sobald die Workflow-Änderungen in den Zielbranch übernommen sind. Laufende Jobs werden beim Wechsel nicht beendet.

## Lokales Prüfen

`auditcore-runner lokal pr` ist der primäre lokale Prüfweg. Docker 29.1.3 und `act` 0.2.98 sind auf `janpow-ai` verfügbar; die Release-Prüfsumme wurde verifiziert. `.actrc` ordnet `self-hosted` einem lokalen Act-Image zu und setzt das Runner-Label als Testvariable. `act -l` listet die Workflows. GPU, JIT-Routing und echte GitHub-Runner-Gruppen werden damit nicht realistisch simuliert. `.secrets.example` enthält nur einen Platzhalter; echte Secrets gehören in eine lokale, ignorierte Datei.
