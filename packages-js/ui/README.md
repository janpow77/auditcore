# @flowaudit/ui

Gemeinsame Oberflächenkomponenten der FlowAudit-Anwendungen: Vue 3,
Web Components (`<flowaudit-…>`) und React-Hüllen (`@flowaudit/ui-react`).

```ts
// Vue
import { createFlowauditUi, FaTable } from '@flowaudit/ui'
import '@flowaudit/ui/style.css'
app.use(createFlowauditUi({ locale: 'de' }))

// Web Components (ohne Vue in der Host-Anwendung; vue wird als Abhängigkeit geladen)
import { defineFlowauditElements } from '@flowaudit/ui/elements'
import '@flowaudit/ui/style.css'
defineFlowauditElements({ locale: 'de' })
```

- **Theming:** alle Farben, Abstände und Schriften als CSS-Variablen `--fa-*`
  (`src/theme/tokens.css`); `applyTheme('dark' | 'light' | 'system')` bzw.
  `data-fa-theme` am Wurzelelement.
- **Sprache:** `useI18n(defineMessages({ de, en }))`, Rückfall auf Deutsch;
  `formatDate`, `formatNumber`, `formatPercent`.
- **Basiskomponenten:** `FaButton`, `FaIcon` (eigene Symbole), `FaDialog`
  (modal, Fokusfalle, Escape), `FaTable` (deklarative Spalten, Sortierung mit
  `aria-sort`), `FaBadge`, `FaTextField`.
- **Risiko-Merkmale** (`src/risk/`): `RiskFlags` bzw. `<flowaudit-risk-flags>`
  für Auswertungen von `auditcore_risk.web` (Vertrag
  [`docs/ui/risk-rest.md`](../../docs/ui/risk-rest.md)) – Verteilung je Merkmal
  (`RiskFlagSummary`), Filter (`RiskFlagFilter`), Zustand je Datensatz
  (`RiskFlagTable`), Karten mit Begründung, Profil und Version, Eingabewerten
  und Schwellen (`RiskFlagCard`, `RiskRecordDetail`), Profil mit Eingabefeldern
  (`RiskProfileInfo`). „Unbestimmt“ (z. B. fehlender Nettobetrag) und
  „übersprungen“ (fehlende Spalten) sind eigene Zustände. Die View-Logik
  (`src/risk/view/`) ist framework-frei.

Beitragen: [`docs/ui/beitragen.md`](../../docs/ui/beitragen.md). Lizenz: MIT.
