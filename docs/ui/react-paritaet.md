# Parität Vue ↔ React (`@flowaudit/ui` ↔ `@flowaudit/ui-react`)

Stand: 26.09.2026. Gegenstand: die nativen React-Komponenten aus
`@flowaudit/ui-react` 1.0.0 und die Vue-Fassung aus `@flowaudit/ui` 0.3.0.
Beide rendern aus demselben framework-freien Kern `@flowaudit/ui-core`.

## Aufteilung

| Schicht | Paket | Inhalt |
|---|---|---|
| Kern | `@flowaudit/ui-core` | Texte (`messages`, auch Kanban), Datentypen der REST-Verträge, Ports, View-Modelle (`viewModel`, `registerView`, `dsfaView`), Zustandsautomaten (`createSynopsisController`, `createVvtController`, `createDsfaController`), Fokusfalle (`trapFocus`), Exporte, Symbole, Stile (auch `kanban.css`) |
| Kanban-Kern | `@flowaudit/kanban-core` | Fachregeln wie `auditcore_kanban` und Ansichtslogik (`createBoardController`, `selectBoardView`, `createMoveController`, `createPointerDrag`, `createBoardListController`, `createColumnEditor`, `createShareSearch`) |
| Vue | `@flowaudit/ui` | SFC-Vorlagen; `useStore` spiegelt den Controller-Zustand in ein `shallowRef` |
| React | `@flowaudit/ui-react` | JSX mit demselben Markup; `useStoreState` liest den Zustand über `useSyncExternalStore` |

Fachregeln (Wortvergleich, Filter, Navigation, Vollständigkeit, Revisionen,
Vier-Augen-Hinweis, Vorschau, Entscheidungsvorbelegung, Freigabebedingungen,
Exporte) gibt es nur einmal im Kern. Die Komponenten halten nur
Darstellungszustand, den die Vue-SFC ebenfalls lokal hält (Suchtext der
Tätigkeitsliste, Eingabefelder der Entscheidung, Text der Anzahl-Felder).

## Komponenten

| Komponente | Vue | React (nativ) | REST-Vertrag | Paritätsfälle |
|---|---|---|---|---|
| Tabelle | `FaTable` | `FlowauditTable` | – | 4 |
| Synopse / Versionsvergleich | `FaSynopsis` | `FlowauditSynopsis` | `auditcore_documents.web` ([synopsis-rest.md](synopsis-rest.md)) | 6 |
| Verzeichnis von Verarbeitungstätigkeiten | `FaVvt` | `FlowauditVvt` | `dataprotection_ui/1` ([dataprotection-rest.md](dataprotection-rest.md)) | 5 + Interaktionsfolge |
| Datenschutz-Folgenabschätzung | `FaDsfa` | `FlowauditDsfa` | `dataprotection_ui/1` | 6 + 3 Interaktionsfolgen |
| Geo-Karte | `FaGeoMap` | `FlowauditGeoMap` | `auditcore_geo.web` ([geo-rest.md](geo-rest.md)) | 4 + Interaktionsfolge |
| Kanban-Board und Boardliste | `KanbanBoard`, `KanbanBoardList` | `FlowauditKanbanBoard`, `FlowauditKanbanBoards` | `auditcore_kanban` ([rest-api.md](../kanban/rest-api.md)) | 6 + 2 + 6 Interaktionsfolgen |
| Basis (Schaltfläche, Eingabefeld, Dialog) | `FaButton`, `FaTextField`, `FaDialog` | `Button`, `TextField`, `Dialog` | – | 9 |
| Risiko-Merkmale | `RiskFlags` | `FlowauditRiskFlags` | `auditcore_risk.web` ([risk-rest.md](risk-rest.md)) | 7 + Interaktionsfolge |
| Screening-Trefferprüfung | `ScreeningReview` | `FlowauditScreeningReview` | `screening_review/1` ([screening-rest.md](screening-rest.md)) | 5 + 2 Interaktionsfolgen |
| Stichprobe | `SamplingPanel` | `FlowauditSampling` | `auditcore_sampling.web` ([sampling-rest.md](sampling-rest.md)) | 5 + 2 Interaktionsfolgen |
| Benford-Analyse | `BenfordPanel` | `FlowauditBenford` | `auditcore_statistics.web` ([benford-rest.md](benford-rest.md)) | 4 + Interaktionsfolge |
| Hochrechnung (TER/RER) | `ExtrapolationPanel` | `FlowauditExtrapolation` | `auditcore_extrapolation.evaluation/1` ([extrapolation-rest.md](extrapolation-rest.md)) | 4 + 2 Interaktionsfolgen |

