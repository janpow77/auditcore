# Changelog @flowaudit/ui-react

## 0.2.0 – 2026-09-25

- React-Hooks auf Basis von `@flowaudit/common`: `useToast` mit
  `ToastProvider` und `sharedToastQueue`, `useMediaQuery`,
  `useClickOutside`, `useSort`, `useDebouncedCallback`, `useAuthToken`.
- Weiterreichung der framework-freien Teile, die bisher nur in
  `@flowaudit/ui` lagen, unter denselben Namen (`formatDate`,
  `formatNumber`, `formatPercent`, `localeTag`, `requestJson`,
  `requestFile`, `RestError`, `saveFile`, `sortRows`, `nextSort`,
  `parseTable`, `parseNumber` …).
- Neue Peer-Abhängigkeit `@flowaudit/common` ^0.1.0; `@flowaudit/ui` ^0.2.0.

## 0.1.0 – 2026-09-25

Erste Fassung.

- Gerüst (PR #80): `createElementComponent` (Objekte als Eigenschaften,
  Ereignisse als `onXxx`), `eventPayload`, Hülle `FlowauditTable`,
  Weiterreichung von `defineFlowauditElements`.
- Kanban (PR #84): `FlowauditKanbanBoard` und `FlowauditKanbanBoards`.
