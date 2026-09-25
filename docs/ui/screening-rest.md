# REST-Vertrag Screening-Trefferprüfung

Vertrag `auditcore_registry_sources.screening_review/1`. Serverseite:
`auditcore_registry_sources.web` (ab `auditcore_registry_sources` 0.2.0),
Oberfläche: `<flowaudit-screening-review>` aus `@flowaudit/ui` bzw. der
React-Wrapper `ScreeningReview` aus `@flowaudit/ui-react`.

**Ein Treffer ist ein Prüfhinweis, keine Feststellung.** Die Schnittstelle
hält fest, *wer* einen Hinweis *mit welcher Begründung* bestätigt, verworfen
oder zurückgestellt hat. Sie ersetzt weder die Identitätsprüfung am Vorgang
noch die Rechtsprüfung einer Bereitstellung.

## Einbindung

| Baustein | Herkunft | Pflicht des Consumers |
|---|---|---|
| `ScreeningReviewService` | Kern, ohne Web-Framework | Konfiguration (Vier-Augen-Regel, Höchstalter der Listen) |
| `SnapshotProvider` | Protocol | Listenbestand laden, `as_of` = Stand laut Quelle (nicht Ladezeit) |
| `ReviewStore` | Protocol; `InMemoryReviewStore` nur für Tests/Demo | dauerhafte Ablage, Compare-and-Append, Sichtbarkeit je Mandant |
| `create_routes` / `create_app` | `web.http`, Extra `web` (Starlette ≥ 0.26.1) | Einhängen, Identitäts-Resolver |
| `create_router` | `web.fastapi_router`, Extra `fastapi` (FastAPI ≥ 0.95.2) | wie oben |

```python
from starlette.routing import Mount
from auditcore_registry_sources.web import ScreeningReviewService
from auditcore_registry_sources.web.http import create_routes

service = ScreeningReviewService(
    provider,                        # SnapshotProvider des Consumers
    store,                           # ReviewStore des Consumers
    four_eyes_outcomes=["confirmed"],  # Bestätigen immer mit Zweitprüfung
    stale_after_days=7,              # ohne Angabe: Alter wird gezeigt, nicht bewertet
)
routes = [Mount("/api/screening", routes=create_routes(service, identify))]
```

`identify(request) -> Actor | None` (synchron oder `async`) liefert die bereits
angemeldete Person aus der Sitzung des Consumers; `None` ergibt 401. Die
Bibliothek authentisiert nicht und kennt keine Rollen. Wer entscheiden darf,
prüft der Consumer im Resolver oder in einer vorgeschalteten Middleware.

## Pflichten des Consumers (Datenschutz und Betrieb)

- Prüfläufe enthalten personenbezogene Daten (Namen, Geburtsdaten). Aufbewahrung,
  Löschfristen, Zugriffsrechte und Mandantentrennung liegen beim `ReviewStore`
  bzw. der Anwendung. Die Bibliothek löscht nichts und protokolliert nichts nach außen.
- Schreibende Anfragen müssen `Content-Type: application/json` tragen (sonst 415).
  Das hält einfache Formular-Posts fremder Seiten ab. Bei Cookie-Sitzungen
  bleibt ein CSRF-Schutz Aufgabe der Anwendung.
- Anfragen über 256 KiB werden mit 413 abgelehnt, höchstens 200 Namen je Prüflauf.
- Die Anwendbarkeit (Benutzer, Entscheidungen, Vier-Augen-Prinzip) ist im
  `ApplicabilityContext` des Consumers zu erfassen; der Kontext der Bibliothek
  beschreibt nur die Berechnung.

## Endpunkte

Alle Pfade relativ zum Einhängepunkt (Vorgabe `/api/screening`). Antworten sind
JSON mit `Cache-Control: no-store`.