## Nachweis

Die Fälle stehen einmal in `packages-js/ui-core/test/parity/cases*.ts` und
nutzen die gemeinsamen Fixtures (`ui-core/test/fixtures`: Ergebnisse der
echten Python-Backends, keine Personendaten).

1. **Gleiche Erwartungen:** `ui/test/parity*.spec.ts` prüft jeden Fall mit der
   Vue-Fassung, `ui-react/test/parity/*.spec.tsx` mit der React-Fassung
   (Texte, Rollen mit zugänglichem Namen, Anzahl je Selektor;
   `ui-core/test/parity/expect.ts`).
2. **Gleiches DOM:** `ui-react/test/parity` rendert beide Fassungen mit
   denselben Eingaben und vergleicht das normalisierte DOM
   (`ui-core/test/parity/dom.ts`) und den Formularzustand (Werte, Häkchen,
   Auswahl; Listen nach gewählter Position und sichtbarem Text) – auch nach denselben Interaktionen (Tätigkeit wählen, Feld
   ändern, Historie, Referat anlegen, verwerfen, Freigabe anzeigen; Tabwechsel
   per Pfeiltaste und Ende, Antwort mit Vorschau, Entscheidung; Geo: Hinweis ohne
   Bezugspunkt, Punkt übernehmen, Umkreis, Kartenklick, Punkt in Fläche,
   Vereinfachung, Einheit, GeoPackage). Die Leaflet-Ansicht ist in beiden
   Fassungen dieselbe Attrappe; gezeichnet wird mit dem gemeinsamen
   `createLeafletView` aus dem Kern.
3. **Verhalten:** je Komponente eigene Tests mit Testing Library, die den
   Vue-Tests entsprechen (Ereignisse, Tastatur, Port-Aufrufe mit Revision,
   Fehlermeldungen, Sprache).

Die Normalisierung gleicht nur Framework-Artefakte aus: Reihenfolge von
Attributen und Klassen, instanzabhängige Kennungen (`id` und alle Verweise
darauf, Gruppennamen von Optionsfeldern), Kommentarknoten, Leerraum aus der
Vorlagenformatierung, leeres `class`, und Formularwerte, die ein Framework als
Attribut, das andere nur als Eigenschaft setzt (verglichen über den
Formularzustand).

Kanban: Die Fälle stehen in `packages-js/kanban-core/test/parity/cases.ts`
(synthetische Boards). `ui/test/parity-kanban.spec.ts` prüft sie mit Vue,
`ui-react/test/parity/kanban.spec.tsx` mit React samt DOM-Vergleich,
`ui-react/test/parity/kanban-interaction.spec.tsx` vergleicht DOM,
Formularzustand und die im `body` liegenden Dialoge nach denselben
Bedienfolgen (Tastatur: aufnehmen, verschieben, ablegen, abbrechen,
Strg+Pfeil; Detailansicht mit Priorität, Tag, Checkliste, Farbe, Löschen;
Suche und Filter; Einstellungen; Teilen; Boardliste). Die React-Tests laufen
unter React 18 (`npm test`) und React 19 (`npm run test:react19`).

## Abweichungen und Korrekturen

