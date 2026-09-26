# Changelog @flowaudit/bpmn-editor

## 0.1.1 – 2026-09-26 – Release v0.4.2

Keine Verhaltensänderung. Build mit Vite 8 und vite-plugin-dts 5 (#169); README: Installation als Tarball aus dem GitHub-Release (#157). Erstmals als Release-Datei (`npm pack`-Tarball).

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