| Methode | Pfad | Zweck | Erfolg |
|---|---|---|---|
| GET | `/settings` | Screening-Profile, Vier-Augen-Regel, Höchstalter | 200 |
| GET | `/sources` | Quellenstand aller Listen | 200 |
| GET | `/runs` | Prüfläufe (Kurzfassung, neueste zuerst) | 200 |
| POST | `/runs` | Prüflauf anlegen und ausführen | 201 |
| GET | `/runs/{run_id}` | Prüflauf mit Treffern und Prüfstatus, filterbar | 200 |
| GET | `/runs/{run_id}/log` | Protokoll | 200 |
| POST | `/runs/{run_id}/hits/{hit_id}/decision` | bestätigen / verwerfen / zurückstellen | 200 |
| POST | `/runs/{run_id}/hits/{hit_id}/second-review` | Zweitprüfung (Vier-Augen) | 200 |

### `GET /settings`

```json
{
  "contract": "auditcore_registry_sources.screening_review/1",
  "profiles": [
    {"id": "audit_designer.sanctions_screening", "version": "2026.09.2",
     "fingerprint": "9e72…", "status": "USER_DECIDED", "kind": "sanctions",
     "legal_status": "…", "default_min_score": 70.0,
     "scale": {"min": 0.0, "max": 100.0}, "recommended": true}
  ],
  "four_eyes_outcomes": ["confirmed"],
  "stale_after_days": 7
}
```

Nur Profile mit einem von der Oberfläche unterstützten Verfahren erscheinen:
`rapidfuzz_token_set` (Art `sanctions`, Skala 0–100) und `token_f1`
(Art `pep`, Skala 0–1). `recommended` folgt `recommended_profile()`; ein
Profil wird nie stillschweigend gewählt, die Anfrage nennt es ausdrücklich.

### `GET /sources`

```json
{
  "checked_at": "2026-09-25T12:00:00Z",
  "sources": [
    {"list": {"key": "eu_fsf", "name": "Konsolidierte Finanzsanktionsliste der Union (FSF)",
              "issuer": "Europäische Kommission", "provider": "OpenSanctions",
              "data_licence": {"status": "REVIEW_REQUIRED", "note": "…"}, "…": "…"},
     "kind": "sanctions", "entry_count": 3, "as_of": "2026-09-22T18:00:00Z",
     "retrieved_at": null, "content_sha256": null, "note": null, "searchable": true,
     "freshness": {"status": "current", "label": "aktuell", "age_days": 2.8,
                   "stale_after_days": 7}}
  ]
}
```

`freshness.status`: `current` (aktuell), `stale` (veraltet, älter als
`stale_after_days`), `unknown` (Stand unbekannt – `as_of` fehlt oder ist
unlesbar), `not_judged` (kein Höchstalter konfiguriert). Eine Liste ohne
Einträge ist `searchable: false` und wird im Prüflauf als *nicht abgefragt*
geführt.

### `POST /runs`

```json
{
  "kind": "sanctions",
  "profile": {"id": "audit_designer.sanctions_screening", "version": "2026.09.2"},
  "subjects": [
    {"name": "Maximilian Beispielmann", "birth_date": "1970-03-14", "country": "de",
     "schema": "Person", "reference": "Auftragnehmer Los 2"}
  ],
  "lists": ["eu_fsf", "un_sc"],
  "min_score": 70,
  "limit": 15,
  "case_reference": "Vorgang 2026/0001"
}
```

| Feld | Pflicht | Regel |
|---|---|---|
| `kind` | ja | `sanctions` oder `pep`; muss zum Verfahren des Profils passen |
| `profile` | ja | `{id, version}` eines paketierten Screening-Profils |
| `subjects` | ja | 1–200 Objekte, `name` Pflicht (Mindestlänge laut Profil); `birth_date`, `country`, `schema`, `reference` optional |
| `lists` | nein | Listenkennungen der Art; ohne Angabe alle Listen der Art |
| `min_score` | nein | Sanktionen: Bereich laut Profil (z. B. 50–100); PEP: über 0 bis 1 |
| `limit` | nein | 1–100, Vorgabe 15 |
| `case_reference` | nein | freier Vorgangsbezug, höchstens 500 Zeichen |

Antwort (201) ist die Laufansicht wie bei `GET /runs/{run_id}`. Der
Quellenstand der verwendeten Listen wird **zum Zeitpunkt des Laufs** in
`sources` festgehalten; spätere Aktualisierungen ändern ihn nicht.

### `GET /runs/{run_id}`

