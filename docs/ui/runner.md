# RunnerConsole (`RunnerConsole` ↔ `FlowauditRunnerConsole`)

Gerüst erzeugt mit `npm run ui:neu -- runner RunnerConsole`; Fachinhalt ergänzen.

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/runner/` (`createRunnerController`, `runnerMessages`, Port, Anzeige) |
| Stil | `packages-js/ui-core/styles/runner.css` |
| Vue / Web Component | `RunnerConsole` / `<flowaudit-runner-console>` (`packages-js/ui/src/runner/`) |
| React | `FlowauditRunnerConsole` (`packages-js/ui-react/src/runner/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-runner.ts` |

## Vertrag

Eigenschaften: `port`, `locale`. Ereignisse: `item-select` (React `onItemSelect`),
`error` (React `onError`).

## Offen

- REST-Vertrag des Backends und Port-Umsetzung beschreiben.
- Demo-Seite (`packages-js/ui/demo/pages/runner/`) und Browser-Test (`packages-js/ui/e2e/runner.e2e.ts`).
