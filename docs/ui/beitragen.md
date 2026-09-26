# Beitragen zu @auditcore/ui

`@auditcore/ui` (`packages-js/ui`) ist das gemeinsame Oberflächenpaket der
FlowAudit-Anwendungen. Jede Komponente gibt es

1. als **Vue-3-Komponente** (`import { FaTable } from '@auditcore/ui'`),
2. als **Web Component** `<flowaudit-<name>>` (`@auditcore/ui/elements`),
3. als **native React-18-Komponente** in `@auditcore/ui-react`
   (`packages-js/ui-react`) – Tabelle, Synopse, VVT, DSFA, Geo-Karte,
   Risiko-Merkmale, Screening, Stichprobe, Benford, Belegerkennung, Dokumentvergleiche,
   Hochrechnung, Kanban und Datenbankansicht (React 18 und 19).

Fachlogik, Texte, Verträge, View-Modelle, Zustandsautomaten und Stile liegen
framework-frei in **`@auditcore/ui-core`** (`packages-js/ui-core`); Vue und
React binden sie nur an (Vue: `useStore`, React: `useStoreState`). Keine
Fachlogik doppelt in Vue und React.

Grundlagen, die alle Komponenten nutzen: Designtoken (`ui-core/styles/tokens.css`,
CSS-Variablen `--fa-*`, Hell/Dunkel), Sprache (`src/i18n`, Deutsch vollständig,
Englisch vorbereitet), Basiskomponenten (`FaButton`, `FaIcon`, `FaDialog`,
`FaTable`, `FaBadge`, `FaTextField`) und Composables (`useFocusTrap`, `useId`,
`useTheme`, `useI18n`).

## Neue Komponente: Generator und Gate

Das Gerüst einer neuen Komponente entsteht nicht von Hand und nicht per
LLM, sondern mit dem Generator; ob Vue und React vollständig sind, prüft ein
Gate in der CI.

```bash
npm run ui:neu -- <gruppe> <Komponente>     # z. B. npm run ui:neu -- audittrail AuditTrail
npm run lint && npm run typecheck && npm test && npm run ui:gate
```

`<gruppe>` ist kurz, klein und englisch (`kanban`, `risk`, `audittrail`),
`<Komponente>` PascalCase aus Wörtern (`AuditTrail`). Der Generator
(`scripts/js/ui-new.mjs`) überschreibt nichts und erzeugt:

| Schicht | Dateien |
|---|---|
| Kern (`packages-js/ui-core`) | `src/<gruppe>/{messages,types,port,view,controller,index}.ts` (Controller mit `createStore`), `test/<gruppe>/controller.spec.ts`, `styles/<gruppe>.css` (in `styles/index.css`), Export in `src/index.ts` |
| Vue (`packages-js/ui`) | `src/<gruppe>/<Komponente>.vue` (bindet den Controller mit `useStore`), `element.ts` (`<flowaudit-<komponente>>`, in `src/registry.ts` → `ELEMENTS`), `index.ts`, Export in `src/index.ts` |
| React (`packages-js/ui-react`) | `src/<gruppe>/Flowaudit<Komponente>.tsx` (bindet denselben Controller mit `useStoreState`), `index.ts`, Export in `src/index.ts` |
| Parität | `ui-core/test/parity/cases-<gruppe>.ts` mit Beispielfällen, `ui/test/parity-<gruppe>.spec.ts` (Vue), `ui-react/test/parity/<gruppe>.spec.tsx` (Vue und React, DOM-Vergleich, Interaktion) |
| Doku | `docs/ui/<gruppe>.md` (Stub), Zeile in `docs/ui/react-paritaet.md`, README-API-Überblick (`scripts/docs/api_overview.py --write`) |

Das erzeugte Gerüst ist lauffähig: Lint, Typprüfung, alle erzeugten Tests
und das Gate sind grün (geprüft von `scripts/js/test/ui-new.test.mjs` in einer
Kopie des Workspaces). Danach wird der Fachinhalt ergänzt: Vertrag und Port
im Kern, Texte in `messages.ts`, Markup gleichzeitig in der SFC und der
React-Komponente, weitere Paritätsfälle.

### Vollständigkeits-Gate (`npm run ui:gate`)

`scripts/js/ui-parity-gate.mjs` leitet aus den Quellen ab, welche Komponenten
es gibt (TypeScript-Compiler-API, nichts wird ausgeführt): alle `.vue`-Exporte
der Einstiegspunkte von `packages-js/ui` und `packages-js/bpmn-vue`, die Web
Components aus `ELEMENTS` (`src/registry.ts`) bzw. aus `defineCustomElement`,
und alle Komponenten-Exporte (`.tsx`) der React-Pakete. Es gibt keine
Hand-Liste. Geprüft wird:

