# auditcore_reportgates

## Zweck

Fail-closed-Zahlengates für erzeugte Berichte: Fließtextzahlen gegen Berichtsobjekte, Tabellen gegen Referenzwerte, Freigabe über alle Pflicht-Gates.

Nicht Prüfbares ist `not_run`, nie `passed`. Prozent und Prozentpunkte werden
nie ineinander umgerechnet, ein Fehlwert ist nie null, und die Skala einer
Tabellenzahl kommt aus der Spaltenüberschrift, nicht aus der Größe der Zahl.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_reportgates==0.2.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256` stehen im
Index unter `https://janpow77.github.io/auditcore/simple/auditcore-reportgates/`):

```text
auditcore_reportgates @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_reportgates-0.2.0-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-reportgates
```

Extras: `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_reportgates import (
    BoundValue,
    Table,
    check_paragraph,
    compare_tables,
    exact,
    release,
    unit_of,
)

werte = [BoundValue(exact(15_782_365), unit_of("Zuwendung (Euro)"), "Tabelle 7")]
prosa = check_paragraph("Bewilligt wurden 15,8 Mio. Euro.", werte, location="S. 12")

ist = Table(("Bereich", "Anzahl", "Mio. Euro"), (("A", 3, 1.25),), vintage="2025-05-14")
soll = Table(("Bereich", "Anzahl", "Mio. Euro"), (("A", "3", "1,3"),), vintage="2025-05-14")
werte_gate = compare_tables(ist, soll)

freigabe = release([prosa, werte_gate], required=["prose_numbers", "reference_values"])
assert freigabe.released
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_reportgates.__all__` (49):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `BASIC_UNITS` | Konstante | Narrow unit set: percent, percentage points and the three scale abbreviations. | `syntax` |
| `CURRENCY` | Konstante | Currency in a lowered header; word boundaries: ``Europa`` names no currency. | `units` |
| `DEFAULT_MASKS` | Konstante | Dates, footnote markers, cross references, legal citations, ``je 100.000``. | `syntax` |
| `DEFAULT_SYNTAX` | Konstante | – | `syntax` |
| `DEFAULT_UNITS` | Konstante | Units read by default: percent, percentage points, scales and currency. | `syntax` |
| `MISSING` | Konstante | – | `numbers` |
| `MISSING_MARKERS` | Konstante | Markers that stand for a missing value (compared case-insensitively). | `numbers` |
| `MISSING_TEXT` | Konstante | Printed form of a missing value. | `numbers` |
| `NEIGHBOURHOOD` | Konstante | Relative distance up to which an unequal value counts as the meant value. | `prose` |
| `NO_CLAIMS` | Konstante | Reason of a paragraph without numbers; neutral for :func:`combine`. | `prose` |
| `PERCENT` | Konstante | – | `units` |
| `PERCENTAGE_POINTS` | Konstante | – | `units` |
| `PLAIN` | Konstante | – | `units` |
| `ROUNDING_MODES` | Konstante | Rounding modes of :mod:`decimal` accepted by :func:`format_de`. | `numbers` |
| `BoundValue` | Datenklasse | A value a claim may refer to: object value or declared context value. | `prose` |
| `Claim` | Datenklasse | A number printed in prose with its unit and position. | `prose` |
| `ClaimCheck` | Datenklasse | Status of a claim and the value it was compared with. | `prose` |
| `ClaimStatus` | Aufzählung | Outcome for one claim. | `prose` |
| `ClaimSyntax` | Datenklasse | Tokeniser settings; the defaults are the strict reading. | `syntax` |
| `Dimension` | Aufzählung | Kind of quantity. | `units` |
| `Finding` | Datenklasse | One concrete deviation that makes a gate fail. | `verdict` |
| `GateResult` | Datenklasse | Result of one gate: verdict, reason when not passed, counts and findings. | `verdict` |
| `Missing` | Aufzählung | The single missing-value marker. | `numbers` |
| `PointReading` | Aufzählung | Reading of a point that is not a thousands separator (``"2.5"``). | `syntax` |
| `PrintedNumber` | Datenklasse | A number as printed: exact value and printed decimals. | `numbers` |
| `ReleaseDecision` | Datenklasse | Fail-closed combination of the required gates. | `verdict` |
| `Table` | Datenklasse | Header row and body rows; the first column holds the row label. | `reference` |
| `Unit` | Datenklasse | Dimension and decimal exponent of the scale; ``exponent`` ``None`` = not stated. | `units` |
| `Verdict` | Aufzählung | Outcome of a gate. | `verdict` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `ambiguous_numbers` | Funktion | Numbers that cannot be read unambiguously (``"2.5 Mio."``); never split into parts. | `prose` |
| `check_claim` | Funktion | Compare one claim with all unit-compatible values. | `prose` |
| `check_paragraph` | Funktion | Gate result for one paragraph. | `prose` |
| `combine` | Funktion | Combine paragraph results; paragraphs without numbers are neutral. | `prose` |
| `compare_tables` | Funktion | Compare every numeric reference cell; extra and missing rows are findings. | `reference` |
| `conversion_exponent` | Funktion | Exponent ``e`` with ``value_in_target = value_in_source * 10**e``. | `units` |
| `decide` | Funktion | Verdict from counts: findings fail, nothing checked is ``not_run``. | `verdict` |
| `exact` | Funktion | A computed value without printed rounding; NaN and infinity are rejected. | `numbers` |
| `extract_claims` | Funktion | All numbers of a paragraph; dates, footnotes and cross references are masked. | `prose` |
| `format_de` | Funktion | Print a value German style; ``None``/``MISSING`` become ``k. A.``, zero stays ``0,00``. | `numbers` |
| `normalise_label` | Funktion | Lower case, without soft hyphens, dashes, spaces and punctuation. | `reference` |
| `read_cell` | Funktion | Classify a cell: number, ``MISSING`` or text (returned stripped). | `numbers` |
| `read_number` | Funktion | German printed number (``"1.234,50"``, ``"2,2 %"``, ``"– 5,1"``) or ``None``. | `numbers` |
| `relative_deviation` | Funktion | ``\|actual - expected\| / \|expected\|``; ``None`` for an expected zero. | `numbers` |
| `release` | Funktion | Combine gate results; a required gate without result counts as not run. | `verdict` |
| `same_value` | Funktion | Equal within the printed rounding of the coarser side (plus ``epsilon``). | `numbers` |
| `scale_of` | Funktion | Decimal exponent of the amount scale named in ``text``, whatever the dimension. | `units` |
| `tolerance` | Funktion | Half a unit of the coarser printed side plus ``epsilon``. | `numbers` |
| `unit_of` | Funktion | Unit named in a prose token (``"%"``, ``"Mio."``) or a column header. | `units` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_reportgates.numbers` | Printed German numbers with their precision; true zero versus missing value. |
| `auditcore_reportgates.prose` | Prose number gate: every number in a paragraph must be bound to a report value. |
| `auditcore_reportgates.reference` | Reference value gate: a generated table against its reference table. |
| `auditcore_reportgates.syntax` | How prose numbers are tokenised: unit set, reading of a lone point, masks. |
| `auditcore_reportgates.units` | Units of printed numbers: percent is not percentage points, scale from the column. |
| `auditcore_reportgates.verdict` | Three-valued gate verdicts and the fail-closed release decision. |
<!-- api-overview:end -->

## Profile und Konfiguration

Keine Konfigurationsdateien und keine Umgebungsvariablen. Stellschrauben sind
Parameter: `neighbourhood` (Nachbarschaft für Widerspruch, Standard 10 %),
`allowed_years` (ausdrücklich erlaubte Jahreszahlen im Fließtext; siehe unten),
`missing_markers` (Fehlwertzeichen), `dash_is_zero` (Strich nach Destatis
als genau null), `epsilon` (absoluter Puffer in `same_value`/`tolerance` für
Gleitkommareste, Standard 0) und `rounding` in `format_de` (Standard
kaufmännisch `ROUND_HALF_UP`, wählbar `ROUND_HALF_EVEN` u. a.).

**Lesart im Fließtext (`syntax`).** `extract_claims`, `check_paragraph` und
`ambiguous_numbers` nehmen eine `ClaimSyntax`: welche Einheiten hinter einer
Zahl gelesen werden (`DEFAULT_UNITS` oder das schmale `BASIC_UNITS` ohne
Währung, `Pp.` und `Millionen`), wie ein einzelner Punkt gelesen wird
(`PointReading.AMBIGUOUS` – Befund `zahl_mehrdeutig` –, `DECIMAL` – „2.5“ ist
2,5 – oder `SPLIT` – „2.5“ sind die Zahlen 2 und 5, Lesart des früheren
FlowStat-Gates) und welche Stellen vorher maskiert werden (`masks`).

```python
from auditcore_reportgates import BASIC_UNITS, ClaimSyntax, PointReading, extract_claims

