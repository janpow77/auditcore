# Changelog @auditcore/bpmn-editor

## 0.1.2 – 2026-10-07

- **Pools lassen sich in der Fläche greifen und verschieben.** Bahnen füllen
  einen Pool bis auf den Titelstreifen aus und dürfen nicht allein verschoben
  werden; ein Ziehen in der Fläche traf die Bahn und tat nichts, greifbar war
  nur der schmale Titelstreifen. Neues Modul `lane-move`: Beim Start einer
  Verschiebung werden Bahnen durch ihren Pool ersetzt (auch in einer
  Mehrfachauswahl), der Pool wandert samt Inhalt. Ein Klick wählt weiterhin
  die Bahn, Shift-Ziehen bleibt das Lasso.

## 0.1.1 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/bpmn-editor` statt `@flowaudit/bpmn-editor` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-bpmn-editor-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

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
