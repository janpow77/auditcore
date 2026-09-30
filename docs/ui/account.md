# Konto, Mandant und Administration

Implementiert als `auditcore_account==0.1.1` mit `AccountWorkspace` (Vue),
`FlowauditAccountWorkspace` (React) und `<flowaudit-account-workspace>` (Custom Element).
Der Generator `ui:neu` wurde für das Grundgerüst verwendet. Formularzustand,
Portvertrag, Kamera-/Zuschnittlogik und CSS liegen gemeinsam in `@auditcore/ui-core`.

## Einbindung

```ts
import { createAccountRestPort } from '@auditcore/ui-core'
const port = createAccountRestPort({
  request: authenticatedRequest,  // Session, CSRF und HTTP-Fehlerabbildung der Anwendung
  upload: uploadAccountImage,     // autorisierte Multipart-Route → { id, url }
  imageUrl: protectedImageUrl,
})
```

```vue
<script setup lang="ts">
import { AccountWorkspace } from '@auditcore/ui'
import '@auditcore/ui/style.css'
// port stammt aus dem oben konfigurierten Anschluss.
defineProps<{ port: import('@auditcore/ui-core').AccountPort }>()
</script>
<template><AccountWorkspace :port="port" /></template>
```

```tsx
import { FlowauditAccountWorkspace } from '@auditcore/ui-react'
import '@auditcore/ui-core/style.css'
<FlowauditAccountWorkspace port={port} locale="de" />
```

Der Host wählt den Mandanten aus seinem vorhandenen Mandantenwechsel und übergibt
einen dazu gebundenen Port. Für einen Kontextwechsel muss die Anwendung zunächst
Speichern/Verwerfen anbieten; ein neuer `port` setzt den lokalen Formularzustand
zurück. Die komponenteninterne Navigation verhindert einen Wechsel bei ungespeicherten
Änderungen. Veraltete Antworten eines früheren Ports werden ignoriert.

| HTTP-Vertrag des Ports | Python-Anschluss im authentifizierten Host |
|---|---|
| `GET /api/account/documents` | `workspace.list(actor, tenant)` |
| `GET /api/account/documents/{id}` | `workspace.read(actor, id, tenant)` |
| `POST /api/account/documents/{id}` mit `{revision, values}` | `workspace.save(actor, id, revision, values, tenant)` |
| Host-spezifischer Bild-Upload | Formular/Feldrechte prüfen, dann `AssetService.upload` |
| Host-spezifische Bildauslieferung | `AssetService.read`, `image/png`, privater Cache |

Dokument-IDs müssen als ein URL-Segment kodiert/dekodiert werden. `member/...`,
`access/...` und `role/...` sind opaque IDs, keine Dateipfade. Der Host muss Typen,
Größen und Inhalt der JSON-Eingaben prüfen. `AccountError.code` bildet er auf
seine HTTP-Fehler ab (`conflict` → 409, fehlende Rechte → 403, ungültige Werte → 422).
Die Oberfläche zeigt Fehler, behält den Entwurf und überschreibt nicht automatisch.
Nach 409: Entwurf sichern, neu laden, Änderungen bewusst übernehmen.

`WorkspaceResult` enthält serverseitige Sitzungs-/Versandinformationen. Ausschließlich
`document` wird als erfolgreiche Formularantwort serialisiert. Details und
Integrationspflichten stehen im [Paket-README](../../packages/auditcore_account/README.md).

## Ansichten und Verhalten

- Persönliche Angaben einschließlich Bild-Upload, optionaler Webcam und quadratischem
  Zuschnitt mit Zoom und Position. Kamera erst nach ausdrücklichem Klick; Tracks
  schließen bei Abbruch, Aufnahme, Unmount und spät eintreffender Berechtigung.
- Dienstliche Funktion/Kontakt pro Mitgliedschaft; selbst bearbeitbar sind standardmäßig
  die Kontaktdaten, organisatorische Zuordnungen benötigen Verwaltungsrechte.
- Passwortwechsel mit Bestätigung; extern verwaltete Angaben sind schreibgeschützt.
- Mandantenstammdaten und Corporate Design mit Logo-Varianten, Kontrastprüfung,
  Schriftkatalog sowie Dokumentkopf/-fuß. Vorschau zeigt Farben und Textschrift.
- Begrüßung mit Klartextvorschau und ungefährlichen Platzhaltern. Der Kern liefert
  zusätzlich einen begrenzten HTML-Renderer und `first_visit_welcome`/Quittierung.
- Verwaltung: Nutzer/Mandanten anlegen, Mitgliedschaften, Rollen, Konto- und
  Mandantenstatus, Einladungen, Reset und Startpasswort. Systemrollen sind geschützt.
- Zusätzliche Fachformulare werden aus registrierten Erweiterungen aufgebaut.

Corporate Design ist ein Datenvertrag. Die Anwendung verwendet die validierten
Farben für `--fa-color-accent`, `--fa-color-accent-hover`, `--fa-color-accent-contrast`
und die freigegebene Schrift für `--fa-font-sans`. Schriftdateien und Dokumentfonts
müssen im Host installiert/lizenziert sein. Die Bibliothek lädt keine externen Fonts
und generiert noch keine Dokumente. Statusfarben und Formularstruktur bleiben gemeinsam.

Die Oberfläche unterstützt den vorhandenen Hell-/Dunkelmodus, Tastaturbedienung,
Statusmeldungen und mobile einspaltige Formulare. Deutsche/englische UI-Rahmentexte
sind gemeinsam; fachliche Labels liefert der Host (Python standardmäßig Deutsch).
Eigenschaften: `port`, `locale`; Ereignisse: `item-select`/`onItemSelect`, `error`/`onError`.

## Demo und Prüfungen

```bash
npm run build -w @auditcore/ui-core
npm run demo -w @auditcore/ui
# http://localhost:5190/#/konto
```

Die Demo nutzt aus dem Python-Formularadapter erzeugte synthetische Daten und
flüchtige Speicherung. Sie simuliert keine echte Anmeldung oder E-Mail-Zustellung.
`createAccountMemoryPort` ist ausschließlich für solche Demos und Tests gedacht.

Controller-Tests prüfen Versionskonflikte, Entwurferhalt, Anschlusswechsel und
Kamerafreigaben. Vue-/React-Parität prüft Rendering und Formularinteraktion.
Browserprüfungen ergänzen Profiländerung, Vorschau, mobile Darstellung und Barrierefreiheit.
Die drei vorhandenen Anwendungen werden erst im nächsten Schritt angeschlossen.

[PDF der implementierten Ansichten](entwuerfe/konto-bibliothek-v0.1.pdf) · [Prüfnachweis](../reports/account-library-20260929.json).
