# Herkunft und Clean-Room-Erklärung

## Eigenständige Entwicklung

`@auditcore/bpmn-editor` wurde im Clean-Room-Verfahren neu geschrieben.
Grundlage waren ausschließlich:

- die BPMN-2.0.2-Spezifikation der OMG (Symbolik, Verbindungs- und
  Containerregeln, DI-Modell),
- die öffentliche API und der Quellcode von **diagram-js** (MIT) sowie die
  Metamodelle von **bpmn-moddle**/**moddle** (MIT), auf denen der Editor
  aufsetzt,
- der eigene Code des audit_designer (FlowAudit-Erweiterungen) für
  Schnittstellen-Kompatibilität (Dienstnamen, Farbattribute, DI-Zugriff).

**Nicht** verwendet, gelesen oder abgeschrieben wurden: `bpmn-js`,
`bpmn-js-properties-panel`, `@bpmn-io/properties-panel` und `bpmn-font`
(eigene Lizenz mit Wasserzeichenpflicht). Diese Pakete sind weder
Abhängigkeit noch Entwicklungsabhängigkeit; die Lizenzprüfung
(`npm run license-check`) schlägt fehl, sobald eines davon im Lockfile
auftaucht.

Eigenständig umgesetzt sind insbesondere: Renderer und alle Symbole (Pfade
neu konstruiert, `src/draw`, `src/icons`), Textsatz, Import/Export
(DI ↔ Formen), Modellierungsbefehle und -verhalten, Regeln, Palette,
Kontextpad, Ersetzen-Logik und -Menü, Beschriftungsbearbeitung,
Kopieren/Einfügen, Suche, Übersichtskarte, Raster und Teilprozess-Ebenen.
Die Farbnamensräume `bioc:` und `color:` werden über die in bpmn-moddle
enthaltenen Beschreibungen gelesen und geschrieben.

## Abhängigkeiten zur Laufzeit

Ermittelt mit `node scripts/js/check-licenses.mjs --list`:

| Paket | Version | Lizenz |
| --- | --- | --- |
| diagram-js | 15.27.1 | MIT |
| @bpmn-io/diagram-js-ui (über diagram-js) | 0.2.4 | MIT |
| bpmn-moddle | 10.3.1 | MIT |
| moddle | 8.2.1 | MIT |
| moddle-xml | 12.3.1 | MIT |
| saxen | 11.2.0 | MIT |
| didi | 11.0.0 | MIT |
| min-dash | 5.1.0 | MIT |
| min-dom | 5.3.0 | MIT |
| tiny-svg | 4.1.4 | MIT |
| domify | 3.0.0 | MIT |
| object-refs | 0.4.0 | MIT |
| path-intersection | 4.2.1 | MIT |
| clsx | 2.1.1 | MIT |
| preact | 10.29.8 | MIT |
| htm | 3.1.1 | Apache-2.0 |
| inherits-browser | 0.1.0 | ISC |

Die Stilvorlage bindet `diagram-js/assets/diagram-js.css` (MIT) ein und
ergänzt eigene Stile.

## Testdaten

- `test/fixtures/synthetisch/`: selbst erzeugte Diagramme ohne reale Inhalte.
- `test/fixtures/audit-designer/`: wörtlich aus Tests des audit_designer
  übernommene Beispiel-XML (keine Produktionsdaten).
- Nutzerdiagramme werden nicht eingecheckt; der Paritätstest
  `test/local-parity.spec.ts` liest sie nur lokal über `BPMN_LOCAL_FIXTURES`.
