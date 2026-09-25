# auditcore_entity_matching

## Zweck

Nachvollziehbare Normalisierung von Firmen- und Personennamen nach benannten, versionierten Profilen, LEI-Prüfung nach ISO 17442 und transparente unscharfe Abgleiche.

Für Anwendungen mit Entitätsabgleich, Sanktions- und PEP-Screening oder
Rechnungsstellerprüfung (flowworkshop, audit_designer, flowinvoice,
audit-portal, riskanalysis) und für die Pakete `auditcore_registry_sources`
und `auditcore_risk`. Datenbank, ORM, SQL-Vorfilter, Schwellen und
Konfidenzklassen bleiben in der Anwendung; es gibt kein stilles
Standardprofil.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_entity_matching[fuzzy]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.2.0 im
Release v0.3.2; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-entity-matching/`):

```text
auditcore_entity_matching @ https://github.com/janpow77/auditcore/releases/download/v0.3.2/auditcore_entity_matching-0.2.0-py3-none-any.whl#sha256=60c6ebec0c45ad48eac1bcd80fa306c49222827e8a36745bac61329be41f3e30
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-entity-matching
```

Extras: `[fuzzy]` – rapidfuzz für `best_match`, `classify` und `pair_score`
(ohne Extra lösen diese `DependencyError` aus; Normalisierung und LEI-Prüfung
laufen ohne); `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_entity_matching import (
    check_lei,
    extract_lei,
    load_profile,
    normalize,
    recommended_profile,
)

# LEI: Format und Prüfziffern (ISO 7064 MOD 97-10)
assert check_lei("529900T8BM49AURSDO55").valid
assert not check_lei("7LTWFZYICNSX8D621K87").valid  # Prüfziffern falsch
assert extract_lei("LEI 529900T8BM49AURSDO55 laut Register") == "529900T8BM49AURSDO55"

# Normalisierung immer nach einem ausdrücklich gewählten Profil
profil = load_profile("flowworkshop.state_aid", "2026.09.1")
assert normalize("Brüder Weiß GmbH & Co. KG", profil) == "brueder weiss"

empfohlen = recommended_profile("entity_normalization")
assert (empfohlen.id, empfohlen.version) == ("flowworkshop.state_aid", "2026.09.2")
```

```pycon
>>> normalize("Müller Holding AG", load_profile("audit_designer.sanctions", "2026.09.1"))
'muller holding'
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_entity_matching.__all__` (21):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `Candidate` | Datenklasse | A candidate record; ``normalized`` must use the same profile as the query. | `matching` |
| `DependencyError` | Ausnahme | The optional fuzzy extra (``auditcore_entity_matching[fuzzy]``) is not installed. | `errors` |
| `EntityMatchingError` | Ausnahme | Base class; ``code`` is stable and machine readable. | `errors` |
| `LeiCheck` | Datenklasse | Result of :func:`check_lei`; ``valid`` requires format and check digits. | `lei` |
| `MatchResult` | Datenklasse | Best candidate with its score and the evidence of every scorer. | `matching` |
| `PAIR_SCORERS` | Konstante | – | `matching` |
| `Profile` | Datenklasse | Immutable profile with identity, source and fingerprint. | `profiles` |
| `ProfileError` | Ausnahme | A profile is missing, malformed or of the wrong kind. | `errors` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `available_profiles` | Funktion | Packaged ``(id, version)`` pairs; no profile is an implicit default. | `profiles` |
| `best_match` | Funktion | Highest-scoring candidate at or above ``min_score`` or ``None``. | `matching` |
| `check_lei` | Funktion | Normalise (strip, upper case) and check format and check digits. | `lei` |
| `classify` | Funktion | Score class ``exact``/``high``/``medium``/``low`` of a screening profile. | `matching` |
| `extract_lei` | Funktion | First LEI token in a free-text identifier field. | `lei` |
| `is_lei_format` | Funktion | Format check only (source behavior); does not verify the check digits. | `lei` |
| `lei_check_digits` | Funktion | Two check digits for an 18-character LEI prefix (for test data and validation). | `lei` |
| `lei_checksum_ok` | Funktion | ISO 7064 MOD 97-10 over the 20 characters (letters A=10 … Z=35). | `lei` |
| `load_profile` | Funktion | Load an explicitly named packaged profile version. | `profiles` |
| `normalize` | Funktion | Comparison form of ``text`` under the given normalisation profile. | `normalize` |
| `pair_score` | Funktion | Score (0–100) of two already normalised names with one named rapidfuzz scorer. | `matching` |
| `recommended_profile` | Funktion | The profile marked as recommended for ``purpose`` (user decisions of 23.09.2026). | `profiles` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_entity_matching.errors` | Error contract of the entity matching library. |
| `auditcore_entity_matching.legacy` | Behavior-compatible functions of the source applications. |
| `auditcore_entity_matching.lei` | Legal Entity Identifier checks (ISO 17442). |
| `auditcore_entity_matching.matching` | Transparent fuzzy match components (optional extra ``fuzzy`` = rapidfuzz). |
| `auditcore_entity_matching.normalize` | Name normalisation for comparison only; the displayed name is never changed. |
| `auditcore_entity_matching.profile_data` | – |
| `auditcore_entity_matching.profiles` | Versioned, source-bound normalisation, classification and resolution profiles. |
<!-- api-overview:end -->

