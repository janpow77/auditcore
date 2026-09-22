# Mehrpaket-Verwaltung

Die installierte Plattform verwaltet Distributionen gemäß
[ADR-001](architecture/ADR-001-multi-package-monorepo.md) mit der bestehenden CLI:

```bash
auditcore-consolidate --state-dir .auditcore packages inventory .
auditcore-consolidate --state-dir .auditcore packages status .
```

`inventory` liest vorhandene Projekte, erstellt einen JSON-Katalog und speichert
einen unveränderlichen Snapshot mit Quellhash und beobachtetem Git-Commit.
Es werden keine Pakete erzeugt, installiert, importiert oder gebaut. Buildbackends,
`setup.py`, dynamische Versionsdateien und Anwendungsquellcode werden nicht ausgeführt.
Es gibt keine automatische Laufzeitabhängigkeit der Fachpakete von `auditcore`.

Ohne Konfiguration werden das Root-`pyproject.toml` und vorhandene
`packages/*/pyproject.toml` erfasst. Andere Layouts werden ausdrücklich konfiguriert.
Die Metadaten müssen einen statischen PEP-621-Projektnamen besitzen; eine dynamische
Version bleibt `UNKNOWN`. Noch nicht gebaute Quellprojekte gelten dadurch nicht
als installierbar nachgewiesen: `build_verification` bleibt `NOT_EXECUTED`.

## Prüffähige Konfiguration

Eine optionale Datei `auditcore-workspace.toml` im Workspace-Root kann enthalten:

```toml
[workspace]
version = 1
members = [".", "packages/*"]

[[package]]
path = "."
source_roots = ["src"]
applicability = "contexts/core.json"
# Optionale deklarierte Evidenz; keine automatische inhaltliche Bestätigung:
# provenance = "docs/provenance.json"
# consumers = ["owner/application"]
```

`members` akzeptiert relative konkrete Projektpfade sowie die besondere
Discovery-Angabe `packages/*`. `source_roots` sind relativ zum jeweiligen Projekt;
`applicability` und `provenance` sind relativ zum Workspace-Root.
Pfade außerhalb der erlaubten Wurzel und symbolisch verknüpfte Verzeichnisse werden
abgelehnt. Reguläre Dateialiasse innerhalb desselben Projekts sind erlaubt, etwa
`AUDITCORE_LASTENHEFT.md` → `docs/auditcore_lastenheft.md`. Ihr Zielpfad, Linkhash und
Inhaltshash werden gebunden. Externe, defekte und zyklische Dateilinks sowie Links
in eine andere Distribution oder den Werkzeugstate werden abgelehnt.
Doppelte Distributionsnamen werden nach Normalisierung von Groß-/Kleinschreibung,
Unterstrichen, Bindestrichen und Punkten erkannt. Konfigurationsfehler werden
nicht durch stillen Ausschluss eines Projekts verdeckt.

Ohne `source_roots` wird die vorhandene Setuptools-`packages.find.where`-Angabe
verwendet, andernfalls die `src`- bzw. flache Layoutkonvention. Die Herkunft dieser
Auswahl steht im Katalog. Das ist statische Discovery, keine Bestätigung des
tatsächlichen Wheel-Inhalts eines beliebigen Buildbackends.

## Erfasste Daten und Grenzen

Pro Projekt enthält der Katalog Pfad, Distributionsname, Version, Python-Vertrag,
Buildbackend, Quellwurzeln, Dateihashes, statisch sichtbare Module/Funktionen/Klassen,
deklarierte Abhängigkeiten und Extras sowie `requirements*.txt`-Dateien.
Die öffentliche API ist eine AST-Beobachtung. Dynamische Exporte, tatsächliche
Installationsinhalte und Laufzeitaufrufe sind damit nicht nachgewiesen.

Requirements werden als deklarierte Namen und unveränderte Vertragsangaben
erfasst; sensitive Angaben werden maskiert. Es findet weder eine Netzauflösung
noch eine vollständige PEP-508-Auswertung statt. Unbekannte Syntax, `-r`-Verweise
oder vergleichbare pip-Optionen bleiben zur Prüfung sichtbar. Environment-Marker
und Extras werden nicht ungeprüft als aktiv gewertet. Deklarierte interne
Abhängigkeiten erzeugen gerichtete Kanten. Zyklen sicher unbedingter
Runtime-Abhängigkeiten führen zu `FAIL`; bedingte Kanten bleiben `REVIEW_REQUIRED`.

Consumer-Konfiguration ist `DECLARED_NOT_VERIFIED`. Fehlende Consumer und
Herkunftsnachweise bleiben `UNKNOWN`. Herkunftsdateien werden referenziert und
gehasht; ihr Inhalt wird nicht automatisch zur bestätigten Provenienz erklärt.
Ein Kontext wird mit `ApplicabilityContext` validiert. Fehlende Werte bleiben
`UNKNOWN`; die Inventur ersetzt keine FrameworkPolicyProvider-Auswertung.
`policy_evaluation` bleibt deshalb `NOT_EXECUTED`, der Paketstatus
`REVIEW_REQUIRED`. Paketbezogene Quality-/Policy-Auswertung erfolgt separat.

## Persistenz und Status

Die Ablage liegt unter
`<state-dir>/workspaces/<workspace-identity>/snapshots/<snapshot-id>.json`.
Der Workspace-Schlüssel verhindert Kollisionen verschiedener Repository-Wurzeln.
Private Dateirechte und atomarer Austausch werden über die gemeinsame I/O-Schicht
verwendet. `current.json` verweist auf den zuletzt aufgenommenen Snapshot;
historische Snapshots werden nicht überschrieben.

Quellhashes binden Paketdateien und konfigurierte Nachweisdateien ein.
Andere Distributionswurzeln, virtuelle Umgebungen, Buildausgaben und Werkzeugstate
werden aus dem jeweiligen Pakethash ausgeschlossen. Änderungen an Quellcode,
Requirements, Kontext oder Workspace-Konfiguration machen den Snapshot veraltet.
Ein geänderter Git-Commit wird ebenfalls als neue Revision behandelt.

`status` liest den bisherigen Snapshot und vergleicht ihn mit den aktuellen
Eingaben, ohne die Evidenz zu erneuern:

| Status | Bedeutung | Exitcode |
|---|---|---|
| `CURRENT` | Quellhash und Revision stimmen überein; keine Freigabeaussage | 0 |
| `STALE` | Quellen, Metadaten, Kontext oder Revision haben sich geändert | 1 |
| `NOT_INVENTORIED` | Noch kein Snapshot für diesen Workspace vorhanden | 1 |
| `REVIEW_REQUIRED` | Inventur durchgeführt, weitergehende Nachweise offen | 0 |
| `FAIL` | Nachgewiesener unbedingter Runtime-Abhängigkeitszyklus | 1 |
| `NOT_EXECUTED` | Lesen oder Konfigurationsvalidierung fehlgeschlagen | 2 |

`inventory_status` im Statusbericht erhält den ursprünglichen Inventurbefund.
Ein aktueller Snapshot ist nicht automatisch ein bestandenes Quality Gate.
Validierungsfehler enthalten eine konkrete sichere `detail`-Diagnose; rohe
Dateipfade, Eingabewerte und mögliche Credentials werden nicht in Fehlertexte übernommen.
Die Python-Schnittstelle lautet `PackageWorkspace(root, state_dir)` mit
`inspect()` (nur lesen), `inventory()` (Snapshot persistieren) und `status()`.

Die Tests verwenden ausschließlich temporäre technische Beispielprojekte.
Diese Funktion erstellt oder migriert keine Fachbibliothek und keinen Consumer.