Kopf (auch in `GET /runs`): `run_id`, `created_at`, `created_by`, `kind`,
`case_reference`, `profile` (mit Fingerabdruck), `subject_count`,
`subjects_with_hits`, `subjects_incomplete`, `hit_count`, `review_counts`
(je Prüfstatus), `review_complete` (keine offenen, zurückgestellten oder
wartenden Treffer), `last_sequence`. Dazu `request`, `sources` und `subjects`.

Je geprüftem Namen (`subjects[]`): `subject_id` (`s1`, `s2` …), `input`,
`status` (`HITS`, `NO_HITS`, `INCOMPLETE` = nicht alle Listen abgefragt,
`NOT_SEARCHED`), `normalized_query`, `min_score`, `findings[]` (je Liste:
`searched`, `entry_count`, `as_of`, `hit_count`, `note`), `hits[]`,
`hits_before_filter`, `total_hits`, `truncated`, `notice`, `limitations[]`.

Je Treffer (`hits[]`):

```json
{
  "hit_id": "hd1a579414038050b", "subject_id": "s1",
  "list_key": "eu_fsf", "list_name": "Konsolidierte Finanzsanktionsliste der Union (FSF)",
  "entry": {"entry_id": "eu-001", "schema": "Person", "name": "Maximilian Beispielmann",
            "aliases": ["Max Beispielmann"], "aliases_total": 1,
            "birth_date": "1970-03-14", "countries": "de",
            "addresses": "Musterstraße 1, 12345 Musterstadt", "identifiers": "",
            "sanctions": "…", "program_ids": "…", "first_seen": "", "last_seen": "",
            "dataset": ""},
  "matched_name": "Maximilian Beispielmann", "matched_field": "name",
  "raw_score": 100.0, "score": 100.0, "confidence": "exact",
  "dob_conflict": false, "country_conflict": false, "below_min_score": false,
  "indicators": [],
  "breakdown": {
    "method": "rapidfuzz_token_set", "scale": {"min": 0.0, "max": 100.0},
    "steps": [
      {"step": "normalization", "label": "Vergleichsform der Eingabe",
       "value": "maximilian beispielmann",
       "detail": "Normalisierungsprofil audit_designer.sanctions 2026.09.3"},
      {"step": "normalization",
       "label": "Vergleichsform der getroffenen Schreibweise (Hauptname)",
       "value": "maximilian beispielmann", "detail": "Maximilian Beispielmann"},
      {"step": "base", "label": "Namensähnlichkeit (Token-Set-Vergleich, …)", "points": 100.0},
      {"step": "adjustment", "kind": "date_of_birth", "label": "Geburtsjahr stimmt überein.",
       "points": 6.0},
      {"step": "adjustment", "kind": "country", "label": "Land stimmt überein.", "points": 4.0},
      {"step": "clamp", "label": "Auf den Wertebereich 0–100 begrenzt", "points": -10.0},
      {"step": "result", "label": "Ergebniswert", "points": 100.0}
    ],
    "min_score": 70.0,
    "classes": [{"class": "exact", "label": "exakt", "from": 97.0},
                {"class": "high", "label": "hoch", "from": 90.0},
                {"class": "medium", "label": "mittel", "from": 80.0}],
    "class": "exact", "class_label": "exakt", "consistent": true
  },
  "review": {"status": "open", "status_label": "offen", "sequence": 0,
             "decision": null, "second_review": null, "events": 0}
}
```

**Aufschlüsselung (`breakdown`).** Die Schritte werden aus Treffer und Profil
nachgerechnet und mit dem Wert der Bibliothek abgeglichen. Stimmen beide nicht
überein, ist `consistent: false`; die Oberfläche zeigt dann, dass die Erklärung
unvollständig ist, statt eine falsche anzuzeigen. PEP-Treffer (`token_f1`)
zeigen statt des Token-Set-Werts den Token-F1-Wert mit Anteil gemeinsamer
Namensbestandteile, Teilstring- und Länderbonus und die Kappung auf 1.

**Filter** (Query-Parameter, kommagetrennt, kombinierbar): `status`
(Prüfstatus), `list` (Listenkennung), `subject` (`s1` …), `confidence`
(`exact`, `high`, `medium`, `low`, `fuzzy`), `min_score` (Zahl). Filter
wirken nur auf `hits`; Zähler im Kopf und `hits_before_filter` bleiben
ungefiltert.