| Kennung | Regel |
|---|---|
| `react-missing` | Jede Vue-Komponente hat eine native React-Fassung: `Fa<Name>` → `<Name>`, Web Component `<flowaudit-x-y>` → `FlowauditXY`, sonst gleicher Name. |
| `vue-missing` | Umgekehrt: keine exportierte React-Komponente ohne öffentliches Vue-Gegenstück (Kontext-Provider ausgenommen). |
| `core-missing`, `core-export`, `core-controller`, `style-missing` | Je Gruppe gibt es `ui-core/src/<gruppe>/index.ts`, exportiert aus `ui-core/src/index.ts`, mit Controller (`createStore` oder `create…Controller`, auch in `packages-js/<gruppe>-core`), und `ui-core/styles/<gruppe>.css` in `styles/index.css`. BPMN: Controller in `bpmn-flowaudit/src/ui`. |
| `parity-cases` | Je Gruppe gibt es `cases-<gruppe>.ts` (oder `cases-<tag>.ts`, `packages-js/<gruppe>-core/test/parity/cases*.ts`), die ein Test mit der Vue-Fassung und ein Test mit der React-Fassung importieren (statische Importanalyse). |
| `vue-import`, `vue-dependency` | Das React-Paket importiert kein Vue (`vue`, `@vue/*`, `.vue`, das Vue-Paket) und hat es nicht als Laufzeit- oder Peer-Abhängigkeit (nur `devDependencies` für die Paritätstests). |

Das Gate läuft fail closed in `js-packages` und im Pflicht-Job
`code-quality-gate` (damit in `ci-ok`): Ein PR mit einer neuen
Vue-Komponente ohne React-Fassung wird rot.

**Ausnahmen** stehen nur in `quality/ui-parity-exceptions.json` – je Eintrag
Kennung (wie in der Ausgabe des Gates), Begründung und Ablaufdatum (höchstens
366 Tage). Abgelaufene Ausnahmen und Ausnahmen für geschlossene Lücken lassen
das Gate scheitern. Im `code-quality-gate` gilt der Ratchet gegen den
Vergleichsstand: keine neuen Kennungen, keine späteren Ablaufdaten – die
Datei darf nur schrumpfen.

## Ordnerkonvention

```
packages-js/ui-core/src/<gruppe>/   # Kern: messages, types, port, view, controller, index
packages-js/ui-core/styles/<gruppe>.css
packages-js/ui/src/<gruppe>/
  index.ts            # öffentliche Exporte der Gruppe
  element.ts          # ElementDefinition für die Web Component
  use<Name>.ts        # Vue-Anbindung des Controllers (useStore), falls mehrere SFC ihn teilen
  <Name>.vue          # Darstellung; höchstens 250 Zeilen je SFC
packages-js/ui-react/src/<gruppe>/Flowaudit<Name>.tsx
packages-js/ui-core/test/parity/cases-<gruppe>.ts
packages-js/ui/test/parity-<gruppe>.spec.ts
packages-js/ui-react/test/parity/<gruppe>.spec.tsx
packages-js/ui/demo/pages/<gruppe>/<Name>Page.vue
```

Komponenten heißen in Vue `Fa<Name>` oder fachlich (`KanbanBoard`); die
React-Fassung heißt wie die Vue-Komponente ohne `Fa`, Hauptkomponenten
`Flowaudit<Name>` passend zum Tag. Bezeichner sind englisch, sichtbare Texte
deutsch mit echten Umlauten und stehen ausschließlich in `messages.ts` des
Kerns.

## Was der Generator nicht erzeugt

- **Demo:** Seite in `demo/pages/<gruppe>/` anlegen und in `demo/pages.ts`
  (`DEMO_PAGES`) mit `id`, `title`, `group: 'Komponenten'` eintragen.
- **Browser-Test:** `e2e/<gruppe>.e2e.ts` (oder `.api-e2e.ts` mit Python-Backend).
- **REST-Umsetzung des Ports:** auf `requestJson`/`requestFile` aus
  `@auditcore/common` aufbauen, Vertrag in `docs/ui/<gruppe>-rest.md`.

Markup-Regeln für die React-Fassung: dasselbe Markup (Klassen, ARIA, Texte)
wie die Vue-SFC; Props wie in Vue, Ereignisse als `onXxx` mit den Nutzdaten,
`v-model` als gesteuerte Prop plus `onXxxChange`. Controller-Aufrufe nie vom
optionalen Callback abhängig machen (`props.onX?.(controller.tuWas())` ist
falsch).

## Regeln für Komponenten

- **Web-Component-tauglich:** Props mit Listen/Objekten brauchen Standardwerte
  (`rows: () => []`), weil das Element vor dem Setzen der Eigenschaften
  eingehängt wird. Ereignisse in kebab-case (`emit('card-move', …)`); die
  React-Fassung nennt sie `onCardMove` und übergibt dieselben Nutzdaten.
  Keine Namen nativer DOM-Ereignisse (`change`, `select`, `input`, `click`,
  `submit` …): im Light DOM steigen diese aus inneren Eingabefeldern bis zum
  Element auf und wären von den eigenen Ereignissen nicht zu unterscheiden
  (daher z. B. `board-change`, `board-select`).
