# auditcore_flow_agent

## Zweck

Dauerhafte Auftragswarteschlange, kapazitätsabhängige Rechnerwahl und überwachte
Prozessausführung als eigenständig installierbare Bibliothek für Flow-Agent.

Ein schneller, freier Rechner erhält bevorzugt passende
Arbeit. Unpassende, zurückgestellte oder fehlerhafte Aufträge halten unabhängige
Arbeit nicht auf.

## Installation

Aus dem Repository, Python ab 3.11:

```bash
python -m pip install ./packages/auditcore_common ./packages/auditcore_flow_agent
```

Paketname und Import: `auditcore_flow_agent`, Version `0.1.0`. Eine Veröffentlichung
im Paketindex ist ein eigener Release-Schritt. `[dev]` enthält Prüfwerkzeuge.

Nach Veröffentlichung stehen die üblichen Installationswege zur Verfügung;
die folgenden Release- und Hashangaben sind ausdrücklich Platzhalter:

```bash
python -m pip install 'auditcore_flow_agent==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
sudo apt-get install python3-auditcore-flow-agent
```

```text
auditcore_flow_agent @ https://github.com/janpow77/auditcore/releases/download/<release>/auditcore_flow_agent-0.1.0-py3-none-any.whl#sha256=<sha256>
```

Den tatsächlichen Hash dem Paketindex entnehmen; die APT-Quelle ist in der
[Paketbereitstellung](../../docs/deployment/package-feed.md) beschrieben.

## Schnellstart

```python
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from auditcore_flow_agent import Command, JobSpec, Node, Queue, State, execute

with TemporaryDirectory() as directory:
    queue = Queue(Path(directory) / "jobs.sqlite3")
    queue.publish_node(Node("fast", time.time(), 8, 32768, ("example",), speed=10))
    queue.enqueue(JobSpec("one", "video", "example", timeout_s=10))
    lease = queue.claim()
    assert lease is not None and lease.node_id == "fast"
    result = execute(queue, lease, Command((sys.executable, "-c", "print('fertig')")))
    assert result.returncode == 0
    assert queue.get("video", "one").state == State.SUCCEEDED
```

`execute` gehört auf den zugeteilten Rechner. Der lokale Aufruf im Beispiel ist
nur für einen Worker auf demselben Rechner gedacht.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_flow_agent.__all__` (20):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `Allocation` | Datenklasse | – | `resources` |
| `Command` | Datenklasse | – | `process` |
| `Gpu` | Datenklasse | – | `resources` |
| `Job` | Datenklasse | – | `models` |
| `JobSpec` | Datenklasse | – | `models` |
| `Lease` | Datenklasse | – | `models` |
| `LeaseClient` | Protokoll | – | `worker` |
| `Node` | Datenklasse | – | `resources` |
| `Outcome` | Datenklasse | – | `models` |
| `ProcessNotStopped` | Ausnahme | Prozessende ist nicht nachgewiesen; zugehörige Ressourcen bleiben gesperrt. | `process` |
| `ProcessResult` | Datenklasse | – | `process` |
| `Queue` | Klasse | Ein DB-Stand pro Koordinator; parallele Prozesse öffnen eigene Verbindungen. | `queue` |
| `ResourceRequest` | Datenklasse | – | `models` |
| `RetryPolicy` | Datenklasse | – | `models` |
| `SchedulerPolicy` | Datenklasse | – | `resources` |
| `State` | Aufzählung | – | `models` |
| `StopRequest` | Datenklasse | – | `models` |
| `choose_node` | Funktion | Weicher Rechnerwunsch, geladene Modelle, Leistung; stabile Kennungen lösen Gleichstand. | `resources` |
| `execute` | Funktion | Nur auf dem zugewiesenen Rechner ausführen; GPUs im App-Adapter verbindlich binden. | `worker` |
| `run_command` | Funktion | Programm ohne Shell ausführen; bei Fehlern immer die Prozessgruppe aufräumen. | `process` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_flow_agent.codec` | Versionierbare JSON-Ablage; keine ausführbaren Python-Objekte in der Warteschlange. |
| `auditcore_flow_agent.database` | SQLite-Adapter für einen zentralen Koordinator; Transaktionen enthalten keine Arbeit. |
| `auditcore_flow_agent.lifecycle` | Arbeitsberechtigungen, Fortschritt und bestätigte Ressourcenfreigabe. |
| `auditcore_flow_agent.models` | Unveränderliche Aufträge; technische Standardwerte sind pro Auftrag überschreibbar. |
| `auditcore_flow_agent.placement` | Atomare Auswahl; nicht ausführbare Aufträge werden übersprungen. |
| `auditcore_flow_agent.process` | POSIX-Prozesswächter mit absolutem Zeitlimit und begrenzter Ausgabepufferung. |
| `auditcore_flow_agent.queue` | Öffentliche, dauerhaft gespeicherte Koordinator-API. |
| `auditcore_flow_agent.resources` | Deterministische Platzierung nach Inventar, Reservierungen und Leistungshinweisen. |
| `auditcore_flow_agent.validation` | Validierung der technischen Auftragsverträge. |
| `auditcore_flow_agent.worker` | Anbindung des Prozesswächters an lokale oder per App-Adapter entfernte Leases. |
<!-- api-overview:end -->

