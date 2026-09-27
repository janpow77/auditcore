# Schnittstellen

## Maschinenlesbare CLI (für zentrale Verwaltung, z. B. flow-agent)

| Befehl | Ergebnis | Exit |
|---|---|---|
| `auditcore-runner profil schema` | JSON-Schema des Profils (Formular dynamisch daraus bauen) | 0 |
| `auditcore-runner profil pruefen --datei <pfad\|-> --json` | `gueltig`, `probleme[]` (`feld`, `meldung`), `aktive_version`, `aenderungen[]` (Datei, Diff), `schritte[]`, `netzsperre_befehl` | 0 gültig, 1 Fehler |
| `auditcore-runner profil anwenden --datei <pfad\|-> --json [--erwartete-version N] [--quelle lokal\|flow-agent] [--wer …]` | wie oben plus `angewendet`, `konflikt`, `version`, `profil_hash`, `fehler[]` | 0 ok, 1 Fehler, 3 Konflikt |
| `auditcore-runner runner status --json`/`--schreiben` | Status (unten) | 0 |
| `auditcore-runner runner soll [KLASSE=N …]` | Soll-Datei lesen/setzen | 0 |
| `auditcore-runner runner status --streng` | wie oben; Exit 4 bei unbekannten Registrierungen | 0, 4 |
| `auditcore-runner scaleset anzeigen` | Scale-Set-Name, Soll, Warteschlange und Statistik je Klasse | 0 |
| `auditcore-runner scaleset loeschen [--klasse K] [--trockenlauf]` | Scale-Sets dieses Rechners löschen | 0 |
| `auditcore-runner workflows vorlage runner-wahl [--ziel DIR]` | Entscheidungs-Job (`workflow_call`) ausgeben oder kopieren | 0, 1 |

`anwenden` bricht nie laufende Jobs ab: Units werden neu geschrieben und
geladen, neue Instanzen gestartet; überzählige Instanzen ruhen, weil der
Supervisor Profil und Soll vor jeder Registrierung neu liest.

**Konflikte:** Wird mit `--erwartete-version` die Version gesendet, auf der eine
Änderung beruht, und hat sich das Profil inzwischen geändert (lokal oder zentral),
wird nichts geschrieben; die Antwort nennt Version, letzte Quelle und den Diff.

## Status-Datei (lesend)

`~/.local/state/auditcore-runner/status.json`, jede Minute (Timer
`auditcore-runner-status.timer`), Schema `auditcore-runner/status/1`:
`rechner`, `profil_schema`, `profil_version`, `profil_hash`, `aenderung`,
`sync`, `ziel`, `soll_quelle`, `backend`, `auth_art`, `hardware`,
`klassen.<k>.{aktiv,max,soll,gruende,instanzen_aktiv,registriert,belegt,warteschlange}`
(mit Scale-Sets zusätzlich `nachfrage_soll`, `scale_set`, `scale_set_statistik`),
`image_vorhanden`, `netz_vorhanden`, `netzsperre_aktiv`, `unbekannte_runner`,
`unbekannte_runner_details[]` (`name`, `id`, `online`, `belegt`, `labels`,
`passt_zu_klasse`), `github_rest_kontingent`.

`warteschlange` stammt aus der Nachfrage-Datei (unten) und ist `null`, wenn sie
fehlt oder älter als 5 Minuten ist; ein externer Regler muss GitHub nicht selbst
abfragen.

## Nachfrage-Datei (lesend)

`~/.local/state/auditcore-runner/nachfrage.json`, Schema
`auditcore-runner/nachfrage/1`: `quelle` (`scaleset` oder `regler`),
`zeit_unix`, `klassen.<k>.{warteschlange,soll,statistik,scale_set}`. Beim Backend
`scaleset` schreibt sie der Listener nach jeder Nachricht (mindestens einmal je
Long-Poll); `soll` = min(Kapazität, Minimum + zugewiesene Jobs) begrenzt dann
die Supervisoren zusätzlich. Sonst schreibt der lokale Regler nur die
Warteschlange.

## Soll-Datei (Vertrag mit einem externen Regler)

Schema `data/schemas/runner-pool.schema.json`: `klassen.<k>.soll`, optional
`gruende[]`, `nutzer_vorrang` (alle GPU-Runner räumen sofort), `karten_gesperrt[]`
(UUIDs sofort räumen, nicht vergeben).

## JSON-API der lokalen Oberfläche (`auditcore-runner ui`)

| Methode, Pfad | Inhalt |
|---|---|
| `GET /api/status` | Status wie oben, plus `nur_lesen` |
| `GET /api/profil` | `profil`, `profil_hash`, `hardware`, `probleme`, `netzsperre_befehl`, `nur_lesen` |
| `POST /api/profil/pruefen` | Body `{"profil": {...}}` → wie `profil pruefen` |
| `POST /api/profil/anwenden` | Body `{"profil": {...}, "erwartete_version": N}` → wie `profil anwenden`; 409 bei Konflikt, 422 bei Fehlern |
| `GET /api/werkzeuge` | Katalog (`im_image`: installierte Version) und Werkzeug-Einstellungen je Prüfprofil |
| `POST /api/werkzeuge` | Werkzeug-Einstellungen dieses Rechners (`auditcore-runner/werkzeuge/1`) |
| `GET /metrics` | Prometheus |

Schreibende Aufrufe: nur Loopback, Kopfzeile `X-Auditcore-Runner: 1`, JSON-Body
bis 256 KiB.

## Oberfläche (`@auditcore/ui`, Gruppe `runner`)

Die Oberfläche ist die Komponentengruppe `runner` (`docs/ui/runner.md`; Bündel
`data/web/runner-elements.js`, erzeugt mit `npm run runner:bundle`, in der CI per
Bytevergleich geprüft). Sie ist eine Komponentengruppe in `@auditcore/ui` (Vue, natives
React, Web Component) und nutzt ausschließlich diese API. Sie braucht die
Bereiche **Status**, **Einstellungen** (alle Profilfelder mit Validierung und
Diff vor dem Anwenden; root-Schritte nur als Befehl zum Kopieren), **Werkzeuge**
(je Prüfprofil an/aus, Zeitlimit, Priorität; installierte Version im Image) und
**Prioritäten** (Rangfolge `prioritaeten[]` mit `rang`, `verdraengbar`, `min`).
Sie zeigt `version`, `aenderung` und `sync` an und bei einem Konflikt (409) beide
Stände mit Diff – „auf dem Rechner geändert“ gegenüber „zentral geändert“.

Hinweise zum heutigen Stand der API, die die Oberfläche berücksichtigt:
Fehler beim Anwenden kommen mit HTTP 200 und `gueltig: false` (nicht 422);
ein Konflikt (409) trägt nur `fehler` ohne Diff – die Oberfläche lädt dann
`GET /api/profil` und zeigt die Unterschiede feldweise selbst; Fehlerpfade in
Listen lauten `gpus[0].uuid`.
