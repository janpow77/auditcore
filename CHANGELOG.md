# Changelog

## Unreleased

- „Kennung prüfen“: REST-Vertrag `identifiers_ui/1` in
  `auditcore_identifiers.web` (Extras `web`, `fastapi`) und Oberfläche
  `IdentifierCheck`/`<flowaudit-identifier-check>` (Vue) sowie native
  `FlowauditIdentifierCheck` (React) auf gemeinsamem Kern in
  `@flowaudit/ui-core` (`createIdentifierController`,
  `createIdentifiersRestPort`): Prüfprofil mit sichtbarer Empfehlung,
  Einzelprüfung mit Status, Begründung, Grund, Normalform und Einzelheiten,
  Stapelprüfung aus CSV/TSV über den TableImport-Controller mit
  Spaltenzuordnung, Filter „Nur Auffälligkeiten“ und CSV-Export. 4
  Paritätsfälle plus 2 Interaktionsfolgen, Demo-Seite und API-E2E
  (`docs/ui/identifiers-rest.md`).

- Belegerkennung: REST-Vertrag `documents_extraction/1` in
  `auditcore_documents.web` (Upload → Extraktionsergebnis mit Konfidenz →
  Validierungsbefunde; OCR/Donut nur über Ports der Anwendung, ohne Engine
  abgeschaltet) und Oberfläche `<flowaudit-extraction>` (Vue `FaExtraction`,
  React nativ `FlowauditExtraction`, Kern `createExtractionController` in
  `@flowaudit/ui-core`), 8 Paritätsfälle plus Interaktionsfolge, Demo mit
  Attrappen-Ports. Vertrag: `docs/ui/extraction-rest.md`.

- Donut-Nachtraining E3 auf janpow-ai (`auditcore_invoicesynth.train`):
  Job-Image `ghcr.io/janpow77/auditcore-donut-train:cu128` (Workflow
  `donut-train-image`, Basis per Digest, torch 2.11.0+cu128, gepinnte
  Laufzeit, Lizenzhinweise unter `/licenses`); Hängeschutz mit atomarer
  `progress.json` samt Herzschlag, SIGTERM → Checkpoint (Frist 90 s),
  NaN/Inf-Loss und CUDA-OOM mit Sicherung des letzten guten Stands und
  eigenen Exit-Codes, gezählte unlesbare Beispiele; Kommando je Lauf im
  FlowAgent-Job (zweiter Lauf 1536×1152, Seed + 1, vorher gleiche
  Konfiguration auf beiden Karten); `train.evaluate` bewertet Kandidat und
  Donut-CORD mit einem Befehl. Keine Versionsanhebung.

- `auditcore_common`-Migrationen Teil A: neues Modul `auditcore_common.rest`
  (rahmenwerkfreier Teil der REST-Schicht, Duplikatgruppe B1);
  `auditcore_sampling` und `auditcore_statistics` nutzen es,
  `auditcore_sampling` zusätzlich `numeric.numpy_pairwise_sum`/`numpy_round`,
  `auditcore_market_indicators` `numpy_pairwise_sum`, `require_finite`,
  `canonical_sha256` und die Profil-Lader. sampling und market_indicators
  hängen neu von `auditcore_common==0.1.1` ab. Paritätstests alt ↔ neu
  (Differenz- und Hypothesis-Tests in `auditcore_common`); keine
  Verhaltensänderung.

- Offene `auditcore_common`-Migrationen (Teil B): `auditcore_price_sources`
  (kanonisches JSON, Paketbytes bytegleich), `auditcore_geo` (Endlichkeit),
  `auditcore_property_sources` (HTML-Erkennung, Zeitzonenprüfung) und
  `auditcore_invoicesynth` (SHA-256, Steuersatz, Kennungen) nutzen
  `auditcore_common`; `auditcore_documents` nutzt die Prüfziffern aus
  `auditcore_identifiers` (neue Pflichtabhängigkeit `auditcore_identifiers==0.1.0`).
  Neue Pins `auditcore_common==0.1.1` für geo, invoicesynth und price_sources.
  Paritätstests alt ↔ neu je Paket; Code-Gate `duplicate_functions` 4 → 0
  (documents 2 → 0, identifiers 2 → 0). Keine Versionsanhebung (Release v0.4.2).
- Vorbereitung Release v0.4.1: Versionen aller seit v0.4.0 geänderten Pakete
  angehoben (Pins auf `auditcore_common==0.1.1` und die neuen Paketstände),
  `auditcore_harvest` 0.1.2 parst Feeds nur noch über defusedxml
  (`auditcore_common.safe_xml`, neues Extra `xml`), `canonical_hash` und der
  Profil-Fingerprint von `auditcore_price_analysis` nutzen
  `auditcore_common.hashing` (duplicate_functions 7 → 4). Die signierte
  APT-Release-Datei trägt ein `Date`-Feld (RFC 2822, `SOURCE_DATE_EPOCH`
  beachtet); apt meldet nicht mehr „Invalid 'Date' entry“.
