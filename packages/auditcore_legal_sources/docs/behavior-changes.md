# Legacyverhalten und korrigierter Vertrag

Quellen: `janpow77/auditdatabase@bba911e918e102426d4ca2f88fd377fe8ca585e4`
(`backend/app/harvester/{base,dip,eurlex,rss}.py`) und
`janpow77/audit_designer@030a71e083ef0feddc14545b095a4945bc0bbd7a`
(`backend/app/modules/vp_ai/harvester/{_funding_period,base,bundestag_dip,eurlex}.py`).
Alle Beobachtungen stammen aus tatsächlich ausgeführtem Originalcode mit
synthetischen Antworten im dokumentierten Antwortformat und ersetztem
`httpx.AsyncClient`/SPARQL-Aufruf (`tools/capture_legacy_harvesters.py`,
176 Fälle; `tools/capture_legacy_feeds.py`, 12 Fälle mit echtem feedparser 6.0.11
und BeautifulSoup 4.12.3, `PYTHONHASHSEED=0`). Kein Netzabruf, keine Anwendungsdatenbank.

`auditcore_legal_sources.legacy` reproduziert beide Varianten exakt (176 Replay-
Tests). Die übrigen Module bilden den korrigierten Vertrag.

| ID | Beobachtung im Original | Korrigierter Vertrag |
|---|---|---|
| LS-C01 | `_parse_date` schneidet den Text vor `strptime` zu kurz ab (`len(fmt.replace('%',''))`); **jede** Zeichenkette ergibt `None`, in beiden Anwendungen. Alle EUR-Lex-Publikationsdaten sind leer. | ISO-Datum/-Zeitpunkt, `YYYY-MM`, `TT.MM.JJJJ`, `JJJJ` mit Genauigkeit; ungültige Werte bleiben `None`, der Rohwert bleibt erhalten. |
| LS-C02 | DIP-API-Schlüssel fest im Code und als Query-Parameter `apikey` (landet in URLs/Logs); Kommentar „gültig bis Mai 2026“. | Kein Schlüssel im Paket; Header `Authorization: ApiKey …` aus dem Credential-Provider; Zeilenumbrüche abgewiesen; fehlend → NOT_CONFIGURED. |
| LS-C03 | Leere/defekte DIP-Einträge werden zu Dokumenten mit ID `dip_` und Titel „Ohne Titel“. | `ParseError` je Eintrag mit Fundort; kein leerer Erfolg. |
| LS-C04 | DIP-Dokumente tragen `id` und `published_date`; der Aufnahmedienst liest `external_id` und `publication_date` und speichert beide nicht. | Einheitliches `LegalDocument` mit `external_id`, geparstem Datum, Identität und Contenthash. Consumer-Befund, dort zu beheben. |
| LS-C05 | Schlägt eine DIP-Suche fehl (HTTP 5xx, Transportfehler, ungültiges JSON), wird nur gedruckt; alle 27 fehlgeschlagen → `success=True`, 0 Dokumente. Ebenso werden fehlgeschlagene SPARQL-Abfragen übersprungen. | Seiten- und Abfragefehler werden als `ParseError`/Transportfehler zurückgegeben; Ablauf, Wiederholung und Teilfehlerstatus übernimmt `auditcore_harvest`. |
| LS-C06 | `get_vorgang` und `test_connection` greifen auf ein nicht vorhandenes `self.headers` zu (AttributeError; `test_connection` meldet deshalb immer `False`). | Nicht übernommen; Verbindungsprüfung über einen begrenzten Seitenabruf des Adapters. |
| LS-C07 | Keine Pagination (DIP-Cursor ungenutzt, SPARQL nur `LIMIT`). | DIP-Cursor und `f.aktualisiert.start` für inkrementelle Abrufe; Ende, wenn der Cursor gleich bleibt. |
| LS-C08 | SPARQL-Strukturfehler ergeben stillschweigend leere Listen. | Strikte Prüfung des W3C-JSON-Ergebnisformats. |
| LS-C09 | Aktualisierungsabfrage per f-String aus einem `datetime`. | Nur `date`-Objekte, feste Profilvorlage mit genau einem Platzhalter. |
| LS-C10 | RSS-Identitäten ohne Link aus `str(hash(title))`, bei ECA `hash(href)`: je Prozess verschieden (Seed 0 gegen 1 nachgewiesen). Sonst nur letztes Pfadsegment des Links (kollisionsanfällig). | SHA-256 aus Eintrags-`id` bzw. vollständigem Link; ohne beides `ParseError`. |
| LS-C11 | RSS-Zeitpunkt aus `published_parsed` als UTC ohne Zonenangabe; Atom-`updated` wird nie gesetzt; nicht auswertbare Datumstexte werden leer. | Datum aus UTC-Tupel mit `+00:00`, sonst RFC 822/ISO-Text; Rohwert bleibt erhalten. |
| LS-C12 | `_working_feeds` ist ein klassenweit geteiltes Dict: nach einem BaFin-Lauf ruft CURIA nur den BaFin-Feed ab und liefert BaFin-Meldungen als CURIA-Dokumente. | Reine Funktionen ohne gemeinsamen Zustand; Feedauswahl je Quelle aus dem Profil. |
| LS-C13 | ECA liefert bei nicht lesbarer Seite drei feste Platzhalter-„Berichte“ als erfolgreiche Dokumente. | Kein Ersatzinhalt; leere Linkliste bzw. Fehler. Platzhalter nur im `legacy`-Adapter. |
| LS-C14 | Jede BaFin-/CURIA-/ECA-Meldung erhält pauschal `fund=EFRE`, `funding_period=2021-2027`. | Keine erfundene Klassifikation. |
| LS-C15 | CURIA: nur `C-`-Aktenzeichen; Typ „Urteil“ nie erreicht (Feedname `urteile` existiert nicht); ohne relevanten Treffer werden die 20 neuesten allgemeinen Einträge übernommen. | `C-`/`T-`-Aktenzeichen, Typ je Feed aus dem Profil (REVIEW_REQUIRED: Bezeichnung), expliziter Relevanzfilter ohne Rückfall. |