eng = ClaimSyntax(units=BASIC_UNITS, point=PointReading.DECIMAL)
assert [c.unit_text for c in extract_claims("2.5 Mio. und 7 Euro", syntax=eng)] == ["Mio.", ""]
```

**Skala aus Mischüberschriften.** `unit_of` ordnet `Veränderung Mio. Euro (%)`
als Prozent ein (keine Betragsskala); `scale_of` liest die Skala unabhängig
davon (6). Die Währungserkennung ist über `currency` austauschbar.

**Jahreszahlen im Fließtext.** Eine ganze Zahl 1900–2100 gilt nur mit
Jahreskontext als Jahr: Jahreswort, `im`/`seit`, Spanne `2022–2024`,
kurze Präposition (`bis`, `ab`, `von`, `vor`, `nach`, `zwischen`) oder
Satzanfang direkt vor Verb oder Komma (`2023 stieg die Quote`). Eine
Einheit (`Euro`, `%`) oder ein Zählwort (`Vorhaben`, `Teilnehmende` …)
danach ist Gegenbeleg: `bis 2050 Vorhaben` und `zwischen 1950 und 2100 Euro`
bleiben prüfpflichtige Zahlen, ebenso `2023 Vorhaben wurden gefördert`. Wo die
Heuristik nicht reicht, nennt der Aufrufer die Berichtsjahre ausdrücklich
über `allowed_years` – das ist der verlässliche Weg; eine dort genannte
Zahl ist immer Jahr.

**Spaltenschlüssel im Wertegate.** Spalten werden über die Überschrift ohne
Einheit zugeordnet (`Betrag (Mio. Euro)` → `betrag`). Zwei Spalten, die sich
nur in der Einheit unterscheiden (`Betrag (Euro)`, `Betrag (%)`), teilen sich
den Schlüssel; wird er für den Vergleich gebraucht, ergibt das den Befund
`spalte_mehrdeutig`, keine geratene Zuordnung. Abhilfe: Überschrift um ein
unterscheidendes Wort ergänzen (`Betrag (Plan)`).

## Herkunft und Charakterisierung

Hervorgegangen aus den Zahlen- und Wertegates der HIS-Berichtsstrecke in
audit_designer (FlowStat). Charakterisiert durch Tests zu Treffer, Widerspruch,
ungebundener Zahl, Jahreszahlen, Einheiten, Fehlwerten und Freigabe;
Herkunftsangaben in `provenance.json`.

## Bewusste Verhaltensabweichungen

Abweichungen gegenüber der Quelle stehen in
[`docs/behavior-changes.md`](docs/behavior-changes.md).

## Abhängigkeiten

- Pflicht: `auditcore_common==0.2.1`, Python `>=3.11`
- Optional: `[dev]` – Test- und Prüfwerkzeuge (pytest, hypothesis, ruff, mypy, build).
- Bewusst keine Abhängigkeit: kein Web-Framework, keine Datenbank, kein Sprachmodell.

## Sicherheit und Datenschutz

Rein lokale Berechnung im Speicher ohne Netzwerk- oder Dateizugriff. Befunde
enthalten nur die geprüften Zahlen und Fundstellen, die der Aufrufer übergibt.

## Lizenz und Herkunftsnachweis

Veröffentlicht unter der MIT-Lizenz gemäß [`LICENSE`](LICENSE) und [`NOTICE`](NOTICE).
Herkunftsnachweis in [`provenance.json`](provenance.json).

## Änderungen

Alle Änderungen sind im [Changelog](CHANGELOG.md) verzeichnet.
