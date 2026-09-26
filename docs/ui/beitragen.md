# Beitragen zu @flowaudit/ui

`@flowaudit/ui` (`packages-js/ui`) ist das gemeinsame Oberflächenpaket der
FlowAudit-Anwendungen. Jede Komponente gibt es

1. als **Vue-3-Komponente** (`import { FaTable } from '@flowaudit/ui'`),
2. als **Web Component** `<flowaudit-<name>>` (`@flowaudit/ui/elements`),
3. als **native React-18-Komponente** in `@flowaudit/ui-react`
   (`packages-js/ui-react`) – Tabelle, Synopse, VVT, DSFA, Geo-Karte,
   Risiko-Merkmale, Screening, Stichprobe, Benford, Belegerkennung und Kanban (React 18 und 19).

Fachlogik, Texte, Verträge, View-Modelle, Zustandsautomaten und Stile liegen
framework-frei in **`@flowaudit/ui-core`** (`packages-js/ui-core`); Vue und
React binden sie nur an (Vue: `useStore`, React: `useStoreState`). Keine
Fachlogik doppelt in Vue und React.

Grundlagen, die alle Komponenten nutzen: Designtoken (`ui-core/styles/tokens.css`,
CSS-Variablen `--fa-*`, Hell/Dunkel), Sprache (`src/i18n`, Deutsch vollständig,
Englisch vorbereitet), Basiskomponenten (`FaButton`, `FaIcon`, `FaDialog`,
`FaTable`, `FaBadge`, `FaTextField`) und Composables (`useFocusTrap`, `useId`,
`useTheme`, `useI18n`).

## Ordnerkonvention

```
packages-js/ui/src/<komponente>/
  index.ts            # öffentliche Exporte der Komponente
  element.ts          # ElementDefinition für die Web Component
  messages.ts         # defineMessages({ de: {...}, en: {...} })
  use<Name>.ts        # Logik als Composable(s), ohne DOM-Zugriff testbar
  <Name>.vue          # Darstellung; höchstens 250 Zeilen je SFC
  <Teil>.vue          # weitere Teilkomponenten
packages-js/ui/test/<komponente>/*.spec.ts
packages-js/ui/demo/pages/<komponente>/<Name>Page.vue
```

`<komponente>` ist kurz, klein und englisch (`kanban`, `synopsis`, `risk`,
`screening`, `sampling`). Komponenten heißen in Vue `Fa<Name>` oder fachlich
(`KanbanBoard`); Bezeichner sind englisch, sichtbare Texte deutsch mit echten
Umlauten und stehen ausschließlich in `messages.ts`.

## Registrierung

1. **Vue-Export:** in `src/index.ts` eine Zeile `export * from './<komponente>'`.
2. **Web Component:** in `src/<komponente>/element.ts`

   ```ts
   import type { ElementDefinition } from '../elements/define'
   import RiskMatrix from './RiskMatrix.vue'
   export const riskMatrixElement: ElementDefinition = { tag: 'flowaudit-risk-matrix', component: RiskMatrix }
   ```

   und in `src/registry.ts` in die Liste `ELEMENTS` aufnehmen. Namen immer
   `flowaudit-<name>` in Kleinbuchstaben mit Bindestrich (ein Test prüft das).
3. **Kern:** Logik, Texte (`messages.ts`), Datentypen, Port und einen
   Controller (`createStore` + reine Selektoren) in
   `packages-js/ui-core/src/<komponente>/` anlegen; Stile nach
   `packages-js/ui-core/styles/<komponente>.css` (in `styles/index.css` aufnehmen).
4. **React:** in `packages-js/ui-react/src/<komponente>/` die native
   Komponente mit demselben Markup (Klassen, ARIA, Texte) wie die Vue-SFC;
   Props wie in Vue, Ereignisse als `onXxx` mit den Nutzdaten, `v-model` als
   gesteuerte Prop plus `onXxxChange`. In `src/index.ts` exportieren.
   Paritätsfälle in `ui-core/test/parity/cases*.ts` ergänzen; der Test in
   `ui-react/test/parity` vergleicht Vue und React (Erwartungen, normalisiertes
   DOM, Formularzustand, auch nach Interaktionen).
5. **Demo:** Seite in `demo/pages/<komponente>/` anlegen und in
   `demo/pages.ts` (`DEMO_PAGES`) mit `id`, `title`, `group: 'Komponenten'`
   eintragen.

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
  Komponenten, deren Demo ein Python-Backend braucht (Stichprobe, Benford),
  legen `e2e/<komponente>.api-e2e.ts` an; `npm run e2e:api -w packages-js/ui`
  startet dafür `demo/api_server.py` (Python über `FA_DEMO_PYTHON`, mit den
  Extras `web` der Pakete und `uvicorn`) und die gebaute Demo mit Proxy `/api`.
- **Typen:** `npm run typecheck -w packages-js/ui` (vue-tsc).
- **Lint:** `npm run lint` prüft auch `.vue` (eslint-plugin-vue, höchstens
  250 Zeilen je SFC, complexity ≤ 12, kein `any`); das Code-Qualitäts-Gate
  (`python scripts/verify_code_quality.py --package js:ui`) misst dieselben Grenzen.

## Befehle

```bash
npm install                                   # im Repository-Wurzelverzeichnis
npm run demo -w packages-js/ui                # Demo mit Hot Reload (Port 5190)
npm run build -w packages-js/ui               # dist/index.js, dist/elements.js, dist/ui.css
npm run build -w packages-js/ui-core
npm run build -w packages-js/ui-react
```
