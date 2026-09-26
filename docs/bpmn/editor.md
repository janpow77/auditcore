# BPMN-Editor (`@flowaudit/bpmn-editor`)

Eigener BPMN-2.0-Zeicheneditor, der bpmn-js im audit_designer ablöst.
Paket: `packages-js/bpmn-editor`, Lizenz MIT, TypeScript, framework-frei.
Die FlowAudit-Fachschicht (`@flowaudit/bpmn-flowaudit`) und die
Vue-Komponenten (`@flowaudit/bpmn-vue`) setzen auf diesem Kern auf.

## Clean-Room-Regel

Grundlage sind die OMG-BPMN-2.0.2-Spezifikation, diagram-js (MIT) und
bpmn-moddle/moddle (MIT). Code, Stile, Symbole und Schriften aus `bpmn-js`,
`bpmn-js-properties-panel`, `@bpmn-io/properties-panel` und `bpmn-font`
werden weder verwendet noch gelesen noch installiert. Die CI prüft das
Lockfile (`npm run license-check`): verbotene Pakete oder unzulässige
Lizenzen (Laufzeit nur MIT, ISC, BSD, Apache-2.0) brechen den Lauf ab.
Einzelheiten: `packages-js/bpmn-editor/PROVENANCE.md`.

## Architektur

```
BpmnEditor ── diagram-js (Canvas, EventBus, CommandStack, …)
   │
   ├─ draw/        Renderer je Elementfamilie, eigene Glyphen, Textsatz, Farben, Pfeilspitzen
   ├─ import/      Importer + PlaneWalker (DI → Formen/Kanten, Ebenen für zugeklappte Teilprozesse)
   ├─ modeling/    Modeling (Befehle), ElementFactory, BpmnFactory,
   │               BpmnUpdater (Semantik/DI folgen dem Diagramm), Verhalten (behavior/)
   ├─ rules/       Verbindungs-, Container- und Größenregeln nach BPMN
   ├─ replace/     Ersetzen („Morphen“) mit deklarativen Zieltabellen
   ├─ palette/ context-pad/ popup-menu/   Bedienoberfläche
   ├─ label-editing/ copy-paste/ search/ minimap/ keyboard/ grid/ snapping/
   └─ auto-place/ auto-resize/ drilldown/ ordering/ layout/ export/ i18n/ icons/
```

Grundsatz der Semantik: Nach jedem ausgeführten oder zurückgenommenen Befehl
ist das Diagramm maßgeblich; `BpmnUpdater` leitet Container
(`flowElements`, `artifacts`, `participants`, `laneSets`, …), Referenzen
(`sourceRef`, `incoming`, …) und DI (Bounds, Waypoints, Beschriftungen,
Einbettung in die Ebene) daraus ab. Bahnen sind im Diagrammbaum Kinder des
Pools; ihre Verschachtelung steht nur in `childLaneSet`, die
Zugehörigkeit der Knoten in `flowNodeRef` (automatisch nachgeführt).

## Öffentliche API

```ts
new BpmnEditor({ container, additionalModules?, moddleExtensions?, keyboard?, gridSize? = 10, locale? = 'de', config? })
importXML(xml): Promise<{ warnings: string[] }>
saveXML({ format? }): Promise<{ xml }>
saveSVG(): Promise<{ svg }>
createDiagram(): Promise<void>
get<T>(service): T
on(event, cb, priority?) / off(event, cb)
destroy()
getDefinitions(), importDefinitions(definitions), clear(), container
export { translations, createTranslate, DEFAULT_MODULES, getBusinessObject, getDi, is, isAny, … }
```

`keyboard.bindTo` wird angenommen, aber nicht mehr weitergegeben: diagram-js 15
bindet Tastenkürzel an die fokussierte Zeichenfläche.

### Dienste (Auszug, Namen wie in diagram-js/bpmn-Ökosystem üblich)

| Dienst | Zweck |
| --- | --- |
| `eventBus`, `canvas`, `elementRegistry`, `commandStack`, `selection`, `overlays` | diagram-js-Kern |
| `moddle`, `bpmnFactory`, `elementFactory` | Objekte und Formen erzeugen |
| `modeling` | `updateProperties`, `updateModdleProperties`, `setColor`, `updateLabel`, `connect`, `addLane`, `splitLane`, `resizeLane`, `updateLaneRefs`, `makeCollaboration`, `makeProcess`, `claimId`, `unclaimId`, `compound` sowie alle diagram-js-Befehle (`createShape`, `moveElements`, `resizeShape`, `removeElements`, …) |
| `bpmnRules` | `canConnect`, `canCreate`, `canMove`, `canAttach`, `canResize` |
| `bpmnReplace` | `replaceElement(element, target)`, `replaceFlow(connection, 'sequence' \| 'default' \| 'conditional')` |
| `bpmnImporter`, `bpmnUpdater`, `bpmnRenderer`, `textRenderer` | Import, Synchronisation, Darstellung |
| `labelEditing` (auch `directEditing`) | `activate`, `complete`, `cancel`, `isActive` |
| `copyPaste`, `clipboard` (gemeinsam für alle Editoren einer Seite) | Kopieren/Einfügen auch zwischen Diagrammen |
| `bpmnSearch`, `searchPad` | Suche nach Name/Kennung (Strg+F) |
| `minimap` | `open`, `close`, `toggle`, `update` |
| `gridSnapping`, `gridDisplay` | Raster (Weite aus `gridSize`) |
| `subProcessPlanes` | `drillDown`, `drillUp`, `toggleExpanded`, `ensurePlane`, `getPlaneRoot` |
| `paletteProvider`, `contextPadProvider`, `replaceMenuProvider`, `colorMenuProvider`, `alignMenuProvider` | Oberfläche; Menüs `bpmn-replace`, `bpmn-color`, `bpmn-align` |
| `editorActions` | u. a. `undo`, `redo`, `copy`, `paste`, `selectElements`, `spaceTool`, `lassoTool`, `handTool`, `globalConnectTool`, `directEditing`, `find`, `replaceElement`, `alignElements`, `distributeElements`, `setColor`, `toggleMinimap`, `zoomFit`, `moveToOrigin` |
| `translate` | Übersetzung (Deutsch Standard) |

