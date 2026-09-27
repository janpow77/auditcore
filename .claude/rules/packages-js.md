---
paths:
  - "packages-js/**"
---

# JS/TS-Pakete

- npm-Workspace; im Repo-Root `npm ci`, dann `npm run lint`, `npm run typecheck`, `npm test`.
- Vue- und React-Varianten gleich halten: `node scripts/js/ui-parity-gate.mjs` (Ausnahmen in
  `quality/ui-parity-exceptions.json` nur abbauen).
- Gemeinsame Vertragsfälle liegen in `contracts/common-cases/*.json`; Python und TS müssen
  dieselben Ergebnisse liefern.
- Lizenzprüfung: `npm run license-check`.
