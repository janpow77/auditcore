# Performance-Review: auditcore Compute und Dokumentauswertungen

Stand: 3. Oktober 2026. Technische Recherche und lokale Vergleichsmessung;
keine Messung eines Produktivrollouts. Arbeitsbasis der Vergleichsmessung:
`f1950dca` mit den vorbereiteten Compute-/Risk-Erweiterungen. Für den nun
beauftragten Gesamtrelease v0.6.0 sind die CI- und Runner-Korrekturen aus
PRs #224–226 integriert. Veröffentlichte Paketversionen werden nicht ersetzt.

Das Vorgehen ist tragfähig, aber ein allgemeines Optimum ist nicht belegt.
Die größten nachgewiesenen Gewinne kommen aus weniger wiederholter
Datenaufbereitung. Rechenkern, Datengröße, Startkosten und gemeinsame
Serverlast müssen getrennt betrachtet werden. Ein einheitliches
Parallelisierungsschema würde einige Auswertungen verlangsamen.

## Entscheidungen aus der Recherche

| Bereich | Befund und Entscheidung |
|---|---|
| Datenaufbereitung | Bestehende Spalten direkt weiterreichen. `DataFrame → records → Arrays` vermeiden, Beträge und Schlüssel einmal vorbereiten. Quoten nur einmal je wiederkehrendem Wert parsen. pandas zeigt ausdrücklich, dass Array-Zugriff die Kosten von Python-/Series-Zugriffen vermeidet. [pandas](https://pandas.pydata.org/docs/user_guide/enhancingperf.html) |
| Auswahl des Rechenkerns | NumPy, serielles und paralleles Numba pro Operation vergleichen. Einfachen Masken fehlen oft genügend Rechenoperationen, um Threadstart und Kompilierung auszugleichen. Die Numba-Beispiele sind ausdrücklich keine allgemeingültigen Leistungsvorgaben. [Numba Performance Tips](https://numba.readthedocs.io/en/stable/user/performance-tips.html) |
| Start und Cache | Ersten Prozessstart ohne Cache, Start mit Dateicache und wiederholte Aufrufe getrennt messen. Numba erkennt Änderungen importierter Helfer nicht durchgehend selbst; Paketfingerabdruck und unterschiedliche Schlüssel für serielle/parallele Varianten bleiben notwendig. Vorwärmen bei Prefork-Workern erst im Kindprozess; OpenMP ist unter Linux nicht forksicher. [Cache](https://numba.readthedocs.io/en/stable/developer/caching.html), [Threading](https://numba.readthedocs.io/en/stable/user/threading-layer.html) |
| Parallelitätsbudget | Workerprozesse × Rechenthreads ist gemeinsam mit API-, BLAS- und sonstiger Last zu budgetieren. Auf dem untersuchten Hetzner-Host sind vier CPUs verfügbar, die betroffenen Container haben keine eigenen CPU-Quoten. Startempfehlung für mehrere aktive Worker: ein Rechenthread je Worker; eine höhere Zahl benötigt einen gemessenen Vorteil unter gemeinsamer Last. [Numba Threading](https://numba.readthedocs.io/en/stable/user/threading-layer.html) |
| OCR-Gateway | Begrenzte gleichzeitige Seitenanfragen nur zusammen mit einem Budget über mehrere Dokumente und Worker einsetzen. Vorhandenen `auditcore_llm_client` mit HTTPX-Verbindungspool wiederverwenden. Ein HTTP-Verbindungslimit ist noch kein modellübergreifendes GPU-Arbeitsbudget. Der vorhandene ai-router besitzt bereits Anwendungsquoten; diese vor einer zusätzlichen Regel wiederverwenden und mit dem Inferenzdienst abgleichen. [HTTPX Async](https://www.python-httpx.org/async/), [Pool-Limits](https://www.python-httpx.org/advanced/resource-limits/) |
| PDF-Rasterung | PDFium darf selbst bei unterschiedlichen Dokumenten nicht gleichzeitig aus mehreren Threads aufgerufen werden. Rasterung bleibt seriell je Prozess; falls sie als Engpass gemessen wird, begrenzte Prozesse einsetzen. Eine speicherbegrenzte Übergabe gerasterter Seiten kann später nützlich sein, verlangt aber einen neuen Rasterizer-Vertrag. [PDFium](https://pypdfium2.readthedocs.io/en/stable/python_api.html) |
| Abbruch und Teilfehler | Seitenreihenfolge bleibt Eingabereihenfolge. Zurückgegebene Seitenfehler bleiben Teilfehler; bei Transportausnahme oder Abbruch müssen alle gestarteten Geschwisteranfragen abgebrochen und abgewartet werden. `gather` allein erledigt das bei einer Ausnahme nicht. Die Implementierung ergänzt deshalb explizite Bereinigung und bewahrt den bisherigen Ausnahmetyp. [asyncio](https://docs.python.org/3/library/asyncio-task.html) |
| Zwischenergebnisse | Dokumentwerte nur innerhalb eines synchronen Prüflaufs wiederverwenden; danach verwerfen. Typgetrennter, begrenzter LRU-Cache ausschließlich für unveränderliche Quoten. Keine pauschale Wiederverwendung kompletter Ergebnisse anhand einer Dokument-ID. [functools](https://docs.python.org/3/library/functools.html) |
| Lange und kurze Jobs | Bestehende Celery-Queues und Prefetch-Einstellungen prüfen. Unterschiedlich lange Aufgaben können getrennte Worker benötigen. `acks_late` setzt idempotente Tasks voraus und wird nicht pauschal als Beschleunigung eingeschaltet. audit_designer setzt bereits Prefetch 1 und vier Worker. [Celery](https://docs.celeryq.dev/en/stable/userguide/optimizing.html) |
| Messmethode | Wiederholte Prozessläufe, Verteilungen, Metadaten und Speicher statt allein bestem Einzelwert erfassen. `pyperf` unterstützt Aufwärmphase, Stabilitätsprüfung und Vergleich. Produktivnahe Lastmessung ergänzt p50/p95, Gesamtdurchsatz, Queue-Wartezeit und Fehlerquote. [pyperf](https://pyperf.readthedocs.io/en/stable/index.html) |

## Lokale Befunde

Python 3.12.3, NumPy 2.5.3, Numba 0.68.0. Acht Numba-Threads im
Vergleichslauf; das ist kein Vorschlag für den Produktivhost mit vier CPUs.
Synthetische Eingaben, gleiches Verfahren und gleiche Maschine. Mediane aus
fünf bzw. sieben Wiederholungen nach dem ersten Aufruf. Keine isolierte
Lasttestumgebung, daher sind kleine Unterschiede nicht belastbar.

| Gesamter gemessener Aufruf | Basis | Änderungen | Einordnung |
|---|---:|---:|---|
| Quoten, 500.000 Beträge, fünf wiederkehrende Quotentexte | 1.547,9 ms | 101,2 ms | etwa 15,3-fach schneller durch Wiederverwendung der Aufbereitung |
| BatchCheckService, 5.000 synthetische Belege | 402,2 ms | 306,7 ms | etwa 24 % weniger Laufzeit einschließlich Eingabeaufbereitung und Ergebnisaufbau; ohne HTTP/DB/OCR |
| Konstante Quote, 500.000 Beträge | 1,90 ms | 2,28 ms | kein Gewinn nachgewiesen; leichte Regression bzw. Messstreuung weiter abklären |
| OCR, 20 simulierte Seitenanfragen mit je 10 ms Wartezeit | 205,0 ms | 51,9 ms | vier gleichzeitige Anfragen; ausschließlich Simulation, kein Nachweis für GPU-Durchsatz |

Alle fünf verglichenen Ergebnis-Hashes einschließlich des nicht tabellierten
5.000-Zeilen-Quotenfalls stimmen überein. Die Batch-Daten wiederholen zehn
synthetische Muster; der Cachegewinn ist damit kein repräsentativer Mittelwert
über sämtliche möglichen Belegbestände. Fälle mit überwiegend eindeutigen
Werten müssen ebenfalls gemessen werden.

Ein gesonderter Vergleich der vorbereiteten Kerne liefert bei 100.000
Werten und acht Threads für eine Schwellenmaske etwa 19 µs mit NumPy,
26 µs seriell und 28 µs parallel mit Numba. Bei 500.000 Werten ist paralleles
Numba schneller. Für die aufwendigere Quotenberechnung zeigt sich der Nutzen
paralleler Verarbeitung schon früher. Deshalb verwendet die vorbereitete
Änderung für Schwellenmasken unter 250.000 Werten direkt NumPy. Die Grenze
ist ein konservativer Startwert zwischen den gemessenen Größen; ihr Optimum
auf dem Zielserver ist offen. Andere Kerne behalten zunächst ihre separat
zu prüfenden Grenzen.

Reproduzierbarer Einstieg: `scripts/benchmarks/compute_documents.py` mit
`--output DATEI`, beim neuen OCR-Pfad zusätzlich `--parallel-ocr` und zur
getrennten Messung vorbereiteter Quoten `--prepared-rates`. Für die
Basis können unveränderte Paketquellen über `PYTHONPATH` geladen werden.
Der erste dort ausgewiesene Aufruf ist kein kontrollierter Kaltstart: Import
und vorhandene Dateicaches sind nicht ausgeschaltet. Rohdaten der ersten
Messung liegen im lokalen `scratchpad/performance-before.json` und
`scratchpad/performance-after.json`; Kernauswahl im `scratchpad/dispatch-probe.json`.
Die vergleichbaren Mediane, Ergebnis-Hashes und Kernauswahl sind zusätzlich
im [Messprotokoll](compute-measurements-2026-10-03.json) versioniert.

Die Bibliothek bietet zusätzlich `PreparedRates`: Einmal validierte Quoten
lassen sich für mehrere gleich lange Betragsspalten wiederverwenden. Die
Vorbereitung wird getrennt gemessen und muss bei einmaliger Nutzung zur
Rechenzeit addiert werden. `LimitedRouterOcr` begrenzt die gleichzeitig
laufenden Anfragen mehrerer Dokumentjobs, wenn diese dieselbe Instanz in
einem Eventloop verwenden. Das ersetzt keine Grenze über mehrere Prozesse
oder Server. Die Seitenparallelität bleibt standardmäßig bei einer Anfrage.

## Verbindliche Ergänzungen für die Umsetzung

1. Mit dem fertigen Gesamtrelease abgleichen; bereits vorbereitete Risk-
   Spaltenauswertung und bestehende App-Komponenten übernehmen. Keine
   veröffentlichten Artefakte unter derselben Version ersetzen.
2. Pro Anwendung den vollständigen Auswertungspfad messen. Matrix:
   kleine/große Bestände, viele/wenige Wiederholungen, Kalt-/Warmstart,
   ein/mehrere gleichzeitige Jobs und tatsächliches Container-CPU-Budget.
3. Rechengrenzen je Kern festlegen. Threadbudget explizit konfigurieren;
   NumPy ohne JIT als vollwertige Betriebsvariante mitprüfen. Keine globalen
   Geschwindigkeitsversprechen aus einem einzelnen Kernel ableiten.
4. OCR erst oberhalb einer Anfrage je Dokument aktivieren, wenn das
   gemeinsame Gateway-Budget und die reale Inferenzkapazität nachgewiesen
   sind. Mit 1/2/4 Anfragen Durchsatz, p95, Queue, Fehler und Speicher messen.
   Serielle Rasterung beibehalten. GPU-Batching nur untersuchen, wenn das
   vorhandene Modell und der Dienst es unterstützen; keinen neuen
   Inferenzserver allein für diese Optimierung einführen.
5. Bibliotheks- und App-Tests vergleichen vollständige fachliche Ergebnisse
   samt Reihenfolge, Rundung, Grenzfällen, Fehlwerten und Exporten. Bestehende
   fachliche Profilversionen bleiben explizit gebunden; das neue Cent-Profil
   ist eine eigene fachliche Entscheidung.
6. Installierte Wheels und die tatsächlichen Produktivimages prüfen. Erst
   anschließend veröffentlichte Versions-/Hash-Pins aktualisieren und aktive
   Anwendungen einzeln ausrollen. Den bewusst abgeschalteten flowinvoice-
   Betrieb nicht durch die Performance-Umstellung starten.

Ein Wechsel auf GPU, verteilte Verarbeitung oder ein anderes DataFrame-System
ist durch die bisherigen Messungen nicht begründet. Der nächste größte
Hebel ist die durchgängige Wiederverwendung vorbereiteter Spalten in den
Anwendungen und ein passendes Gesamtbudget für CPU- und OCR-Arbeit.