### `POST …/decision`

```json
{"outcome": "dismissed", "reason": "Geburtsjahr und Anschrift weichen ab.",
 "four_eyes": false, "expected_sequence": 0}
```

- `outcome`: `confirmed` (bestätigen – Identität belegt), `dismissed`
  (verwerfen – keine Identität), `deferred` (zurückstellen – Klärung offen).
- `reason`: Pflicht, nicht nur Leerraum, höchstens 4000 Zeichen.
- `four_eyes`: Zweitprüfung anfordern. Ist `outcome` in `four_eyes_outcomes`
  des Dienstes, gilt sie immer (`four_eyes_source: "policy"`).
- `expected_sequence`: optional, `review.sequence` des gelesenen Stands;
  weicht er ab, 409 `stale_state`.

Antwort: der Treffer mit neuem `review`.

### `POST …/second-review`

```json
{"approve": true, "reason": "Nachvollzogen.", "expected_sequence": 3}
```

Nur für Treffer im Status `pending_second_review` und nur durch eine andere
Person als die entscheidende (`actor.id` verschieden). Zustimmung setzt den
vorgeschlagenen Status, Ablehnung setzt den Treffer auf `open` zurück; die
Ablehnung bleibt im Protokoll und in `review.second_review` sichtbar, bis neu
entschieden wird.

### Zustände

```
open ──decision──▶ confirmed | dismissed          (abschließend)
open ──decision──▶ deferred ──decision──▶ …       (erneut entscheidbar)
open ──decision (Vier-Augen)──▶ pending_second_review
pending_second_review ──second-review approve──▶ vorgeschlagener Status
pending_second_review ──second-review reject───▶ open
```

### `GET /runs/{run_id}/log`

Unveränderliches Protokoll (`events[]`): `sequence`, `type`
(`run_created`, `decision_recorded`, `second_review_recorded`), `type_label`,
`at` (UTC), `actor`, `hit_id`, `hit` (`subject_name`, `entry_name`,
`list_name`), `data` (Entscheidung, Begründung, Vier-Augen-Angaben),
`outcome_label`. Der Prüfstatus wird ausschließlich aus diesem Protokoll
abgeleitet.

## Fehler

```json
{"error": {"code": "same_person", "message": "Die Zweitprüfung muss eine andere Person vornehmen …", "details": {}}}
```

| Status | Code | Anlass |
|---|---|---|
| 400 | `invalid_json` | Anfragetext ist kein JSON |
| 401 | `unauthenticated` | Resolver liefert keine Person |
| 404 | `not_found` | Prüflauf oder Treffer unbekannt |
| 409 | `already_decided` | Treffer bereits bestätigt oder verworfen |
| 409 | `second_review_pending` | Entscheidung wartet auf Zweitprüfung |
| 409 | `no_pending_decision` | Zweitprüfung ohne wartende Entscheidung |
| 409 | `same_person` | Zweitprüfung durch die entscheidende Person |
| 409 | `stale_state` | `expected_sequence` veraltet |
| 409 | `concurrent_update` | Speicher meldet gleichzeitige Änderung |
| 413 | `too_large` | Anfrage über 256 KiB |
| 415 | `unsupported_media_type` | kein `application/json` |
| 422 | `invalid_request` | Vertrag verletzt (Profil, Liste, Mindestwert, Pflichtbegründung …) |

## Speicher-Protocol

```python
class ReviewStore(Protocol):
    def add_run(self, run: StoredRun, first_event: ReviewEvent) -> None: ...
    def get_run(self, run_id: str) -> StoredRun | None: ...
    def list_runs(self) -> Sequence[StoredRun]: ...
    def events(self, run_id: str) -> Sequence[ReviewEvent]: ...
    def append(self, event: ReviewEvent, *, expected_sequence: int) -> None: ...
```

`append` schreibt nur, wenn die letzte Sequenz des Laufs `expected_sequence`
ist, sonst `SequenceConflict` (→ 409 `concurrent_update`). In einer Datenbank
genügt dafür ein eindeutiger Schlüssel `(run_id, sequence)`. Ein Prüflauf
wird nie geändert, Ereignisse werden nie gelöscht oder überschrieben.