## Profile und Konfiguration

`JobSpec` legt Fähigkeit, Ressourcen, Modell, Bereich (`scope`), Abhängigkeiten,
Priorität und Fristen fest. Abhängigkeiten müssen vorher im selben Bereich
angelegt sein; fehlende Abhängigkeiten und Zyklen werden dadurch abgewiesen.
Dieselbe Kennung mit demselben Vertrag ist idempotent. Ein geänderter Vertrag
braucht eine neue Auftragskennung.

`Node` meldet aktuell für diese Warteschlange angebotene CPU-/RAM-Kapazität,
GPUs mit freiem VRAM, installierte Modelle und einen positiven Geschwindigkeitswert.
Die zentrale Stelle setzt `observed_at` aus ihrer Uhr und aktualisiert Meldungen
regelmäßig. Die Standardfrist beträgt 60 Sekunden. Veraltete und in der Zukunft
liegende Meldungen sind nicht nutzbar. Bestehende Reservierungen werden zusätzlich
abgezogen; angebotene CPU-/RAM-Kapazität darf diese nicht bereits abziehen.

Die Auswahl prüft zuerst Zulässigkeit und Kapazität. Danach zählen ausdrücklich
bevorzugte Rechner, bereits geladene Modelle und die angegebene Geschwindigkeit.
Ohne ausdrückliche Präferenz oder geladenes Modell erhält der schnellere passende
Rechner die Arbeit; bei Belegung wird ein anderer passender Rechner verwendet.
`allowed_nodes` ist eine harte Einschränkung, `preferred_nodes` eine weiche
Bevorzugung. Die Werte sind Konfiguration, keine gemessenen Benchmarks.

Pro GPU läuft höchstens ein reservierter Auftrag. Mehrere GPUs eines Auftrags
werden atomar vergeben. Kleine Embedding-Anfragen sollten innerhalb eines
GPU-Workers gebündelt werden. Das Paket lädt selbst keine Modelle, verändert
keine Embeddings und entscheidet keine modellabhängigen Batchgrößen.
Für bessere Auslastung: Modellidentität im Auftrag angeben, geladene Modelle
melden, Batches begrenzen und den tatsächlichen Chunk-Fortschritt zurückmelden.

`SchedulerPolicy` begrenzt parallel aktive Aufträge je Bereich standardmäßig
auf zwei. Wartende Aufträge gewinnen alle 60 Sekunden einen Prioritätspunkt.
Dies reduziert Verhungern; Laufzeiten und Prioritäten müssen zur Anwendung passen.

## Fehler, Fristen und Wiederaufnahme

- `Outcome("permanent", ...)` beendet einen defekten Auftrag endgültig.
- `retryable` wiederholt mit begrenzter Versuchszahl und exponentieller Wartezeit.
  Standard: drei Versuche, fünf bis höchstens 300 Sekunden Wartezeit.
- `deferred` benötigt einen zukünftigen Zeitpunkt und verbraucht keinen Versuch.
  Diese Rückstellung ist für Kapazitätsengpässe, nicht für Inhaltsfehler gedacht.
- Fehlgeschlagene Voraussetzungen blockieren nur ihre tatsächlichen Nachfolger.
  Andere Bereiche, unabhängige Aufträge und andere Pipelinezweige laufen weiter.
- Beschädigte Auftragsverträge werden bei der Auswahl als fehlgeschlagen isoliert;
  das Ereignisprotokoll bleibt über `events` lesbar.
- Lebenszeichen verlängern weder das absolute Zeitlimit noch eine Fortschrittsfrist.
  Nur steigender messbarer Fortschritt erneuert die Fortschrittsfrist.
- Abgelaufene oder abgebrochene Arbeit behält ihre Ressourcen bis zum bestätigten
  Prozessende. `pending_stops()` liefert diese Fälle auch nach einem Neustart.
  Erst danach darf ein vertrauenswürdiger Worker `confirm_stopped(token)` aufrufen.
  Alte Tokens können keine Ergebnisse für einen neuen Versuch veröffentlichen.

SQLite mit WAL und Transaktionen sichert Zuteilung und Ressourcenreservierung
auch bei konkurrierenden Koordinatorprozessen. Die Datei gehört auf lokalen
Speicher. Entfernte Worker benötigen einen authentifizierten API-Adapter.
Eine ausgefallene Maschine bleibt bis zum nachgewiesenen Stillstand gesperrt;
die Sicherheit gegen Doppelbelegung geht hier vor automatischer Wiedervergabe.
Genau-einmal-Ausführung externer Seiteneffekte wird nicht zugesichert: Ergebnis-
und Dateiablage müssen die Anwendungen idempotent gestalten.

