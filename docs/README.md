# Dokumentation — auditcore

Zentrale Dokumentationsübersicht für das Monorepo `auditcore`. Dieser Leitfaden strukturiert alle technischen, fachlichen und regulatorischen Dokumente des Repositories.

---

## 1. Primäre Dokumente

- [**`AUDITCORE_LASTENHEFT.md`**](../AUDITCORE_LASTENHEFT.md) (Verweis auf [`docs/auditcore_lastenheft.md`](auditcore_lastenheft.md)):
  Das verbindliche Lastenheft mit den 5 Phasen des EU-Prüfprozesses, Migrationsregeln und CI-Kriterien.
- [**`ARCHITEKTUR.md`**](../ARCHITEKTUR.md):
  Monorepo-Topologie, Verzeichnisstruktur, Modulkarte der 32 Python-Pakete unter `packages/` (22 Fachbibliotheken, 5 Querschnittspakete, 5 Quellen-Adapter) und Clean-Domain-Leitplanken.
- [**`README.md`**](../README.md):
  Einführung, Installationswege, Anwendungsphasen und der aus den Paketdateien generierte Paketkatalog (42 Pakete: 32 Python, 10 npm; aufklappbar, Stand prüft `python3 scripts/docs/catalog.py --check`). Die ausführlichere Paketübersicht steht in [`docs/bibliotheken/uebersicht.md`](bibliotheken/uebersicht.md).
- [**`CHANGELOG.md`**](../CHANGELOG.md):
  Vollständige Versionshistorie sämtlicher Releases nach Keep-a-Changelog-Standard.

---

## 2. Struktur des `docs/`-Verzeichnisses

| Verzeichnis | Inhalt & Zweck |
| :--- | :--- |
| [`docs/architecture/`](architecture/) | Detaillierte Entwurfsentscheidungen, Systemkomponenten und Schnittstellenkonzepte. |
| [`docs/bibliotheken/`](bibliotheken/) | Standards und Vorlagen für Fachbibliotheken: [`readme-vorlage.md`](bibliotheken/readme-vorlage.md), [`spezifikation-vorlage.md`](bibliotheken/spezifikation-vorlage.md) und der Paketstatus [`uebersicht.md`](bibliotheken/uebersicht.md). |
| [`docs/bpmn/`](bpmn/) | Spezifikationen der BPMN 2.0-Engine, Prüfpfade und Umstellungspläne für Fachanwendungen. |
| [`docs/deployment/`](deployment/) | Infrastruktur, Paketbereitstellung (PyPI, privater PEP-503-Paketindex, APT Debian/Ubuntu) und Container-Spezifikationen. |
| [`docs/integrations/`](integrations/) | Integrationsleitfäden für Consumer-Anwendungen (z. B. `audit_designer`, `flowstat`, `flowlib`). |
| [`docs/kanban/`](kanban/) | Spezifikationen und Integrationshinweise für Kanban-Boards und Feststellungs-Workflows. |
| [`docs/migrations/`](migrations/) | Migrationsdokumentation, Breaking Changes und Schnittstellenanpassungen zwischen Versionen. |
| [`docs/policy/`](policy/) | Lizenzrichtlinien, Sicherheitsregeln, Open-Source-Governance und Code-Audit-Vorgaben. |
| [`docs/projekt/`](projekt/) | Projektpläne, Phasenübersichten, Statusberichte und Meilenstein-Tracking. |
| [`docs/prompts/`](prompts/) | Standardisierte Agenten-Prompts, Rollenprofile und Prüfanweisungen für KI-Agenten. |
| [`docs/provenance/`](provenance/) | Herkunftsnachweise, SBOMs und Lieferkettensicherheit der Quell- und Binärpakete. |
| [`docs/quality/`](quality/) | Definition der Code-Gates, Qualitätsmetriken, Linter-Regeln und `baseline.json`-Mechanik. |
| [`docs/reports/`](reports/) | Umfassende Berichtsablage aller Fach-, Paket- und Migrationsprüfungen (über 30 Auditberichte, siehe unten). |
| [`docs/ui/`](ui/) | Designsystem-Dokumentation, Komponentenparität zwischen Vue und React sowie Barrierefreiheitsstandards. |
| [`docs/validation/`](validation/) | Validierungsprotokolle, Rauchtests und Nachweise der funktionalen Korrektheit. |

---

## 3. Zentrale Berichte in `docs/reports/`

In [`docs/reports/`](reports/) sind die Prüf- und Fortschrittsberichte strukturiert hinterlegt:
- [`PACKAGE_REVIEW_20260929.md`](reports/PACKAGE_REVIEW_20260929.md): Umfassende Bestandsaufnahme aller Monorepo-Pakete.
- [`ECOHESION_REVIEW_20260929.md`](reports/ECOHESION_REVIEW_20260929.md): Review und Integrationsstand für ECOHESION.
- [`BIBLIOTHEKEN_FORTSCHRITT_20260930.md`](reports/BIBLIOTHEKEN_FORTSCHRITT_20260930.md): Statusbericht zu den neu implementierten Fachpaketen (`pdf`, `checklists`, `privacy`).
- Fachberichte je Paket: z. B. [`GEO_PACKAGE_REPORT.md`](reports/GEO_PACKAGE_REPORT.md), [`RISK_PACKAGE_REPORT.md`](reports/RISK_PACKAGE_REPORT.md), [`DOCUMENTS_PACKAGE_REPORT.md`](reports/DOCUMENTS_PACKAGE_REPORT.md), [`PRICE_PACKAGES_REPORT.md`](reports/PRICE_PACKAGES_REPORT.md) etc.