Das Modul `legacy` enthält die verhaltensgleichen Funktionen der
Quellanwendungen (etwa `flowworkshop_is_valid_lei`,
`designer_normalisiere_name_umschrift`, `flowinvoice_pep_normalize_name`) für
bestehende Consumer.

## Profile und Konfiguration

Jedes Profil ist quellengebunden, versioniert und hat einen Fingerprint;
`available_profiles()` listet alle `(id, version)`-Paare.

| Profil | Versionen | Herkunft / Verwendung |
|---|---|---|
| `flowworkshop.state_aid` | 2026.09.1, 2026.09.2 | Beihilfe-Namensabgleich (`Müller → mueller`) |
| `flowworkshop.sanctions` | 2026.09.1–2026.09.3 | Sanktionsabgleich flowworkshop |
| `audit_designer.sanctions` | 2026.09.1–2026.09.3 | Sanktionsabgleich audit_designer |
| `flowworkshop.entity_resolution` | 2026.09.1 | Entity Resolution flowworkshop |
| `flowinvoice.pep` | 2026.09.1, 2026.09.2 | PEP-Massenabgleich |
| `audit_portal.name`, `audit_portal.name_folded` | 2026.09.1 | Vergleichsformen des Portals |
| `riskanalysis.payee` | 2026.09.1, 2026.09.2 | Rechnungssteller der Red-Flag-Regel RF09 |

`recommended_profile(zweck)` liefert die nach den Nutzerentscheidungen vom
23.09.2026 empfohlenen Profile (alle NFC und Umschrift `Müller → mueller`):
`entity_normalization` → `flowworkshop.state_aid` 2026.09.2,
`sanctions_screening` → `audit_designer.sanctions` 2026.09.3,
`pep_screening` → `flowinvoice.pep` 2026.09.2, `payee` →
`riskanalysis.payee` 2026.09.2. Die Empfehlung ändert kein Ergebnis eines
benannten Profils. Schwellen (etwa 75, 70, Klassen 97/90/80) existieren nur
als benannte Profilwerte; `best_match` verlangt `min_score` ausdrücklich.

## Herkunft und Charakterisierung

Extrahiert aus `flowworkshop@a05bb21` (entity_resolution, state_aid_service,
sanctions_service) und `audit_designer@030a71e` (Register-Sanktionen), seit
0.2.0 zusätzlich `audit_designer@1254591`, `flowworkshop@3d1cb40`,
`flowinvoice@fb2d185`, `audit-portal@ac1ccc7` und `riskanalysis@b5c523b`.
Das Verhalten wurde vor der Übernahme tatsächlich ausgeführt und
aufgezeichnet (`tools/capture_legacy.py` mit 440 Fällen und weitere
Erfassungswerkzeuge für Umschrift, flowinvoice, Portal und riskanalysis).
Das Modul `legacy` und alle Profile reproduzieren die Originale
**legacy-exakt**; die Refaktorierung 0.2.1 ließ alle 989 Tests und die
Profil-Fingerprints unverändert.

## Bewusste Verhaltensabweichungen

Nur der Bibliotheksvertrag weicht ab, die Legacy-Funktionen nicht
([docs/behavior-changes.md](docs/behavior-changes.md)):

- EM-C01/EM-C02: `check_lei(...).valid` und `extract_lei` verlangen korrekte
  Prüfziffern (Original: nur Format, auch `000…0` galt als gültig);
  `is_lei_format` behält die reine Formatprüfung.
- EM-C03: Die unterschiedlichen Normalisierungen der Quellen bleiben
  getrennte Profile, keine Vereinheitlichung.
- EM-C04: Schwellen nur als benannte Profilwerte, nicht als Konstanten.
- EM-C05: `normalize` nimmt nur Text, keine stille Typumwandlung.

Anbindung von flowworkshop: [docs/consumer-integration.md](docs/consumer-integration.md).

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Optional
`rapidfuzz>=3.10.1,<4` über `[fuzzy]`. Keine Abhängigkeit von der Plattform
`auditcore` oder anderen Fachpaketen.

## Sicherheit und Datenschutz

Verarbeitet Namen natürlicher und juristischer Personen, die der Aufrufer
übergibt; das Paket speichert nichts, nutzt kein Netzwerk und keine Dateien
außer den mitgelieferten Profildaten. Profile sind charakterisiertes
Softwareverhalten, keine validierte Abgleichmethode: Ein Treffer ist ein
Hinweis zur Prüfung, keine Feststellung. Schwellen und Treffer-Entscheidungen
verantwortet die Anwendung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Der Rechteinhaber hat am 22.09.2026 den extrahierten
Bibliothekscode freigegeben (`USER_AUTHORIZED_MIT`); die Quellrepositories
selbst werden nicht umlizenziert. Quellen mit Commits und Git-Blobs:
`NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