## Training und Nutzerarbeit

Donut-Training kann als eigener Auftrag mit Fähigkeit `train`, passender CPU-/RAM-
und GPU-Anforderung laufen. Bereits außerhalb der Warteschlange laufendes Training
benötigt `reserve(node_id, gpu_ids, reason=..., cpus=..., memory_mb=...)`.
Die Reservierung endet ausdrücklich über `release_reservation(token)` nach
Trainingsende. Es gibt keinen zeitgesteuerten Verlust einer Trainingsreservierung.

Wenn der Eigentümer einen Rechner benötigt: `drain_node(node_id)` sperrt neue
Zuteilungen und fordert das kontrollierte Ende aktiver Arbeit an. Der Worker
beendet den Prozess und bestätigt den Stillstand. Diese Unterbrechung verbraucht
keinen Fehlversuch. Für einen Trainingsstart auf einem belegten Rechner zuerst
drainen, das Ende bestätigen, die Trainingsressourcen reservieren und anschließend
eine neue Inventarmeldung veröffentlichen. Unreservierte Ressourcen sind dann
wieder verfügbar. Fortsetzen aus Checkpoints bleibt Aufgabe des Trainingsadapters.

## Integration und Grenzen

Hardwareerkennung, Eigentümeraktivität, HTTP-Authentifizierung, Modellserver und
Oberfläche bleiben in Flow-Agent. VideoArchivAssistent erzeugt bereichsgebundene
Aufträge und explizite Abhängigkeiten. Donut meldet Training und Fortschritt über
denselben Ressourcenvertrag. Die Anwendungen sind mit diesem Paket noch nicht
migriert; ihr laufendes Verhalten ändert sich durch das Paket allein nicht.

Der mitgelieferte Prozesswächter benötigt POSIX, startet ohne Shell und begrenzt
Ausgabe sowie Laufzeit. Er beendet die ganze Prozessgruppe einschließlich Kindern.
Programme dürfen sich nicht durch Daemonisierung von dieser Gruppe lösen.
Ein gestarteter Docker-Client ist kein Nachweis über das Ende seines Containers:
Container und Remote-Inferenz brauchen eigene Stop-/Statusadapter.
`tick`, Fortschrittsabfragen und entfernte `LeaseClient`-Aufrufe müssen kurze,
begrenzte Laufzeiten haben. CPU-/GPU-Kennungen ersetzen keine Betriebssystem-
Isolation: GPU-Bindung, cgroups und Containerlimits setzt der Anwendungsadapter.

## Herkunft und Charakterisierung

Neue Implementierung aus den Anforderungen an Flow-Agent, Videoverarbeitung und
Donut-Training. Keine Übernahme fremden Quelltexts. Vergleichbare Ansätze:
[HTCondor](https://github.com/htcondor/htcondor) für Ressourcenvergabe und
Unterbrechung, [GPUStack](https://github.com/gpustack/gpustack) für GPU-Platzierung,
[Celery](https://github.com/celery/celery) für Auftragsfristen und Wiederholungen
und [RQ](https://github.com/rq/rq) für isolierte Fehlerbehandlung.
Dies ist eine kleine einbettbare Bibliothek, kein Ersatz für sämtliche Funktionen
dieser Systeme. Altimplementierungsparität und optimale Hardwareauslastung werden
nicht behauptet. Die Tests verwenden synthetische Rechner und echte lokale
Testprozesse; sie benötigen keine GPU und kein Netzwerk.

## Bewusste Verhaltensabweichungen

Keine globale Sperre zwischen Transkription und Bildarbeit; nur ausdrückliche
Auftragsabhängigkeiten zählen. Keine unbegrenzten Fehlerwiederholungen. Keine
Freigabe einer möglicherweise noch arbeitenden GPU allein wegen Lease-Ablauf.

## Abhängigkeiten

Python `>=3.11`, `auditcore_common==0.2.0` und Python-Standardbibliothek.
Kein Webframework, Message-Broker, CUDA, PyTorch oder Plattformimport erforderlich.

## Sicherheit und Datenschutz

Der Koordinator führt keine Programme aus gespeicherten Payloads aus. Der
vertrauenswürdige Worker übersetzt einen Auftrag in eine erlaubte Argumentliste.
Datenbank, Payloads, Fehlertexte und Prozessausgabe können Anwendungsdaten
enthalten. Zugriff, Aufbewahrung und Geheimnisfilter bestimmt die Anwendung.

## Lizenz und Herkunftsnachweis

MIT gemäß [LICENSE](LICENSE), [NOTICE](NOTICE) und
[provenance.json](src/auditcore_flow_agent/provenance.json).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
