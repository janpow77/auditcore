# Changelog auditcore_dataprotection

## 0.5.1 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_common==0.2.0`, `auditcore_reporting==0.3.0`.

## 0.5.0 – REST-Schnittstelle für VVT- und DSFA-Oberfläche

Neues Modul `auditcore_dataprotection.web` (Vertrag `dataprotection_ui/1`,
`docs/ui/dataprotection-rest.md`) für `<flowaudit-vvt>` und `<flowaudit-dsfa>`
aus `@flowaudit/ui`. Bestehende Module, Berechnung, Profile und Berichte
unverändert.

- `DataProtectionApi`: Handler ohne Web-Framework für Profil, Verzeichnis
  (lesen, prüfen, Entwurf, Freigabe, Export) und Folgenabschätzung (Übersicht,
  Beginn, Erhebung, Vorschau `calculate`, Entscheidung, DSB-Einholung,
  Freigabe, Neubewertung, Bericht). Fehler als
  `{"error": {"code", "message"}}`, Bibliotheksfehler mit eigenem Code.
- `Storage`-Protocol (Repositories und Audit aus `ports`), `InMemoryStorage`
  für Demo/Tests, `create_backend`, `SystemClock`, `UuidIds`.
- Extras `web` (`routes`, `create_app`; Starlette ≥ 0.26.1) und `fastapi`
  (`create_router`); Frameworks werden nur bei Bedarf importiert.
- Exporte: HTML-Druckansicht (Renderer der Bibliothek), Markdown, CSV mit
  Formelschutz nach `contracts/common-cases` (`csv-cell`, `csv-document`).
- Debian-Zuordnung der Extras in `packaging/library-extras.json`.

## 0.4.3 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung. Neue Laufzeitabhängigkeit `auditcore_common==0.1.0`
(APT `python3-auditcore-common`).

- Profil-Fingerprint und Inhaltshash → `auditcore_common.hashing.canonical_sha256`;
  `hashing.canonical_sha256` bleibt als veralteter Alias (`DeprecationWarning`).
- `available_profiles`/`load_profile` → `auditcore_common.profiles`
  (`require_text=True, invalid_name="missing"`).
- `report_data.plain` ist veraltet; intern
  `jsonable(value, enums=True, dataclasses=True, sets=True)`.
- openpyxl über `optional.require_module`, Tausendertrennung der
  Vorbelegungstexte über `text.group_thousands_de`.
- `fingerprint`/`content_hash` nehmen `Mapping[str, object]` (statt `Any`); Code-Gate `any_usages` 146 → 145.
- Meldungen, Fingerprints und Berichtsdaten unverändert; 501 Tests grün.

## 0.4.2 – Abhängigkeit auf auditcore_reporting 0.2.1

Keine Änderung an Code oder Ergebnissen. Das Extra `excel` verlangt jetzt
`auditcore_reporting[excel]==0.2.1` (Refaktorierung ohne
Verhaltensänderung; Profile, Zahlenformate und Arbeitsmappen bytegleich).
Debian-Zuordnung in `packaging/library-extras.json` entsprechend
(`python3-auditcore-reporting (>= 0.2.1)`).

## 0.4.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: Berechnung, Legacy-Adapter, Berichte, Exporte und
Fehlermeldungen sind unverändert. Die 19 Originaltests, die 129 beobachteten
Legacy-Fälle und alle übrigen Tests laufen unverändert; Profile und Fixtures
sind bytegleich.

- `calculation` (1 063 Zeilen) geschnitten in `answers` (Eingabegrenze),
  `screening`, `risk`, `results`, `prefill`; `propose` baut den Vorschlag über
  einen kleinen Builder statt einer eingebetteten Funktion.
- `assessment` (1 187 Zeilen) geschnitten in `assessment_core` (Ports,
  Wächter, Lesen), `assessment_input`, `assessment_checks` (Freigabeprüfungen
  als geordnete Prüfkette statt einer Funktion mit Komplexität 19),
  `assessment_involvement` (DSB, Konsultation), `assessment_review`
  (Prüfbedarf, Neubewertung, Übersicht). `AssessmentService` setzt sich daraus
  zusammen; Felder, Methoden und Signaturen bleiben gleich.
- `rules` geschnitten in `profile_model`, `profile_loader`,
  `profile_sections`; `register` in Dienst und `register_content`; `export`
  in `report_data`, `assessment_html`, `assessment_html_outcome`,
  `register_html`, `html_common`;
  `legacy` in `legacy_scoring`, `legacy_admin`, `legacy_report`; die
  tabellarischen XLSX-Inhalte in `workbook_tables`.
- Gemeinsame Hilfen statt Duplikaten: `hashing.canonical_sha256` für
  Profil-Fingerprint und Inhaltsprüfsumme, `legacy_report.format_datetime_de`
  für Bericht und Arbeitsmappe, eine gemeinsame Prüfung „nur eine offene
  Fassung“.
- Typen: `Any` nur noch an JSON-Grenzen (Profil-, Register- und
  Berichtsdokumente, Legacy-Datensätze) und für das ungetypte openpyxl;
  Eingabeparameter sonst `object`/`Mapping[str, object]`, neue TypedDicts für
  Schema-2-Profilfelder und EDPB-Szenariofelder.

| Messung (nur `src`) | 0.4.0 | 0.4.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 7 | 0 |
| Module > 400 Zeilen | 7 | 0 |
| `Any`-Vorkommen (grep) | 180 | 172 |
| `Any` in Annotationen (Code-Gate `any_usages`) | 170 | 146 |
| Funktionen > 60 Zeilen (Code-Gate) | 20 | 0 |
| mypy `--strict` | sauber | sauber |
| Tests | 488 + 1 übersprungen | 500 + 1 übersprungen |
| Zeilenabdeckung | 96 % | 97 % |

Veraltete Aliase (mit `DeprecationWarning`): `legacy.PFLICHT` →
`legacy.LEGACY_SCREENING_REQUIRED`, `legacy.KEINE_PFLICHT` →
`legacy.LEGACY_SCREENING_NOT_REQUIRED`.
