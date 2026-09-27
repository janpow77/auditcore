# Runner-Konsole (`RunnerConsole` ↔ `FlowauditRunnerConsole`)

Oberfläche der verteilten Prüfbank `auditcore_runner` (Lastenheft 102AC, RUN-050 bis RUN-052):
Status, Einstellungen, Werkzeuge und Prioritäten **eines** Rechners. Die Komponente spricht
ausschließlich die JSON-API von `auditcore-runner ui`
(`packages/auditcore_runner/docs/api.md`); nutzerspezifische Werte kommen nur aus dieser API,
nie aus dem Code.

Gerüst erzeugt mit `npm run ui:neu -- runner RunnerConsole`; die vier Bereiche sind Reiter
einer Komponente (eine Web Component für die Paketoberfläche).

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/runner/` – `controller.ts` (Zustand), `aktionen.ts` (Prüfen, Anwenden, Konflikt, Werkzeuge), `profil.ts` (Entwurf, Unterschiede, Prioritäten), `view.ts` (Ansichtsmodelle), `port.ts` (Speicher- und REST-Port), `messages.ts` |
| Stil | `packages-js/ui-core/styles/runner.css` (nur `--fa-*`-Token, hell und dunkel) |
| Vue / Web Component | `RunnerConsole` / `<flowaudit-runner-console>` (`packages-js/ui/src/runner/`, Teile unter `components/`) |
| React (nativ) | `FlowauditRunnerConsole` (`packages-js/ui-react/src/runner/`, Teile unter `parts/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-runner.ts` (8 Fälle, 4 Interaktionsfolgen) |
| Eigenständiges Bündel | `packages-js/ui/runner-bundle/` → `npm run build:runner -w @auditcore/ui` |

## Vertrag

Eigenschaften: `port` (hat Vorrang) oder `api` (Basis-URL, z. B. `/api`; als Attribut der Web
Component), `ansicht` (`status` | `einstellungen` | `werkzeuge` | `prioritaeten`), `locale`.
Ereignisse: `applied` (neue Profilversion; React `onApplied`), `error` (React `onError`).

```html
<script type="module" src="/runner-elements.js"></script>
<flowaudit-runner-console api="/api"></flowaudit-runner-console>
```

```ts
import { createRunnerRestPort } from '@auditcore/ui-core'
<RunnerConsole :port="createRunnerRestPort({ baseUrl: '/api' })" />          // Vue
<FlowauditRunnerConsole port={createRunnerRestPort({ baseUrl: '/api' })} /> // React
```

Der REST-Port sendet bei schreibenden Aufrufen die Kopfzeile `X-Auditcore-Runner: 1`,
übersetzt `{"fehler": …}` in lesbare Meldungen und macht aus HTTP 409 beim Anwenden ein
Ergebnis mit `konflikt: true`.

## Bereiche

- **Status:** Rechner, Profilversion, Abgleich (lokal oder zentrale Verwaltung), Ziel,
  Soll-Quelle, Anmeldung bei GitHub (`auth_art`), letzte Änderung (Zeit, Quelle), Image, Netzsperre, GitHub-Kontingent,
  Runner-Version mit Frist (sobald geliefert); Klassen mit Soll, Max., Instanzen, registriert,
  belegt, Warteschlange (sobald geliefert) und Begründung; Hardware. Warnungen: unbekannte
  Runner-Registrierungen, fehlendes Image, inaktive Netzsperre, Nur-Lesen.
- **Einstellungen:** Felder nur für Werte, die das Profil enthält (allgemein, Regelung,
  Thermikquelle, Netz, je Klasse, je Grafikkarte). Klassen sind frei benennbar (Profil-Schema 3):
  hinzufügen und umbenennen mit derselben Prüfung wie im Backend (a–z, 0–9, Bindestrich,
  höchstens 31 Zeichen, eindeutig); Umbenennen zieht Kartenzuordnung, Prioritäten und das
  gleichnamige Label mit. Je Klasse Auswahl `art` (`cpu`/`gpu`); Grafikspeicher und die
  Kartenauswahl erscheinen nur bei Klassen der Art `gpu` (beim Wechsel auf `cpu` wird
  `vram_mb` 0). „Prüfen“ zeigt Fehler am Feld, Datei-Diffs,
  Schritte und den root-Befehl der Netzsperre zum Kopieren; „Anwenden“ sendet die erwartete
  Version. Bei einem Konflikt stehen Entwurf und gespeicherter Stand feldweise nebeneinander
  (letzte Quelle, z. B. zentrale Verwaltung), mit „Gespeicherten Stand übernehmen“ oder
  „Entwurf trotzdem anwenden“.
- **Werkzeuge:** je Prüfprofil Werkzeuge an/aus, Zeitlimit, Priorität; installierte Version im
  Runner-Image.
- **Prioritäten:** Rangfolge `prioritaeten[{klasse, rang, verdraengbar, min}]` mit
  Hoch/Runter-Schaltflächen (Tastatur), „verdrängbar“, Mindestanteil und Vorschau, wer bei
  Platzmangel zuerst weicht; angewendet über denselben Prüfen/Anwenden-Weg.

Barrierefreiheit: Reiter mit `tablist`/`tab`/`tabpanel` und Pfeiltasten, Beschriftungen an
allen Feldern, Fehler über `aria-invalid`/`aria-describedby`, Meldungen als `status`/`alert`.

## Auslieferung im Python-Paket

`npm run build:runner -w @auditcore/ui` erzeugt `packages-js/ui/runner-bundle/dist/runner-elements.js`
(ein ES-Modul mit Vue, Kern und Stilen, registriert nur `<flowaudit-runner-console>`). Das Paket
`auditcore_runner` legt die Datei als Paketdaten unter `src/auditcore_runner/data/web/` ab und
liefert sie über `auditcore-runner ui` aus; auf dem Zielrechner ist kein Node nötig.

## Bildschirmfotos

Synthetische Daten: [Status](screenshots/runner-1-status.png),
[Einstellungen mit Vorschau](screenshots/runner-2-einstellungen.png),
[Konflikt](screenshots/runner-3-konflikt.png), [Werkzeuge](screenshots/runner-4-werkzeuge.png),
[Prioritäten dunkel](screenshots/runner-5-prioritaeten-dunkel.png),
[Einstellungen dunkel](screenshots/runner-6-einstellungen-dunkel.png).
