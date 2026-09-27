# Prüfbank: Ausgangsmessung

Stand 27.09.2026, Zeitraum 14 Tage (13.–27.09.2026). Erhoben mit
`auditcore-runner messen --repo janpow77/auditcore --tage 14` (CI) und aus den
lokalen Claude-Code-Protokollen der Rechner, auf denen an auditcore gearbeitet
wurde. Die Werte sind der Vergleichsmaßstab für die Prüfbank (lokale Prüfung
vor dem Push, Cache nach Git-Inhalt, Autofix vor Modell, Aufgabenpakete).
Die Messung wird mit demselben Befehl wiederholt.

## CI-Dauer je Workflow

| Workflow | Läufe | Median min | p90 min | Anteil rot |
|---|---|---|---|---|
| code-quality-gate | 158 | 1,0 | 1,3 | 1 % |
| quality | 137 | 3,7 | 10,6 | 6 % |
| autofix | 111 | 2,9 | 10,4 | 0 % |
| domain-packages | 95 | 9,9 | 16,6 | 8 % |
| js-packages | 84 | 13,3 | 25,0 | 14 % |
| ci-ok | 82 | 11,5 | 20,2 | 23 % |
| update-pr-branches | 36 | 1,0 | 2,2 | 0 % |
| donut-train-image | 18 | 8,7 | 10,6 | 11 % |

Ausgewertet sind nur abgeschlossene Läufe ohne übersprungene oder abgebrochene;
die Liste ist auf die 1000 jüngsten Läufe begrenzt. `ci-ok` wartet auf alle
anderen Workflows eines Commits, seine Dauer entspricht der Wartezeit bis zum
grünen Haken.

## LLM-Token für auditcore

| Quelle | Antworten | Ausgabe | Cache gelesen | Cache geschrieben |
|---|---|---|---|---|
| Claude Code, Arbeitsverzeichnis auditcore | 3 859 | 3,7 M | 2 002 M | 26,5 M |

Frische Eingabe-Tokens fallen fast nicht an (unter 0,1 M); der Verbrauch
besteht aus Kontext, der je Antwort aus dem Cache erneut gelesen wird. Das ist
der Hebel der Prüfbank: kleinere, gezieltere Kontexte (Befundbericht statt
Quelltext, Aufgabenpakete mit exakten Stellen) statt vieler Runden über große
Dateien.