- Festlegungen der gemeinsamen Vertragsfälle entschieden (Nutzer, 25.09.2026):
  Ersatzwert „—“, Dateigröße Basis 1024 mit KB/MB und Dezimalkomma, „1.5“ und
  „1.234“ in Beträgen ungültig bzw. mehrdeutig mit Hinweis, höchstens zwei
  Nachkommastellen bei Beträgen (de), Anzeige-Zeitzone Europe/Berlin
  (`contracts/common-cases/decisions.json`: Status „festgelegt (Nutzer
  2026-09-25)“, `DECISIONS.md`). Verträge `parse-number`, `empty-value`,
  `format-date`, `format-filesize` jetzt `verbindlich`; Rundung von Beträgen
  und Trenner Datum/Zeit bleiben vorläufig.
- Neues Paket `auditcore_bpmn` 0.1.0: BPMN 2.0 mit FlowAudit-Erweiterung
  Schema 1.1 (verbindlich in `docs/bpmn/flowaudit-schema-1.1.md`, XSD im
  Paket), gehärtetes Parsen, Elementmodell, Prüfregeln mit stabilen IDs
  (de/en), Profile je Förderperiode (KA nach Anhang XI VO (EU) 2021/1060 und
  Anhang IV Delegierte VO (EU) Nr. 480/2014 aus den amtlichen Texten),
  Diagrammsammlung mit Speicher-Port, Versions- und Soll/Ist-Vergleich,
  Neutralisieren, Anreichern von Altbeständen, Berichte (Prozesstabelle,
  RCM, Feststellungen, KA-Kategorievorschlag) sowie die legacy-treue
  Übernahme von `bpmn_analyzer.py`, `validate_bpmn_bva` und
  `bpmn_export.py` aus audit_designer (charakterisiert, eine dokumentierte
  Abweichung). `EXPECTED_SOURCES` und `packaging/library-extras.json`
  ergänzt.
- CI-Automatisierung (Rechteinhaber, 25.09.2026): Sammel-Check `ci-ok` als
  Required Check neben `code-quality-gate`, Workflows `autofix` (ruff, ESLint,
  reine Baseline-Absenkungen; Hilfsskript `scripts/ci_baseline_lower_only.py`),
  `update-pr-branches`, `dependabot-automerge` und `nightly` (Vollprüfung mit
  Issue „Nightly rot“), dazu `.github/dependabot.yml` und Auto-Merge im
  Repository. Siehe `docs/deployment/ci-automatisierung.md`.

## 0.3.0

- Helfer-Verträge für App-Repositorys (Nutzerauftrag 25.09.2026, „Frontend-
  inventur im Code einbauen, damit die Fehler immer identifiziert werden“):
  neues Modul `auditcore.tools.helpers`, Befehl `auditcore-helpers`
  (`scan`, `lint`, `contracts`, `check`, `toolchain`, `rules`), gemeinsame
  Vertragsfälle `contracts/common-cases/*.json` (11 Verträge, 165 Fälle,
  JSON-Schema, Festlegungen vorläufig in `DECISIONS.md`), 11 deklarative
  Regeln (u. a. Zahlparser wie `BeleglisteGrid.parseDecimal`, Datum ohne
  Zeitzone, handgebaute €-Formatierung, CSV ohne Formelschutz, 422-Fehlertexte;
  zwei Regeln führen erkannte Helfer isoliert aus), Ratchet gegen
  `.auditcore/helpers-baseline.json`, Action `.github/actions/helper-contracts`,
  Nachtlauf `scripts/helpers_nightly.sh` mit systemd-User-Timer (nicht
  aktiviert). Siehe `docs/quality/helper-contracts.md`.
- Verbindliche Code-Qualitätsmaßstäbe als Ratchet (Rechteinhaber, 25.09.2026):
  neue Module `auditcore.tools.quality.codegate*`, Befehl
  `auditcore-codegate check` bzw. `scripts/verify_code_quality.py`, Baseline
  `quality/baseline.json`, Pflicht-Job `code-quality-gate`, pre-commit-Hook
  und Release-Blocker in `verify_domain_packages.py`/`prepare_library_release.py`.
  Siehe `docs/quality/code-quality.md`.

## 0.2.0

- Pflicht zum fachlichen Rauchtest nach Produktions-Deploys (Rechteinhaber,
  24.09.2026): neues Modul `auditcore.tools.deployer.smoke`, Befehl
  `auditcore-deploy smoke`, Blocker in `auditcore-deploy plan` für jedes
  Ziel außer `internal_test` ohne gültige `functional_smoke`-Fälle, Action
  `.github/actions/functional-smoke`. Health-Endpunkte zählen nicht als
  Rauchtest. Siehe `docs/deployment/functional-smoke.md`.

## 0.1.0

Initial platform: framework-independent core models and reporting function,
policy-aware quality gates, GitHub inventory and consolidation planning,
KIRA/Graphify providers, transactional application migration, Debian builds
and isolated lifecycle validation. Release authorization remains separate from
technical build success; see the platform build report for actual evidence.
