# BatchChecks (`BatchChecks` ↔ `FlowauditBatchChecks`)

Gerüst erzeugt mit `npm run ui:neu -- batchchecks BatchChecks`; Fachinhalt ergänzen.

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/batchchecks/` (`createBatchchecksController`, `batchchecksMessages`, Port, Anzeige) |
| Stil | `packages-js/ui-core/styles/batchchecks.css` |
| Vue / Web Component | `BatchChecks` / `<flowaudit-batch-checks>` (`packages-js/ui/src/batchchecks/`) |
| React | `FlowauditBatchChecks` (`packages-js/ui-react/src/batchchecks/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-batchchecks.ts` |

## Vertrag

Eigenschaften: `port`, `locale`. Ereignisse: `item-select` (React `onItemSelect`),
`error` (React `onError`).

## Offen

- REST-Vertrag des Backends und Port-Umsetzung beschreiben.
- Demo-Seite (`packages-js/ui/demo/pages/batchchecks/`) und Browser-Test (`packages-js/ui/e2e/batchchecks.e2e.ts`).
