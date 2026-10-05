# auditcore_officebank

## Zweck

Prüfbank für Office-Makroprojekte (Excel, Access, Word): Konfiguration, Gates, Steuerung einer Windows-VM, Build aus Commits, Abnahme gegen Sollwerte und datenfreie Lieferpakete.

Zielgruppe sind Projekte mit VBA-Quelltext im Git-Repo, die statisch geprüft,
nativ in einer VM gebaut und gegen unabhängige Sollwerte abgenommen werden.
Fassung 0.1.0 ist das **Gerüst (Etappe 0)**: Konfiguration, Ausgabe-Maskierung,
Gast-Schnittstelle mit Fake und CLI-Rahmen. Gates, VM, Office-Automation, Build,
Abnahme, Lieferung und SQL-Server-Dienst folgen in den Etappen 1–6 laut
[Plan](../../docs/projekt/20261005_Plan_auditcore_officebank_0.1.md).
Fachlogik, Sollwerte, Projektnamen und echte Daten gehören nicht in dieses Paket.

## Installation

Aus dem Repository, Python ab 3.11:

```bash
python -m pip install ./packages/auditcore_officebank
```

Paketname und Import: `auditcore_officebank`, Version `0.1.0`. Die Fassung ist
noch nicht veröffentlicht; die folgenden Release- und Hashangaben sind
ausdrücklich Platzhalter:

```bash
python -m pip install 'auditcore_officebank==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
sudo apt-get install python3-auditcore-officebank
```

```text
auditcore_officebank @ https://github.com/janpow77/auditcore/releases/download/<release>/auditcore_officebank-0.1.0-py3-none-any.whl#sha256=<sha256>
```

Den tatsächlichen Hash dem Paketindex entnehmen; die APT-Quelle ist in der
[Paketbereitstellung](../../docs/deployment/package-feed.md) beschrieben.

Extras: `[docx]` – Anleitungen und Abnahmeberichte im Office-Design über
python-docx (ab Etappe 3); `[xlsx]` – lesender Zugriff auf Ergebnismappen über
openpyxl (ab Etappe 4, nie schreibend); `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from auditcore_officebank import load_project, mask_secrets

with TemporaryDirectory() as directory:
    root = Path(directory)
    (root / ".officebank.toml").write_text(
        'schema = "auditcore-officebank/projekt/1"\n'
        '[projekt]\nkuerzel = "P-DEMO"\nhost = "access"\n'
        '[module]\nreihenfolge = ["modBasis", "modAuswertung"]\n',
        encoding="utf-8",
    )
    project = load_project(root)
    assert project.host == "access"
    assert project.modules == ("modBasis", "modAuswertung")
    assert project.lint_profile == "access"

masked = mask_secrets("Server=db;Uid=app;Pwd=geheim;")
assert masked == "Server=db;Uid=app;Pwd=****;"
```

```pycon
>>> from auditcore_officebank import stage_of
>>> stage_of("vm").number
2
```

Auf der Kommandozeile:

```bash
auditcore-officebank status
auditcore-officebank konfig pruefen --rechner --projekt .
auditcore-officebank konfig schema projekt
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_officebank.__all__` (19):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `HOST_SCHEMA` | Konstante | – | `config` |
| `PROJECT_SCHEMA` | Konstante | – | `config` |
| `STAGES` | Konstante | – | `stages` |
| `ConfigError` | Ausnahme | Rechnerprofil oder Projektdatei ist unlesbar, unvollständig oder ungültig. | `errors` |
| `Endpoint` | Datenklasse | MCP-Endpunkt mit Adresse und Verweis auf das Token. | `config` |
| `HostProfile` | Datenklasse | Rechnerabhängige Einstellungen; gehört nie in ein Projekt-Repo. | `config` |
| `OfficebankError` | Ausnahme | Basisklasse aller erwarteten Fehler der officebank. | `errors` |
| `ProjectConfig` | Datenklasse | Projektangaben aus ``.officebank.toml``. | `config` |
| `SecretRef` | Datenklasse | Name eines Secrets in Umgebung oder Schlüsselbund, nie der Wert. | `config` |
| `Stage` | Datenklasse | Eine Etappe mit Nummer, Titel und den CLI-Gruppen, die sie liefert. | `stages` |
| `StageNotImplemented` | Ausnahme | Der Baustein ist geplant, gehört aber zu einer späteren Etappe. | `errors` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `load_host_profile` | Funktion | Liest das Rechnerprofil (Standardpfad im Benutzerverzeichnis). | `config` |
| `load_project` | Funktion | Liest ``.officebank.toml``; ``path`` darf die Datei oder ihr Ordner sein. | `config` |
| `mask_secrets` | Funktion | Gibt ``text`` mit maskierten Secrets zurück. | `masking` |
| `parse_host_profile` | Funktion | Prüft ein eingelesenes Rechnerprofil und gibt es typisiert zurück. | `config` |
| `parse_project` | Funktion | Prüft eine eingelesene Projektdatei; Pfade werden relativ zu ``root`` gelesen. | `config` |
| `require` | Funktion | Bricht mit :class:`StageNotImplemented` ab, wenn die Gruppe noch fehlt. | `stages` |
| `stage_of` | Funktion | Etappe einer CLI-Gruppe; ``KeyError`` bei unbekannter Gruppe. | `stages` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_officebank.acceptance` | Abnahme gegen unabhängige Sollwerte (Etappe 4, Plan Kap. 2.7). |
| `auditcore_officebank.builder` | Inkrementeller Build nur aus committeten Ständen (Etappe 4, Plan Kap. 2.6). |
| `auditcore_officebank.cli` | Kommandozeile ``auditcore-officebank`` (Befehle deutsch, wie beim Runner). |
| `auditcore_officebank.config` | Rechnerprofil und Projektdatei (``.officebank.toml``) mit Schemaversion. |
| `auditcore_officebank.delivery` | Datenfreies Lieferpaket, Schwärzung und Upload (Etappe 4, Plan Kap. 2.9). |
| `auditcore_officebank.errors` | Fehlerklassen der officebank; Meldungen sind deutsch und enthalten keine Secrets. |
| `auditcore_officebank.gates` | Gates vor jeder Weitergabe von Code: ascii, lint-vba, lint-sql, datenschutz, mcp. |
| `auditcore_officebank.masking` | Zentraler Ausgabefilter: maskiert Secrets, bevor Text ausgegeben oder abgelegt wird. |
| `auditcore_officebank.mssql` | Generischer SQL-Server-Testdienst im Container (Etappe 5, Plan Kap. 2.5). |
| `auditcore_officebank.office` | Office-Automation für Excel (Windows und macOS), Access und Word. |
| `auditcore_officebank.project` | Projektgerüst aus Vorlagen und Abgleich der Modulliste (Etappe 6, Plan Kap. 4.5). |
| `auditcore_officebank.stages` | Etappenplan der officebank: welche CLI-Gruppe in welcher Etappe kommt. |
| `auditcore_officebank.testing` | Fakes für Tests ohne VM und ohne Office. |
| `auditcore_officebank.vm` | Windows-Gast steuern: Gastagent, Benutzersitzung, Austauschserver, Sperre, Fotos. |
<!-- api-overview:end -->

## Profile und Konfiguration

- **Rechnerprofil** `~/.config/auditcore-officebank/profil.toml`, Schema
  `auditcore-officebank/rechner/1`: Tabellen `[vm]` (`name`, `backend` = `utm`),
  `[austausch]` (`bind`, `port`), `[autor]` (`kopfkommentar`), optional
  `[mcp.endpunkte.<name>]` (`url`, `token` = *Name* des Secrets) und `[upload]`
  (Name → Ziel). Das Profil gehört nie in ein Projekt-Repo.
- **Projektdatei** `.officebank.toml`, Schema `auditcore-officebank/projekt/1`:
  `[projekt]` (`kuerzel`, `host` = `excel|access|word`, `quelle`, Standard `src`),
  `[module]` (`reihenfolge`, `modulliste`), `[lint]` (`profil`, Standard = Host).
  Die Tabellen `datenschutz`, `gast`, `schritte`, `dialogregeln`, `build`,
  `paket`, `schwaerzung` und `upload` sind für spätere Etappen reserviert;
  andere Einträge sind ein Fehler.
- JSON-Schemas: `auditcore-officebank konfig schema rechner|projekt`.
- Exitcodes der CLI: 0 erfolgreich, 2 Konfigurationsfehler, 3 noch nicht umgesetzt.

Spezifikation und Etappenstand: [docs/spezifikation.md](docs/spezifikation.md).

## Herkunft und Charakterisierung

Neue Implementierung. Die Abläufe stammen aus privaten Projektwerkzeugen, die
für vier Office-Pilotprojekte entstanden sind; sie werden ohne Übernahme von
Quelltext und ohne Projektpfade neu geschrieben (`provenance.json`:
`NEW_IMPLEMENTATION`, keine Quellen). Charakterisiert wird mit synthetischen
Konfigurationen und Fakes; eine Altparität wird nicht behauptet.

## Bewusste Verhaltensabweichungen

Keine. Etappe 0 ersetzt noch kein bestehendes Projektwerkzeug.

## Abhängigkeiten

Python `>=3.11`, nur die Standardbibliothek. Extras: `[docx]` mit
`python-docx>=1.1,<2`, `[xlsx]` mit `openpyxl>=3.0.9,<4`. Office, das Office
Deployment Tool und SQL-Server-Images sind keine Abhängigkeiten und werden nicht
mitgeliefert.

## Sicherheit und Datenschutz

Etappe 0 greift nicht auf das Netz zu und startet keine Prozesse. Secrets stehen
in keiner Konfigurationsdatei; dort steht nur ihr Name. Jede CLI-Ausgabe läuft
durch `mask_secrets`. Tests nutzen nur synthetische Daten; ein Test prüft, dass
die Paketdaten keine Office-Dateien, CSV-Dateien oder echten E-Mail-Adressen
enthalten. Statische Prüfungen melden `native_office_compile = not_run`; ein
Office-Lauf wird nie behauptet, solange keiner stattfand.

## Lizenz und Herkunftsnachweis

MIT gemäß [LICENSE](LICENSE), [NOTICE](NOTICE) und
[provenance.json](src/auditcore_officebank/provenance.json).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
