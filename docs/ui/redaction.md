# PDF schwärzen (`PdfRedaction` ↔ `FlowauditPdfRedaction`)

Oberfläche zur zweistufigen Schwärzung aus `auditcore_pdf.redaction`: Datei und
Suchkriterien wählen, Fundstellen auf dem Seitenbild prüfen und um eigene
Bereiche ergänzen, dann genau die bestätigte Auswahl schwärzen lassen. Das
Ergebnis prüft der Dienst fail-closed nach, bevor er die Datei ausliefert.
REST-Vertrag: [redaction-rest.md](redaction-rest.md).

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/redaction/` (`createRedactionController`, `redactionReview`, `redactionMessages`, `createRedactionRestPort`) |
| Stil | `packages-js/ui-core/styles/redaction.css` (Präfix `fa-redaction`) |
| Vue / Web Component | `PdfRedaction` / `<flowaudit-pdf-redaction>` (`packages-js/ui/src/redaction/`) |
| React | `FlowauditPdfRedaction` (`packages-js/ui-react/src/redaction/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-redaction.ts` (Antworten des echten Dienstes aus `ui/demo/redaction_demo.py`) |
| Demo | Seite „PDF schwärzen“ (`ui/demo/pages/redaction/`), Backend in `ui/demo/api_server.py` |

## Einbindung

```ts
import { PdfRedaction, createRedactionRestPort } from '@auditcore/ui'

const port = createRedactionRestPort({ baseUrl: '/api/redaction' })
// <PdfRedaction :port="port" @redaction-completed="onDone" />
```

```tsx
import { FlowauditPdfRedaction, createRedactionRestPort } from '@auditcore/ui-react'

const port = createRedactionRestPort({ baseUrl: '/api/redaction' })
// <FlowauditPdfRedaction port={port} onRedactionCompleted={onDone} />
```

`createRedactionRestPort` nimmt dieselben `RestOptions` wie die übrigen Ports
(`baseUrl`, `headers`, `fetch`). Eine Anwendung mit eigenem
Backend setzt einen eigenen `RedactionPort` ein (`catalogue`, `plan`, `preview`,
`apply`).

## Vertrag der Komponente

| Eigenschaft | Typ | Bedeutung |
|---|---|---|
| `port` | `RedactionPort \| null` | Dienst; ohne Port erscheint nur der Hinweis „Kein Dienst angebunden“. |
| `locale` | `'de' \| 'en'` | Sprache (Standard: Seite bzw. `LocaleProvider`). |
| `urls` | `RedactionUrls` | Erzeugen und Freigeben von Objekt-URLs; Standard `URL.createObjectURL`. In Tests ersetzbar. |
| `file` | `Blob \| null` | Von der Anwendung bereitgestellte PDF. Statt des Dateifelds und seines Hilfetexts steht „Dokument“ mit dem Namen; „Neu beginnen“ (statt „Weiteres Dokument“) behält die Vorgabe. Eine andere Datei (neues Objekt) verwirft Plan und Fehlermeldung; den Blob daher stabil halten (State oder Memo), nicht bei jedem Rendern neu erzeugen. |
| `filename` | `string` | Name zu `file`, an den Port übergeben (Standard: Name der Datei, sonst `dokument.pdf`). |
| `terms` | `readonly string[]` | Startwerte der eigenen Begriffe; leere und doppelte entfallen. Übernommen bei geändertem Inhalt, danach frei änderbar. Kommen sie, während ein Plan läuft oder angezeigt wird, verfällt der Plan und das Formular zeigt die neuen Werte mit einem Hinweis; während des Schwärzens und im Ergebnis werden sie vorgemerkt und beim nächsten Schritt übernommen. Ein dann noch gemeldetes `redaction-completed` gehört zu den alten Kriterien, die neuen Werte sind darin nicht geschwärzt. |
| `patterns` | `readonly string[]` | Startwerte der Muster (Kennungen aus dem Katalog); nicht angebotene entfallen. Sonst wie `terms`. Beim Web Component `terms` und `patterns` als Eigenschaft setzen, nicht als Attribut; ein Attribut (Zeichenkette) wird übergangen. |

| Ereignis (Vue / Web Component) | React | `detail` |
|---|---|---|
| `redaction-planned` | `onRedactionPlanned` | `RedactionPlan` (enthält Klartext der Fundstellen) |
| `redaction-completed` | `onRedactionCompleted` | `RedactionResult` (`blob`, `filename`, `report` nur mit Zahlen) |
| `error` | `onError` | Meldung der abgelehnten Anfrage; bei `verification_failed` mit kurzen Textauszügen, daher nicht protokollieren |

Beispiel mit Vorgaben, etwa wenn der Server die Arbeitsfassung zusammenstellt
und der Port sie wieder an eigene Endpunkte schickt:

```tsx
<FlowauditPdfRedaction port={aktenPort} file={arbeitsfassung} filename="Akte 2026-17.pdf"
  terms={vorschlag.begriffe} patterns={['iban', 'email']} />