Unverändert: Suchbegriffe, SPARQL-Abfragen, Kerndokumente, CELEX-Typregel,
Fondsregel, Contenthash-Definition, Dublettenregel „erstes Vorkommen gewinnt“,
Kerndokumente vor Abfrageergebnissen, DIP-PDF-Adresskonstruktion.

## Getrennte Varianten (keine Harmonisierung)

- Förderperiode: auditdatabase kennt nur 2021-2027/2014-2020 über wenige
  Merkmale; der Designer zusätzlich 1994–2013, weitere VO-Nummern und das
  Publikationsjahr. Beide Regeln sind benannt (`auditdatabase`, `designer`).
- DIP: auditdatabase sucht per `f.titel` mit 27 Begriffen und klassifiziert
  jede Drucksache heuristisch (Standard „EFRE“); der Designer nutzt 10 andere
  Begriffe, `Authorization`-Header, Vorgänge und keine Klassifikation.
- EUR-Lex: der Designer fragt ECA-Sonderberichte/Jahresberichte statt
  Durchführungs-VO/Leitlinien ab und hat andere Kerndokumenttitel.

## Offene Entscheidungen

1. **HUMAN_DECISION_REQUIRED:** Die DIP-Standardklassifikation („EFRE“ für jede
   Drucksache ohne ESF/Interreg im Titel) ist eine Heuristik der Quelle. Sie ist
   als `heuristic: true` gekennzeichnet; ob sie fachlich weiter gelten soll,
   entscheidet die Fachseite.
2. **REVIEW_REQUIRED:** Parameter `num` wird wie im Original gesendet; seine
   Wirkung auf die DIP-Seitengröße ist nicht per Live-Abruf bestätigt.
3. Datenrechte der abgerufenen Inhalte (DIP-Nutzungsbedingungen, EUR-Lex
   Wiederverwendung nach Beschluss 2011/833/EU) sind je Consumer zu beachten;
   das Paket enthält nur synthetische Fixtures.
