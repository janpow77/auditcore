# auditcore_privacy

## Zweck

Deterministische, kollisionsfreie Pseudonymisierung, Maskierung und Scoped-Zuordnungsverwaltung für Prüf- und Kontrollprozesse.

Die Bibliothek stellt Fachanwendungen reproduzierbare, format- und rechtsformerhaltende Ersatzwerte für sensible Personen-, Unternehmens- und Finanzdaten bereit. Sie arbeitet framework-unabhängig ohne Datenbank- oder Netzwerkanbindung.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_privacy==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256` stehen im
Index unter `https://janpow77.github.io/auditcore/simple/auditcore-privacy/`):

```text
auditcore_privacy @ https://github.com/janpow77/auditcore/releases/download/v0.1.0/auditcore_privacy-0.1.0-py3-none-any.whl#sha256=d3adb33f
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-privacy
```

Extras: `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_privacy import EntityType, PseudonymEngine, mask_text

engine = PseudonymEngine(
    scope_key="pruefung-2026",
    salt="0123456789abcdef0123456789abcdef",
)
person = engine.get_or_create(EntityType.PERSON, "Dr. Hans Meyer")
company = engine.get_or_create(EntityType.COMPANY, "Musterbau GmbH")

assert person == engine.get_or_create(EntityType.PERSON, "Dr. Hans Meyer")
assert company.endswith("GmbH")
assert mask_text("DE1234567890") == "DE12••••••90"
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_privacy.__all__` (14):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `__version__` | Wert | – | `(Paketstamm)` |
| `PrivacyError` | Ausnahme | Basis-Ausnahme für Fehler im Pseudonymisierungs- und Datenschutzmodul. | `errors` |
| `ScopeError` | Ausnahme | Fehler bei der Verwaltung des Pseudonymisierungs-Scopes. | `errors` |
| `CollisionError` | Ausnahme | Kollision bei der Pseudonym-Erzeugung konnte nicht aufgelöst werden. | `errors` |
| `EntityType` | Aufzählung | Kategorie sensibler personenbezogener oder geschäftlicher Daten. | `models` |
| `ReplacementKind` | Aufzählung | Art der Ersetzung für sensible Angaben. | `models` |
| `PseudonymMapping` | Datenklasse | Eintrag in der geschützten Zuordnungstabelle eines Scopes. | `models` |
| `MappingExport` | Datenklasse | Exportfähiges Bündel aller Pseudonymzuordnungen eines Scopes. | `models` |
| `PseudonymEngine` | Klasse | Verwaltet deterministische und kollisionsfreie Pseudonyme für einen Scope. | `engine` |
| `compute_original_hash` | Funktion | Berechnet den Einweg-Hash für die Zuordnungstabelle ohne Klartextablage. | `engine` |
| `generate_salt` | Funktion | Erzeugt einen kryptografisch sicheren Zufalls-Salt für einen Scope. | `engine` |
| `MappingStore` | Klasse | Verwaltet Zuordnungstabellen getrennt nach Scopes. | `mapping` |
| `mask_text` | Funktion | Maskiert sensible Zeichenfolgen mit Schutzpunkten (•). | `masking` |
| `is_valid_iban` | Funktion | Prüft eine IBAN nach ISO 13616 (MOD 97-10). | `generators` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_privacy.engine` | Kollisionsfreie Pseudonymisierungs-Engine mit fester Scope-Bindung. |
| `auditcore_privacy.errors` | Fehlerklassen und JSON-Typverträge für auditcore_privacy. |
| `auditcore_privacy.generators` | Deterministische Generatoren für formattreue und natürlich wirkende Pseudonyme. |
| `auditcore_privacy.mapping` | Verwaltung und Austausch von Scope-Zuordnungstabellen. |
| `auditcore_privacy.masking` | Maskierung von Textauszügen zur sicheren Anzeige in Prüfberichten. |
| `auditcore_privacy.models` | Datenmodelle und Aufzählungen für Pseudonymisierung und Maskierung. |
| `auditcore_privacy.names` | Kandidatenlisten und feste Konstanten für echt wirkende Ersatzwerte. |
<!-- api-overview:end -->

## Profile und Konfiguration

Die Bibliothek benötigt keine externen Konfigurationsdateien oder Umgebungsvariablen. Alle Pseudonymisierungsoperationen arbeiten deterministisch auf Basis des übergebenen Scopes und Salts.

## Herkunft und Charakterisierung

Hervorgegangen aus den Pseudonymisierungsbausteinen von ECOHESION (`sanitizer/pseudonyms.py`), `flowinvoice` und `riskanalysis`. Charakterisiert durch 23 automatisierte Tests, die deterministische Wiederholung, Scope-Trennung, Kollisionsfreiheit und ISO-13616-Prüfzifferngültigkeit bei IBAN-Generierung nachweisen. Das Verfahren stellt eine Pseudonymisierung dar und darf nicht als Anonymisierung bezeichnet werden, da bei Kenntnis von Salt und Zuordnungstabelle eine Re-Identifizierung möglich bleibt.

## Bewusste Verhaltensabweichungen

Gegenüber früheren Altimplementierungen werden Klartextdaten niemals als Schlüssel in der Zuordnungstabelle gespeichert, sondern ausschließlich Einweg-Hashes (Blake2b). Potenzielle Kollisionen werden deterministisch über bis zu 64 Versuche und einen garantierten nummerierten Fallback aufgelöst.

## Abhängigkeiten

- Pflicht: `auditcore_common==0.2.0`, Python `>=3.11`
- Optional: `[dev]` – Test- und Prüfwerkzeuge (pytest, ruff, mypy, build).
- Bewusst keine Abhängigkeit: kein SQLAlchemy, kein FastAPI/Starlette, keine Datenbanktreiber.

## Sicherheit und Datenschutz

Verarbeitung erfolgt vollständig lokal im Speicher ohne Netzwerk- oder Dateisystemzugriffe. Klartexte werden nicht persistent in Zuordnungstabellen abgelegt. Reversible Zuordnungen bleiben streng an den jeweiligen Scope gebunden. Format-treue Ersatzwerte für IBAN, E-Mail und Telefon nutzen standardisierte Testbereiche (Null-Bankleitzahl 00000000, RFC-2606-Domäne `.example`, Bundesnetzagentur-Prüfbereich).

## Lizenz und Herkunftsnachweis

Veröffentlicht unter der MIT-Lizenz gemäß [`LICENSE`](LICENSE) und [`NOTICE`](NOTICE).
Dokumentation der Herkunft und Charakterisierung in [`provenance.json`](src/auditcore_privacy/provenance.json).

## Änderungen

Alle Änderungen sind im [Changelog](CHANGELOG.md) verzeichnet.
