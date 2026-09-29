# Architektur — auditcore

Monorepo-Architektur für die Prüfung, Verifikation und Standardisierung von Förder- und Finanzprozessen (EFRE/ESF+ Prüfbank und Rechnungsverarbeitung).

---

## 1. Systemübersicht & Monorepo-Topologie

```
┌─────────────────────────────────────────────────────────────┐
│                 auditcore Monorepo                          │
├──────────────────────────────┬──────────────────────────────┤
│  Plattform-Tools             │  Fachpakete (Domain)         │
│  - src/auditcore/quality     │  - packages/auditcore_common │
│  - src/auditcore/codegate    │  - packages/auditcore_invoices│
│  - src/auditcore/consolidate │  - packages/auditcore_rules  │
│  - src/auditcore/refactor    │  - packages/auditcore_donut  │
├──────────────────────────────┴──────────────────────────────┤
│  Frontend / JS-Pakete                                       │
│  - packages-js/auditcore-ui                                 │
│  - packages-js/auditcore-components                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Modulkarte & Paketgrenzen

| Pfad | Typ | Verantwortung |
| :--- | :--- | :--- |
| [`src/auditcore/`](src/auditcore/) | Plattform-Kern | Code-Gate, Qualitätsmessung, Konsolidierungs- und Refactoring-Tools (`codegate`, `consolidator`, `apprefactor`). |
| [`packages/auditcore_common/`](packages/auditcore_common/) | Basis-Fachpaket | Gemeinsame Basistypen, Hash-Prüfsummen, Fehlerklassen und universelle Hilfsfunktionen. |
| [`packages/auditcore_invoicesynth/`](packages/auditcore_invoicesynth/) | Rechnungs-Engine | Synthetische Rechnungserzeugung, Prüfregeln, Donut-Modell-Vorbereitung. |
| [`packages/auditcore_invoicedonut/`](packages/auditcore_invoicedonut/) | KI-Inferenz | PyTorch/Donut-OCR-freie Dokumentenextraktion auf GPU. |
| [`packages-js/`](packages-js/) | TypeScript / UI | Wiederverwendbare UI-Komponenten und Vue/TS-Bausteine. |
| [`contracts/`](contracts/) | Schnittstellen | JSON-Schemas und Typverträge für Prüfberichte und Zertifikate. |

---

## 3. Zentrale Architektur-Regeln (Clean Domain)

1. **Unabhängigkeit der Fachpakete:**
   * Fachpakete (`packages/auditcore_*`) dürfen keine Web-Frameworks (FastAPI, Flask), Datenbank-ORMs oder Plattform-Werkzeuge importieren. Sie sind reine Fachkerne (`tests/test_architecture.py` prüft dies ab).
2. **Keine zirkulären Paket-Abhängigkeiten:**
   * Abhängigkeiten fließen streng hierarchisch: Fachpakete -> `auditcore_common`.
3. **Qualitäts-Ratchet (`baseline.json`):**
   * Code-Metriken (Komplexität, Typabdeckung, Zeilenanzahl) dürfen sich nie verschlechtern; Verbesserungen werden in die Baseline übernommen.
4. **Strikte interne Versionierung:**
   * Paket-Abhängigkeiten im Monorepo werden exakt gepinnt.
