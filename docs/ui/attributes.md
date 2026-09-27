# Merkmalsstichprobe (`AttributeSampling` ↔ `FlowauditAttributeSampling`)

Auswertung von Kontrolltests in Systemprüfungen nach dem KOM-Leitfaden
EGESIF_16-0014-01, Abschn. 7.9. Die Komponente ist mit `npm run ui:neu -- attributes AttributeSampling`
angelegt. Gerechnet wird ausschließlich über den REST-Vertrag
`auditcore_extrapolation.evaluation/1` (`POST /attributes`, siehe
[extrapolation-rest.md](extrapolation-rest.md)).

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/attributes/` (`createAttributesController`, `buildAttributesRequest`, `attributesMetrics`, `createAttributesRestPort`) |
| Stil | `packages-js/ui-core/styles/attributes.css` |
| Vue / Web Component | `AttributeSampling` / `<flowaudit-attribute-sampling>` (`packages-js/ui/src/attributes/`) |
| React | `FlowauditAttributeSampling` (`packages-js/ui-react/src/attributes/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-attributes.ts` (Fixtures aus dem echten Backend) |

## Verfahren

| Verfahren | Leitfaden | Auswertung |
|---|---|---|
| Merkmalsstichprobe | 7.9.3–7.9.5 | EDR = k/n, SE = z × √(p(1 − p)/n), ULD = EDR + SE; Ergebnis „Kriterium erfüllt“, wenn ULD ≤ tolerierbare Quote |
| Discovery-Stichprobe | 7.9.6 | exakte Binomial-Obergrenze; ohne Abweichung und Obergrenze ≤ kritische Quote: Kriterium erfüllt; jede Abweichung ist ein zu untersuchender Einzelfall |
| Stop-or-go-Stichprobe | 7.9.6 | exakte Binomial-Obergrenze; „Stopp“, wenn sie höchstens die tolerierbare Quote erreicht, sonst „Weiter“ (Erweiterung ist Planung) |

Der Leitfaden nennt für 7.9.6 keine Formel (Verweis auf die Fachliteratur);
die exakte Binomialgrenze ist eine Methodenwahl der Bibliothek und in der
Prüfstrategie zu begründen. Die Formel in 7.9.4 ist ohne Wurzel gedruckt; die
Bibliothek rechnet mit Wurzel (siehe `packages/auditcore_extrapolation/docs/referenzfaelle.md`).

## Vertrag

Eigenschaften: `port` (z. B. `createAttributesRestPort({ baseUrl: '/api/extrapolation' })`),
`locale`. Ereignisse: `evaluation-completed` (React `onEvaluationCompleted`),
`error` (React `onError`).
