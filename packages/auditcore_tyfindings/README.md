# auditcore_tyfindings

## Zweck

Types of Findings 2021–2027 für Feststellungen der EFRE-Verwaltungsprüfungen: versionierter Katalog, Zuordnung der Fehlerkennziffern mit Schlüsselwortregeln und Gold-plating-Kennzeichen.

Gemeinsames Modul für FlowInvoice (VerwK) und den Dummydaten-Generator; es
ersetzt die bisher nur in VBA vorhandene Logik des Moduls `modAKB_ToF` der
AKB-Auswertung. Nicht enthalten sind das Einlesen von Prüfberichten,
Beträge, Hochrechnung und Fehlerquoten sowie Feststellungen der Prüfbehörde.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt);
`auditcore_tyfindings` ist noch nicht veröffentlicht, die Befehle gelten ab
dem ersten Release, das 0.1.0 enthält:

```bash
python -m pip install 'auditcore_tyfindings==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256` stehen nach
der Veröffentlichung im Index unter
`https://janpow77.github.io/auditcore/simple/auditcore-tyfindings/`):

```text
auditcore_tyfindings @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_tyfindings-0.1.0-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-tyfindings
```

Extras: keine außer `[dev]` – Test- und Prüfwerkzeuge (pytest, ruff, mypy,
openpyxl für den lokalen Paritätstest).

## Schnellstart

Belegkürzungen und nichtfinanzielle Mängel mit synthetischen Beschreibungen
zuordnen:

```python
from auditcore_tyfindings import formal_zuordnen, katalog, kategorie, zuordnen

assert len(katalog()) == 86

skonto = zuordnen("8.9", "Skonto nicht abgezogen")  # mehrdeutig: Schlüsselwort gewinnt
assert (skonto.tof_unterkategorie, skonto.zuordnungsweg) == ("4.2", "Schlüsselwort")

bagatelle = zuordnen("16", "Einzelbeleg unter 50 EUR")  # Regel mit !GP
assert bagatelle.tof_unterkategorie == "4.16" and bagatelle.gold_plating

assert zuordnen("7.1").tof_kategorie == "10"
assert zuordnen("1.10").zuordnungsweg == "nicht zugeordnet"  # Text, nicht Zahl
assert formal_zuordnen("Förderhinweis auf der Website fehlt").tof_unterkategorie == "8.1"
assert kategorie("4.16") == "4"
```

