# @flowaudit/ui-react

React-18-Hüllen für die Web Components aus `@flowaudit/ui`. React 18 setzt an
Custom Elements nur Attribute; die Hüllen übergeben Objekte als Eigenschaften
und verdrahten Ereignisse (`onRowClick` ↔ `row-click`).

```tsx
import { FlowauditTable, defineFlowauditElements } from '@flowaudit/ui-react'
import '@flowaudit/ui/style.css'

defineFlowauditElements()

<FlowauditTable columns={columns} rows={rows} clickable onRowClick={(row) => open(row)} />
```

Risiko-Merkmale: `<FlowauditRiskFlags evaluation={antwort} profile={profil} onRecordSelect={(index) => …} />`
(Antworten von `auditcore_risk.web`, siehe `docs/ui/risk-rest.md`).

Eigene Hüllen: `createElementComponent<Props, Events>('flowaudit-…', { properties, events })`.
Lizenz: MIT.
