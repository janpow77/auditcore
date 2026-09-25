# @flowaudit/bpmn-vue

Vue-3-Oberfläche des FlowAudit-BPMN-Editors: Werkzeugleiste, Palette,
Eigenschaften-Panel (deklarativ), Diagramm-Infos, Rechtsgrundlagen-Erfassung,
Sammlung als Ordnerbaum mit Drag-and-drop, Tags, Filter, Info-Spalte,
Gruppenübersicht, Hinweisliste, Durchlauftest, Soll/Ist- und
Versionsvergleich, Exportdialog, Anreicherung, Suche, Tastenkürzel.

Drei Ausgaben:

- Vue-Bibliothek (`dist/`): `FlowauditEditor`, `FlowauditWorkbench`, Stores, REST-Ports,
- Web Component `<flowaudit-bpmn-editor>` (`dist-wc/`, Import `@flowaudit/bpmn-vue/web-component`),
- eigenständige App (`dist-standalone/`) gegen den REST-Vertrag `docs/bpmn/rest-api.md`.

Alles ist lokal gebündelt, keine CDN-Abhängigkeit.

```bash
npm run demo        # Demo mit synthetischen Diagrammen (Vite, Speicher im Browser)
npm test            # Vitest + @vue/test-utils
npm run test:e2e    # Playwright gegen die Demo
```

Dokumentation: `docs/bpmn/frontend.md`.

## Lizenz und Herkunft

MIT (siehe `LICENSE`). Clean-Room-Erklärung: Dieses Paket enthält keinen Code,
keine Styles und keine Icons aus bpmn-js, bpmn-js-properties-panel,
@bpmn-io/properties-panel oder bpmn-font. Genutzt werden nur diagram-js und
bpmn-moddle (MIT) über den eigenen Kern `@flowaudit/bpmn-editor`. Portiert
wurde ausschließlich FlowAudit-eigener Code aus dem audit_designer
(Paritätsinventar: `docs/bpmn/paritaet-audit-designer.md`). Die Icons sind
eigene SVG-Pfade (24 px, `currentColor`).