```pycon
>>> zuordnen("8.3")
Zuordnung(tof_unterkategorie=None, tof_kategorie=None, zuordnungsweg='nicht zugeordnet', gold_plating=False, regel_id='kennziffer:8.3')
>>> zuordnen("8.3").anzeige
'nicht zugeordnet'
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_tyfindings.__all__` (27):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `OHNE_KENNZIFFER` | Konstante | Schlüssel der Kennziffertabelle für Belege ohne Fehlerkennziffer. | `modell` |
| `STANDARDPROFIL` | Konstante | Profil, das :func:`auditcore_tyfindings.zuordnen` ohne ``profil`` verwendet. Ein neues Profil ändert diesen Wert nur mit einer neuen Paketversion. | `profil` |
| `WEG_KENNZIFFER` | Konstante | Zuordnungsweg „Kennziffer“: Unterkategorie aus der Kennziffertabelle. | `modell` |
| `WEG_NICHT_ZUGEORDNET` | Konstante | Zuordnungsweg und VBA-Anzeigetext, wenn keine Unterkategorie gefunden wurde. | `modell` |
| `WEG_SCHLUESSELWORT` | Konstante | Zuordnungsweg „Schlüsselwort“: Treffer einer Schlüsselwort- oder Formalregel. | `modell` |
| `EingabeFehler` | Ausnahme | Eine Eingabe hat den falschen Typ (z. B. Kennziffer als Zahl statt als Text). | `errors` |
| `KennzifferEintrag` | Datenklasse | Zeile der Kennziffertabelle (VBA ``ToFStandard``). | `modell` |
| `KuerzungsgrundEintrag` | Datenklasse | Ein Schlüssel der Belegliste; ``kennziffer`` nur bei Status ``zugeordnet``. | `kuerzungsgrund` |
| `KuerzungsgrundTabelle` | Datenklasse | Versionierte Schlüsseltabelle mit Fingerabdruck. | `kuerzungsgrund` |
| `ProfilFehler` | Ausnahme | Ein Profil oder eine Tabelle fehlt, ist fehlerhaft oder nicht ausdrücklich gewählt. | `errors` |
| `Schluesselwortregel` | Datenklasse | Suchwort (klein geschrieben, Teilzeichenkette) → Unterkategorie; erster Treffer gewinnt. | `modell` |
| `ToFEintrag` | Datenklasse | Eine Unterkategorie der Kommissionstabelle „Types of findings 2021–2027“. | `modell` |
| `ToFProfil` | Datenklasse | Versioniertes Profil: Katalog, Kennziffertabelle und Formalregeln mit Fingerabdruck. | `modell` |
| `TyFindingsFehler` | Ausnahme | Basisklasse aller Fehler der Bibliothek. | `errors` |
| `Zuordnung` | Datenklasse | Ergebnis einer Zuordnung; ``tof_unterkategorie`` ist ``None``, wenn nicht zugeordnet. | `modell` |
| `formal_zuordnen` | Funktion | ToF-Unterkategorie eines nichtfinanziellen Mangels über die Formalregeln. | `zuordnung` |
| `katalog` | Funktion | Alle Unterkategorien der Kommissionstabelle in Katalogreihenfolge. | `zuordnung` |
| `kategorie` | Funktion | ToF-Kategorie einer Unterkategorie: der Text vor dem ersten Punkt („4.16“ → „4“). | `modell` |
| `kennziffer_aus_kuerzungsgrund` | Funktion | Fehlerkennziffer zum Kürzungsgrund oder ``None``. | `kuerzungsgrund` |
| `kennziffer_normalisieren` | Funktion | Schlüssel der Kennziffertabelle wie im VBA-Import (``ToKey``). | `zuordnung` |
| `kuerzungsgrund` | Funktion | Eintrag zum Schlüssel (exakter Text nach Abschneiden der Ränder) oder ``None``. | `kuerzungsgrund` |
| `load_kuerzungsgruende` | Funktion | Eine ausdrücklich benannte, verpackte Tabellenversion laden. | `kuerzungsgrund` |
| `load_profile` | Funktion | Ein ausdrücklich benanntes, verpacktes Profil in einer Version laden. | `profil` |
| `profil_aus_dict` | Funktion | Profildokument prüfen und als :class:`ToFProfil` liefern. | `profil` |
| `standardprofil` | Funktion | Das Profil :data:`~auditcore_tyfindings.profil.STANDARDPROFIL` (einmal geladen). | `zuordnung` |
| `verfuegbare_profile` | Funktion | Verpackte ``(id, version)``-Paare. | `profil` |
| `zuordnen` | Funktion | ToF-Unterkategorie einer Belegkürzung aus Fehlerkennziffer und Beschreibung. | `zuordnung` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_tyfindings.errors` | Fehlervertrag der Bibliothek; ``code`` ist stabil und maschinenlesbar. |
| `auditcore_tyfindings.kuerzungsgrund` | Versionierte Tabelle: Kürzungsgrund der Beleglisten → Fehlerkennziffer. |
| `auditcore_tyfindings.kuerzungsgrund_data` | Packaged tables of reduction-reason keys (``<id>-<version>.json``). |
| `auditcore_tyfindings.modell` | Unveränderliche Datenmodelle: Katalog, Regeln, Profil und Ergebnis einer Zuordnung. |
| `auditcore_tyfindings.profil` | Versionierte ToF-Profile laden, prüfen und mit Fingerabdruck versehen. |
| `auditcore_tyfindings.profile_data` | Packaged ToF profiles (``<id>-<version>.json``). |
| `auditcore_tyfindings.zuordnung` | Zuordnung von Fehlerkennziffern und nichtfinanziellen Mängeln zu ToF-Unterkategorien. |
<!-- api-overview:end -->

## Profile und Konfiguration

- **`efre.tof_2021_2027` Version `2026.10.1`** (`STANDARDPROFIL`): Katalog mit
  86 Unterkategorien in 15 Kategorien, Kennziffertabelle (11 Zeilen) und 30
  Formalregeln, Fingerabdruck
  `149acf962219ec306a83615e56e42500691dd56aa08557f147688862a0adcdc5`
  (SHA-256 über das kanonische JSON). `zuordnen`, `formal_zuordnen` und
  `katalog` verwenden es, wenn kein `profil` übergeben wird; andere Versionen
  lädt `load_profile(id, version)` ausdrücklich. Ein neues Standardprofil
  kommt nur mit einer neuen Paketversion.
- **`efre.kuerzungsgrund_zs` Version `2026.10.1`**: Kürzungsgründe der
  Beleglisten der Zwischengeschalteten Stelle → Fehlerkennziffer
  (`kennziffer_aus_kuerzungsgrund`). Sicher ist nur „0“ = kein Kürzungsgrund;
  „810“ und „890“ sind als offen geführt (Fehlerkennziffer `None`) und **vom
  Fachbereich zu befüllen**. Nichts ist erfunden.
- Regeln, Zuordnungswege und das Erzeugen eines Profils aus dem VBA-Modul:
  [docs/zuordnungsregeln.md](docs/zuordnungsregeln.md).
- Umgebungsvariable `AUDITCORE_TYFINDINGS_PARITY_XLSX`: nur für den lokalen
  Paritätstest (siehe unten); die Bibliothek selbst liest keine Variable.

## Herkunft und Charakterisierung

Portiert aus `src/modAKB_ToF.bas` des lokalen Repositorys `akb-makro`
(Commit `4799ac6c`, `provenance.json`). Katalog und Regeln erzeugt
`tools/vba_profil.py` aus den VBA-Ausdrücken (`--check` vergleicht erneut).
Die Ablauflogik entspricht `ToFZuordnen`, `ToFFormalZuordnen` und
`ToFKategorie`. Paritätstest gegen die Ergebnismappe des VBA-Laufs vom
04.10.2026: 574 Belegkürzungen und 46 nichtfinanzielle Mängel, 0
Abweichungen in Unterkategorie, Zuordnungsweg, Gold-plating und Kategorie.
Der Test läuft nur lokal mit gesetzter Umgebungsvariable, weil die Mappe
personenbezogene Daten enthält; im Repository liegen keine Inhalte daraus.

## Bewusste Verhaltensabweichungen

Ergebnisse sind gleich; Abweichungen betreffen nur die Schnittstelle (keine
Überschreibung durch Tabellen der Trägermappe, `None` statt „nicht
zugeordnet“, Kennziffer nur als Text). Einzelheiten:
[docs/behavior-changes.md](docs/behavior-changes.md).

## Grenzen

Die Zuordnung ist der Vorschlag der Quellanwendung, abgeleitet aus den
Beschreibungen im Bericht über die Verwaltungsprüfungen, und gegen den
Fehlerkatalog der Verwaltungsbehörde zu prüfen. Kennziffer 8.3 ist offen.
Schlüsselwörter sind Teilzeichenketten ohne Wortgrenzen („datum“ trifft auch
„Rechnungsdatum“); es gewinnt die erste passende Regel. Gold-plating-Kandidaten
sind ein Hinweis, keine Feststellung.

## Abhängigkeiten

- Pflicht: `auditcore_common==0.2.1` (kanonischer SHA-256, verpackte
  Profile), Python `>=3.11`.
- Optional: `[dev]` – Test- und Prüfwerkzeuge; `openpyxl` nur für den
  Paritätstest. Excel ist keine Laufzeitabhängigkeit.

## Sicherheit und Datenschutz

Kein Netzwerkzugriff, keine Geheimnisse, keine personenbezogenen Daten im
Paket. Beschreibungen werden nur im Speicher klein geschrieben und durchsucht,
nicht gespeichert oder protokolliert. Eingaben müssen Text sein (sonst
`EingabeFehler`), Profile werden vor Gebrauch vollständig geprüft
(`ProfilFehler`). Der Paritätstest meldet nur Tabelle, Zeile, Kennziffer und
Zuordnung, nie Zellinhalte.

## Lizenz und Herkunftsnachweis

MIT, siehe [`LICENSE`](LICENSE) und [`NOTICE`](NOTICE); Herkunft und
Freigabe des Rechteinhabers (USER_AUTHORIZED_MIT, 22.09.2026) in
[`provenance.json`](provenance.json). Nummern und englische Bezeichnungen
des Katalogs stammen aus der Kommissionstabelle „Types of findings 2021–2027“.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
