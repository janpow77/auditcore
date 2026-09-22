# Bestandsverhalten und Vertrag des gemeinsamen Harvest-Kerns

Grundlage: tatsächlich ausgeführte Bestandsbasen (`tools/capture_legacy_harvest.py`,
Fixture `tests/fixtures/legacy_harvest_observed.json`), jeweils gegen GitHub-HEAD
und Git-Blobs geprüft, Netz nur über `httpx.MockTransport`, keine Anwendungsdatenbank:

| Quelle | Commit | Ausgeführt |
|---|---|---|
| `janpow77/auditdatabase` | `bba911e918e102426d4ca2f88fd377fe8ca585e4` | `harvester/base.py` (Hash, Datum, Förderperiode, Fonds, Relevanz, Normalisierung), `DIPHarvester.harvest` in vier Szenarien |
| `janpow77/audit_designer` | `030a71e083ef0feddc14545b095a4945bc0bbd7a` | `vp_ai/harvester/base.py` inkl. `_fetch_page_content`; Scheduler-Zeitgrenzen gelesen (DB-/Redis-gebunden) |
| `janpow77/regulierung` | `a5d48ea4b90a410210ec25e707781ef9e21ad743` | `BaseConnector.run` und `DestatisGenesisConnector` in sechs Szenarien |

Gleiche Namen (`HarvestResult`, `BaseHarvester`) bedeuten nachweislich **nicht**
gleiche Semantik: auditdatabase/Designer kennen `success: bool`, regulierung
`erfolg | teilweise | fehler`; nur regulierung schreibt ein Laufprotokoll.

| ID | Beobachtung im Bestand | Vertrag des Kerns |
|---|---|---|
| HC-01 | DIP mit HTTP 429 auf allen Abfragen: `success=True`, 0 Dokumente. | `RateLimitError` mit `retry_after`, begrenzte Wiederholung; danach `failed`/`rate_limited`. |
| HC-02 | DIP mit HTTP 500 und Timeout bei einzelnen Schlagworten: `success=True`, kein Fehlertext. | Fehler je Seite strukturiert; bereits bestätigte Seiten bleiben, Lauf `partial`. |
| HC-03 | Keine Pagination: je Schlagwort nur die erste Seite, danach hartes Abschneiden auf `limit`. | Seitenfolge mit Cursor, `LimitReached` als sichtbarer Teilabbruch. |
| HC-04 | Timeouts 30 s je Anfrage, Designer-Scheduler 600/1800 s je Quelle; keine Wiederholung (regulierung-Docstring nennt Retry, Code nicht). | Timeout je Anfrage, Laufdauergrenze, `RetryPolicy` mit Backoff und `Retry-After`-Obergrenze. |
| HC-05 | Designer `_fetch_page_content`: 404, Timeout und PDF ergeben gleichermaßen `""`. | Transport-/Statusfehler sind Fehler, kein leerer Inhalt. |
| HC-06 | regulierung unterscheidet `teilweise`; fehlende Zugangsdaten schreiben kein Laufprotokoll. | `partial` und `auth_error` als eigene Zustände; Protokollierung bleibt Consumeraufgabe. |
| HC-07 | `_parse_date` liefert in auditdatabase und Designer für jedes Format `None` (Slicing-Fehler). | Datumsparsing gehört in den Quellenadapter und wird dort mit Fixtures belegt. |
| HC-08 | `content_hash` = SHA-256 über `content or abstract or title`; leerer Inhalt → Titel-Hash. | `content_hash` über normalisierte Nutzdaten und Löschkennzeichen (kanonisches JSON). |
| HC-09 | Checkpoints: Designer `last_harvest_at`/`supports_incremental`, sonst keine; Status wird vor Speicherung geschrieben. | Checkpoint erst nach Bestätigung der Senke, Compare-and-Set, Profilversion gebunden. |
| HC-10 | Dubletten: DIP entfernt gleiche IDs innerhalb eines Laufs; Staging im Designer zählt Duplikate. | Dubletten im Lauf und an der Senke getrennt gezählt; Senke idempotent. |

Löschungen/Snapshots: Kein Bestand entfernt Datensätze aus einem Harvestlauf
heraus. Der Kern bleibt dabei: er löscht nie und meldet nur
`snapshot_complete`, damit ein Consumer seine eigene Regel ausschließlich nach
einem vollständigen Lauf von Anfang an anwendet.

## Offene Entscheidungen

- **HUMAN_DECISION_REQUIRED:** Ob Quellen mit harter Ergebnisbegrenzung (DIP-
  Schlagwortsuche) künftig vollständig paginiert werden sollen, ist eine
  fachliche Frage des jeweiligen Quellenprofils (Umfang, Abrufkosten).
- Der Kern ist synchron. Asynchrone Consumer rufen ihn über einen Thread
  (`asyncio.to_thread`) auf; ein asynchroner Engine ist nicht Teil von Vertrag 1.