```

Ohne Oberfläche: `controller.provideFile(blob, name)` und
`controller.presetCriteria({ terms, patterns })`.

## Ablauf

1. **Suchkriterien:** PDF (Grenzen aus dem Katalog), Muster mit Prüfziffer,
   KI-Namenserkennung nur, wenn der Dienst sie anbietet, eigene Begriffe (ein
   Begriff je Zeile), Groß-/Kleinschreibung, ganze Wörter. Die Prüfung vor dem
   Senden (`redactionValidation`) deckt Datei, Größe, leere Kriterien und
   Begriffsgrenzen ab.
2. **Prüfansicht:** Seitenbild als PNG vom Dienst (je Seite zwischengespeichert)
   mit den Fundstellen der Seite. Ein Klick auf eine Markierung wählt sie ab
   oder wieder an. Daneben steht die Liste nach Fundtext gruppiert: Quellen
   lassen sich als Ganzes umschalten, die Gruppen haben Teilauswahl, ab acht
   Gruppen gibt es einen Filter, angezeigt werden jeweils 200 Gruppen.
   Versteckte Fundstellen (Metadaten, Lesezeichen, Formularfelder usw.) und
   Seiten ohne Textebene werden ausdrücklich genannt.
3. **Eigene Bereiche:** Rechteck mit dem Zeiger aufziehen oder „Bereich
   hinzufügen“ (Tastaturweg). Verschieben mit der Maus oder den Pfeiltasten,
   mit Umschalt in großen Schritten. Der Griff unten rechts vergrößert den Bereich, mit dem
   Zeiger oder den Pfeiltasten. Entfernen per Entf, Rücktaste oder ×. Die
   Grenzen je Seite und insgesamt kommen aus dem Katalog.
4. **Schwärzen:** Gesendet werden Auswahl, Bereiche und die Option „Metadaten
   und Anhänge bereinigen“. Der Bericht enthält nur Zahlen: Schwärzungen,
   Bereiche, entfernte versteckte Fundstellen, abgewählte Fundstellen, Seiten
   und Bereinigung. Danach folgen der Download, „Auswahl nachbearbeiten“
   (Plan und Auswahl bleiben) oder „Weiteres Dokument“.

Wird die Datei gewechselt oder führt „Zurück“ zu den Kriterien, verfallen Plan,
Auswahl, Bereiche und alle Objekt-URLs. Während des Schwärzens sind Auswahl,
Bereiche und Optionen gesperrt, damit das Ergebnis genau der gesendeten Auswahl
entspricht. Beim Entfernen der Komponente werden die Objekt-URLs freigegeben;
noch laufende Antworten werden verworfen.

## Datenschutz

Plan und Seitenbilder enthalten Klartext und bleiben nur im Arbeitsspeicher
des Browsers. Die Komponente speichert nichts in `localStorage` und schreibt
nichts in die Konsole. Das Ereignis `redaction-planned` gibt den Plan an die
Anwendung weiter; wer es abonniert, verantwortet den Umgang damit.

## Barrierefreiheit

Markierungen sind Schaltflächen mit `aria-pressed` und einer Beschriftung aus
Fundart und Text. Bereiche haben eigene Schaltflächen zum Verschieben,
Vergrößern und Entfernen, alle per Tastatur erreichbar. Quellen mit
Teilauswahl melden `aria-pressed="mixed"`. Beim Schrittwechsel (Prüfansicht,
Ergebnis, Formular) springt der Fokus auf die Überschrift des neuen Schritts,
nach dem Entfernen eines Bereichs auf „Bereich hinzufügen“. Der Seitenwechsel
ist `aria-live`. Auf dem stets hellen Seitenbild gelten feste Markierungsfarben
mit mindestens 3:1 Kontrast auch im Dunkelmodus, und `forced-colors` wird
unterstützt. Zwei Spalten gibt es ab 60rem Breite der Komponente selbst
(Container-Abfrage), nicht des Fensters.

## Nicht enthalten

- Stapelverarbeitung mehrerer Dateien. Der Vertrag ist bewusst auf eine Datei
  je Anfrage zugeschnitten; Stapel bleiben Sache der Anwendung.
- OCR für Seiten ohne Textebene. Diese Seiten werden gemeldet, Bereiche lassen
  sich dort von Hand setzen.
