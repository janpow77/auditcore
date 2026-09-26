# Changelog – @flowaudit/bpmn-flowaudit

## 0.2.1 – 2026-09-26 – Release v0.4.2

Keine Verhaltensänderung. Build mit Vite 8 und vite-plugin-dts 5 (#169); README: Installation als Tarball aus dem GitHub-Release (#157). Abhängigkeit `@flowaudit/bpmn-editor` ^0.1.1.

## 0.2.0 – 2026-09-26

- Neu: Unterpfad `@flowaudit/bpmn-flowaudit/ui` – framework-freier Kern der
  Editor-Oberfläche, den `@flowaudit/bpmn-vue` und `@flowaudit/bpmn-react`
  gemeinsam nutzen: Controller auf `createStore` (Editor, Auswahl, Prüfung,
  Sammlung, Sitzung mit XML-Abgleich, Werkzeugleisten-Aktionen), Export,
  Deskriptoren der Felder und Tabs, Texte (de/en), REST-Ports, Datenquelle
  des einbettbaren Editors, Tastenkürzel und reine View-Funktionen.
  Stile: `@flowaudit/bpmn-flowaudit/ui.css`.
- Korrektur: Das Seitenraster lag unter der Zeichenfläche und war daher
  verdeckt; es liegt jetzt darüber (`z-index`).

## 0.1.0 – 2026-09-25

- Erste Fassung (#90): framework-freie FlowAudit-Fachschicht für den
  BPMN-Editor – moddle-Deskriptor flowaudit 1.0/1.1, Rollen, Kennzeichen,
  Prüfbezüge (KA/BK), Kontrollen, Risiken, Nachweise, Fristen, Quellen,
  Feststellungen, Prüfregeln (Katalog wie `auditcore_bpmn`), Anreicherung,
  Neutralisierung, Versions- und Soll/Ist-Vergleich, Durchlauftest, Berichte,
  Diagrammsammlung, SVG/PNG/PDF-Export, diagram-js-Module, eigene Icons, Ports.