- **Light DOM:** Elemente laufen ohne Shadow DOM; Stile stehen in `<style>`
  (nicht `scoped`), Klassen mit Präfix `fa-<komponente>__…`, Farben nur aus
  `--fa-*`-Variablen. Neue Token nur in `tokens.css` (hell und dunkel).
  Eine gemeinsame Stildatei einer Komponente (`src/<komponente>/<komponente>.css`)
  wird in `src/index.ts` **und** `src/elements.ts` importiert, nicht im
  `index.ts` der Komponente – dort entfernt das Tree-Shaking reine
  CSS-Importe (`sideEffects`).
- **Barrierefreiheit:** Tastaturbedienung für alles, was mit der Maus geht;
  ARIA-Rollen/-Beschriftungen, `aria-live` für Statusmeldungen, sichtbarer
  Fokus über `var(--fa-focus-ring)`, `prefers-reduced-motion` beachten.
- **Keine festen API-Aufrufe:** Daten und Speichern über Props, Ereignisse oder
  einen übergebenen Port (Interface), nie direkt `fetch`/axios. Eine
  mitgelieferte REST-Umsetzung des Ports baut auf `src/rest` auf:
  `requestJson`/`requestFile` (injizierbares `fetch`, Fehler als `RestError`
  mit Status und Code aus `{"error": {"code", "message"}}`), `createRunner`
  (Beschäftigt-Status und Fehlermeldung je Portanfrage) und `saveFile`.
- **Sprache:** jede Komponente hat eine optionale Prop `locale`; ohne sie gilt
  die per `createFlowauditUi({ locale })` bzw. `defineFlowauditElements({ locale })`
  gesetzte Sprache.
- **Qualität** (verbindlich, `docs/quality/code-quality.md`): TS strict mit
  `noUncheckedIndexedAccess`, kein `any` ohne begründete Zeilenausnahme,
  complexity ≤ 12, Dateien ≤ 400 Zeilen, Vue-SFC ≤ 250 Zeilen, Logik in
  Composables, Tabellen deklarativ.

## Tests

- **Einheit:** `npm run test -w packages-js/ui` (Vitest, happy-dom,
  `@vue/test-utils`). Pro Komponente mindestens: Rendern, Ereignisse,
  Tastaturbedienung, ARIA, Sprache; Composables ohne DOM.
- **Web Component:** Element über `defineFlowauditElements({ only: [...] })`
  registrieren, Eigenschaften setzen, Ereignis prüfen (Vorlage:
  `test/elements.spec.ts`).
- **React:** `npm run test -w packages-js/ui-react` (Vorlagen:
  `test/synopsis.spec.tsx` für Verhalten, `test/parity/*.spec.tsx` für den
  Vergleich mit der Vue-Fassung; Grenzen dort: complexity ≤ 10, Funktionen
  ≤ 60 Zeilen, `.tsx` ≤ 250 Zeilen, `react-hooks`-Regeln).
- **Browser:** `npm run demo:build -w packages-js/ui && npm run e2e -w packages-js/ui`
  (Playwright gegen die gebaute Demo; `FA_SCREENSHOTS=<ordner>` legt
  Bildschirmfotos ab). Jede Komponente ergänzt `e2e/<komponente>.e2e.ts`.
  Komponenten, deren Demo ein Python-Backend braucht (Stichprobe, Benford, Hochrechnung),
  legen `e2e/<komponente>.api-e2e.ts` an; `npm run e2e:api -w packages-js/ui`
  startet dafür `demo/api_server.py` (Python über `FA_DEMO_PYTHON`, mit den
  Extras `web` der Pakete und `uvicorn`) und die gebaute Demo mit Proxy `/api`.
- **Typen:** `npm run typecheck -w packages-js/ui` (vue-tsc).
- **Lint:** `npm run lint` prüft auch `.vue` (eslint-plugin-vue, höchstens
  250 Zeilen je SFC, complexity ≤ 12, kein `any`); das Code-Qualitäts-Gate
  (`python scripts/verify_code_quality.py --package js:ui`) misst dieselben Grenzen.
- **Gate und Generator:** `npm run ui:gate` (Vollständigkeit Vue ↔ React) und
  `npm run test:scripts` (Tests des Gates mit synthetischen Mini-Workspaces,
  Generator in einer Kopie des Workspaces).

## Befehle

```bash
npm install                                   # im Repository-Wurzelverzeichnis
npm run ui:neu -- <gruppe> <Komponente>       # Gerüst in Kern, Vue, React, Parität, Doku
npm run ui:gate                               # Vollständigkeits-Gate Vue ↔ React
npm run demo -w packages-js/ui                # Demo mit Hot Reload (Port 5190)
npm run build -w packages-js/ui               # dist/index.js, dist/elements.js, dist/ui.css
npm run build -w packages-js/ui-core
npm run build -w packages-js/ui-react
```
