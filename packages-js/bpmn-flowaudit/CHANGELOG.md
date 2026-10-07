# Changelog – @auditcore/bpmn-flowaudit

## 0.4.0 – 2026-10-07

- **Prüfungsmerkmale nach dem Profil:** `ProfileData.properties` (Block
  `entries` mit `name`, `label`, `kind` = `text` | `choice` | `multi_choice` |
  `yes_no`, `values`, optional `applies_to`, `help`, `depends_on`,
  `separator`) beschreibt Name/Wert-Merkmale je Elementart; die Bibliothek
  kennt keine feste Liste. Hilfen `propertyDefinitionsFor`, `propertyActive`,
  `propertyOptions`, `splitPropertyValue`.
- **`camunda:property` lesen und schreiben** (`model/camundaProperties.ts`):
  `readNamedProperties`, `namedPropertyValue`, `writeNamedProperties`
  (über `modeling`, rückgängig machbar), `setNamedPropertiesDirect`
  (headless). Der Camunda-Namensraum wird bewusst nicht registriert – moddle
  behält die Elemente generisch, Laden und Speichern ohne Bearbeitung bleiben
  unverändert. Geschrieben wird nur das genannte Merkmal; ein leerer Wert
  entfernt es, fremde Merkmale und ihre Reihenfolge bleiben erhalten.
- UI-Kern: Reiter `properties` („Prüfungsmerkmale“), nur wenn das Profil
  Merkmale für den Elementtyp definiert (`tabsFor(type, profile)`);
  Formularmodell `propertyFields` mit `textPatch`, `togglePatch`,
  `yesNoPatch`; Auswahl-Controller `namedProperties()`/`writeProperties()`.
- `ModdleFactory.createAny` (optional) im Diensttyp; Texte DE/EN
  `props.tab.properties`, `props.properties.*`; `ui.css` mit `.fa-property`.

## 0.3.1 – 2026-10-07

- `DiagramCollection.renameFolder()` trimmt den Namen; ein leerer Name lässt den
  bisherigen stehen (bisher wurde er ungeprüft übernommen).
- Texte DE/EN `collection.renameFolder`, `collection.renameHint`,
  `collection.name.edit`, `collection.name.field`; `ui.css` mit `.fa-inline-name`.

## 0.3.0 – 2026-10-06

- Neu: `folderCards()`/`FolderCard`/`CardDiagram` (Ordnerkarten einer Ebene),
  `DiagramCollection.describeFolder()`, im UI-Kern `collectionCards`,
  `hintCount`, `describedXml` sowie die Aktionen `describeFolder` und
  `describeDiagram` des Sammlungs-Controllers. Diagrammbeschreibungen stehen in
  der Diagramm-Info (`flowaudit:diagrammInfo`, Feld `beschreibung`) und werden
  über `StoragePort.saveDiagram` gespeichert; Ordnerbeschreibungen über
  `saveCollection` (Feld `description`, schon im Schema). Der `StoragePort`
  bleibt unverändert.
- Neu: Palettenansichten `PALETTE_VIEWS`, `readPaletteView`,
  `writePaletteView`, `paletteName`, `paletteCaption`; `PaletteItem` trägt bei
  Rollen `short` und `roleLabel` aus dem Rollenkatalog.
- Neu: `HostAction`, `FolderAction`, `hostActionsFor()` für Aktionen der
  einbettenden Anwendung.
- `ui.css`: Ordnerkarten, Prüfhinweise, Palettenansichten, Umbruch der
  Rollenkacheln, dezente Linienauswahl mit hellen Knickpunkten (auch ohne
  diagram-js-Stylesheet wirksam).
- Texte DE/EN für alle neuen Bedienelemente.

## 0.2.1 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/bpmn-flowaudit` statt `@flowaudit/bpmn-flowaudit` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-bpmn-flowaudit-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

Keine Verhaltensänderung. Build mit Vite 8 und vite-plugin-dts 5 (#169); README: Installation als Tarball aus dem GitHub-Release (#157). Abhängigkeit `@auditcore/bpmn-editor` ^0.1.1.

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
