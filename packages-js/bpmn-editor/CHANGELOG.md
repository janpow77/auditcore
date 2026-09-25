# Changelog @flowaudit/bpmn-editor

## 0.1.0 – 2026-09-25

Erste Fassung (PR #76).

- Eigener BPMN-2.0-Editor im Clean-Room-Verfahren auf diagram-js und
  bpmn-moddle: Renderer mit eigenen Symbolen, Import/Export mit DI,
  Modellierung, Regeln, Palette, Kontextpad, Ersetzen, Beschriftung,
  Kopieren/Einfügen, Suche, Übersichtskarte, Raster und Teilprozess-Ebenen.
- Eigene Typschicht, Aufteilung nach Verantwortung, Komplexität ≤ 12.
- Tests für Regeln, Renderer (Snapshots), Oberfläche, Kopieren/Einfügen,
  Übersetzung, Hilfsfunktionen und SVG-Export; Rundlauf gegen kanonisch
  serialisierte Originale.
- Lizenzprüfung (verbietet bpmn-js*, bpmn-font, @bpmn-io/properties-panel),
  Workflow `js-packages`, `docs/bpmn/editor.md`, `PROVENANCE.md`.