Ereignisse u. a.: `import.parse.start`, `import.parse.complete`, `import.render.start`,
`import.render.complete`, `import.done`, `saveXML.start`, `saveXML.serialized`,
`saveXML.done`, `saveSVG.done`, `selection.changed`, `element.changed`,
`elements.changed`, `commandStack.changed`, `directEditing.activate`,
`directEditing.complete`, `minimap.toggle`, `root.set`.

Konventionen: `element.businessObject` (moddle), `element.di` (BPMNShape/
BPMNEdge bzw. BPMNPlane der Wurzel). Farben stehen an der DI als
`bioc:fill`/`bioc:stroke` und `color:background-color`/`color:border-color`
(Beschriftung `color:color`); `setColor` schreibt beide Namensräume.

## Elementumfang

- **Pools und Kollaboration:** Pool (aufgeklappt/leer, waagerecht/senkrecht,
  Mehrfachbeteiligung), verschachtelte Bahnen, Nachrichtenflüsse. Der erste
  Pool macht aus dem Prozess eine Kollaboration und umschließt den Inhalt.
- **Aktivitäten:** Aufgabe, Benutzer-, manuelle, Service-, Skript-,
  Geschäftsregel-, Sende-, Empfangsaufgabe, Aufrufaktivität, Teilprozess
  (auf-/zugeklappt mit eigener Ebene, Ereignis-Teilprozess, Transaktion,
  Ad-hoc); Marker Schleife, parallele/sequenzielle Mehrfachinstanz,
  Kompensation, Ad-hoc.
- **Ereignisse:** Start, Zwischen (fangend/werfend), Ende, Rand
  (unterbrechend/nicht unterbrechend) mit Nachricht, Zeitgeber, Eskalation,
  Bedingung, Link, Fehler, Abbruch, Kompensation, Signal, Mehrfach,
  parallel Mehrfach, Terminierung.
- **Gateways:** exklusiv, inklusiv, parallel, komplex, ereignisbasiert
  (auch instanziierend und parallel).
- **Daten:** Datenobjekt (Sammlung), Dateneingang/-ausgang, Datenspeicher,
  Dateneingangs-/-ausgangsassoziation.
- **Artefakte:** Textanmerkung, Assoziation (ohne/mit Richtung), Gruppe mit
  Kategoriewert.
- **Sequenzfluss:** Standard, bedingt, Default.

Funktionen: eigene SVG-Renderer, Palette, Kontextpad (Anhängen, Ersetzen,
Verbinden, Bahnen, Anmerkung, Farbe, Löschen; bei Mehrfachauswahl
Ausrichten/Farbe/Löschen), Ersetzen-Menü mit Marker-Kopfleiste,
Beschriftung direkt bearbeiten, rechtwinklige Kantenführung mit Knick- und
Andockpunkten, BPMN-Regeln, Verschieben, Größe ändern, Raumwerkzeug, Lasso,
Hand, Einrasten mit Hilfslinien und Raster, Ausrichten/Verteilen,
Kopieren/Einfügen (auch zwischen Diagrammen), Rückgängig/Wiederholen,
Tastenkürzel, Zoom/Einpassen, Übersichtskarte, Suche, Teilprozess-Ebenen mit
Brotkrumen, Import/Export BPMN 2.0 XML mit DI (unbekannte Erweiterungen und
Attribute bleiben erhalten), SVG-Export, deutsche Oberfläche.

## Qualität und Prüfungen

- `npm run lint` (ESLint, `no-explicit-any` als Fehler, Komplexität ≤ 12,
  keine dateiweiten Ausnahmen; `npm run lint:exceptions` zählt Ausnahmen),
  `npm run typecheck` (`strict`, `noUncheckedIndexedAccess`), `npm test`
  (Vitest mit happy-dom), `npm run build` (Vite, ESM + Typen + CSS),
  `npm run license-check`.
- Rundlauf-Tests: Export ohne Bearbeitung entspricht exakt dem kanonisch
  serialisierten Original (synthetische Fixtures, Beispiele aus dem
  audit_designer). Lokal zusätzlich gegen nicht veröffentlichte
  Nutzerdiagramme: `BPMN_LOCAL_FIXTURES=<verzeichnis> npm test -w @flowaudit/bpmn-editor`.

## Bekannte Grenzen

- Diagramme ohne DI werden verlustfrei durchgereicht, aber nicht angezeigt
  (keine automatische Anordnung).
- Beim Kopieren von Pools wird die Verschachtelung von Bahnen flach
  eingefügt; der Inhalt zugeklappter Teilprozesse (eigene Ebene) wird nicht
  mitkopiert.