| Punkt | Entscheidung |
|---|---|
| Vorlesetexte der Synopse („gestrichen:“, „eingefügt:“, „Ende“) | In Vue entfernte der Vorlagencompiler das trennende Leerzeichen; korrigiert in `SynopsisText.vue` (beide Fassungen jetzt mit Leerzeichen). |
| `v-model` | React: gesteuerte Prop plus `onXxxChange` oder ungesteuert mit `defaultXxx` (`sort`, `layout`). |
| Slot `cell-<key>` der Tabelle | React: `renderCell(column, row, value)`. |
| `defineExpose` der Synopse | React: `ref` mit `next()`, `previous()`, `exportAs()`. |
| Ereignisse | Gleiche Nutzdaten; React übergibt sie direkt statt als `CustomEvent`. |
| Kanban: Slot `card-extra`, `defineExpose` | React: `renderCardExtra(card)`; `ref` mit `reload()` und `board`. |
| Kanban: Fokus nach dem Verschieben | Vue setzt ihn nach `nextTick`, React nach dem nächsten Rendern (`setTimeout 0`); gleiche Zielkarte. |
| `autofocus` in Dialogen | React setzt das Attribut selbst (`TextField` mit `autoFocus`), damit die Fokusfalle beider Fassungen dasselbe Feld wählt. |
| Grund einer Synopse-Zeile | Vue sendet bei `change`, React beim Verlassen des Feldes nur bei geändertem Text – dieselbe Auslösung. |
| Filter der Risiko-Merkmale (`v-model` an `RiskFlagFilter`) | React: gesteuert `filter`/`onFilterChange`; `FlowauditRiskFlags` meldet jede Änderung wie Vues `filter-change`. |
| Leerer Mindestwert im Screening-Laufformular | Vue (`v-model.number`) liefert `''`, React `null`; beides heißt „kein Mindestwert“. |
| Profilauswahl der Benford-Analyse | Leere Auswahl in beiden Fassungen `<option value="">` (Vue vorher `:value="null"`, nicht sichtbar). |

## BPMN-Editor (`@flowaudit/bpmn-vue` ↔ `@flowaudit/bpmn-react`)

Eigene Paketfamilie mit demselben Aufbau: Kern `@flowaudit/bpmn-flowaudit/ui`
(Controller auf `createStore` für Editor, Auswahl, Prüfung, Sammlung,
Sitzung und Werkzeugleisten-Aktionen; Deskriptoren, Texte, REST-Ports,
Export, Stile), Vue bindet über `useStore`/`reactive`, React über
`useSyncExternalStore`. Die Dialoge beider Fassungen nutzen
`createFocusTrap` aus `@flowaudit/ui-core`.

| Bereich | Vue | React (nativ) | Paritätsfälle |
|---|---|---|---|
| Editor als Ganzes (Werkzeugleiste, Palette, Statusleiste, Seitenleiste, Dialoge) | `FlowauditEditor` | `FlowauditEditor` | 11 Fälle mit Schrittfolgen + XML-Rundlauf + gleiche Bearbeitung |
| Einbettbarer Editor | Web Component `<flowaudit-bpmn-editor>` | `FlowauditBpmnEditor` (gleiche Props, Ereignisse, Ref) | Verhaltenstests je Fassung |
| Formulare, Listen, Rechtsgrundlagen, Kennzeichen | `FieldForm`, `ListEditor`, `LegalBasisEditor`, `LegalSearch`, `MarkerPicker` | gleichnamig | 9 + Interaktionsfolgen |
| Dialoge und Ansichten | Export, Anreicherung, XML, Tastenkürzel, Elementsuche, Diagramm-Infos, Hinweisliste, Schlüsselfilter | gleichnamig | 8 + Interaktionen |
| Sammlung | `CollectionTree`, `GroupOverview`, `DiagramInfoColumn` | gleichnamig | 8 (Filter, Ordner) |

Fälle: `packages-js/bpmn-flowaudit/test/parity/cases-*.ts`; Prüfung in
`packages-js/bpmn-react/test/parity/*.spec.tsx` (Vue und React mit denselben
Eingaben, gleiche Erwartungen, gleiches normalisiertes DOM und gleicher
Formularzustand). Der XML-Rundlauf vergleicht `getXml()` nach dem Laden, die
Nutzdaten von Strg+S, den erneuten Import des exportierten XML und das XML
nach derselben Eigenschaftsänderung. Tests laufen unter React 19 und 18.3.

| Punkt | Entscheidung |
|---|---|
| Zeichenfläche | Die Kindknoten des Canvas-Hosts (Seitenraster, Popover) fügt React hinter, Vue vor dem Container des Kerns ein; verglichen werden die Bereiche außerhalb der Zeichenfläche und das XML. Das Seitenraster liegt in beiden Fassungen per `z-index` über der Zeichenfläche (vorher in Vue verdeckt). |
| Textfelder (`@change`) | React übernimmt beim Verlassen oder mit Enter und nur bei geändertem Text; Vue sendet auch unveränderten Text. |
| Slot `editor` des XML-Dialogs | React: `renderEditor(xml, update)`. |
| `class` am Wurzelelement | React: Prop `className` (Vue reicht sie automatisch durch). |
| `LegalSearch` | `aria-controls` nur bei sichtbarer Trefferliste (korrigiert in Vue). |
