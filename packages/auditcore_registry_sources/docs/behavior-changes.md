# Legacyverhalten und bewusst korrigiertes Verhalten

Quellen (Blob-geprüft gegen GitHub am 23.09.2026, tatsächlich ausgeführt mit
`tools/capture_legacy.py`, **456 Fälle**, rapidfuzz 3.10.1, Python 3.12.3):
audit_designer `1254591` (74), flowworkshop `3d1cb40` (55), audit-portal
`ac1ccc7` (38), flowsearch `10cb2a3` (173), flowinvoice `fb2d185` (103, davon
die beiden Originaltests `test_pep_checker.py`: PASS), osint `d361ddb` (7),
riskanalysis `b5c523b` (6, nur dokumentiert). Das Modul `legacy` gibt alle
Fälle exakt wieder (Ausnahmen: Zeitstempel `check_timestamp`/`request_date`
und von httpx formulierte Fehlertexte, die als Eingabe durchgereicht werden).
Die Namensnormalisierung stammt aus `auditcore_entity_matching` 0.2.0 (Profile
`audit_designer.sanctions`/`flowworkshop.sanctions` 2026.09.2, `flowinvoice.pep`,
`audit_portal.name[_folded]`).

## Bestätigte Befunde der Originale

| Quelle | Befund (beobachtet) |
|---|---|
| flowsearch `SanctionsAPIClient`/`PEPScreeningAPIClient` | Die OpenSanctions-API verlangt `Authorization: ApiKey …` (Doku, HTTP 401 ohne Schlüssel beobachtet). Der Sanktionsclient sendet keinen, der PEP-Client einen `Bearer`-Schlüssel. Beide lesen `result.entity`; die dokumentierte Antwort (yente 5.5.0) hat kein solches Feld — mit echter Antwort wird **nie** ein Treffer gefunden. Fehler werden als `found: False` zurückgegeben. |
| flowsearch `OpenRegisterAPIClient` | `https://offeneregister.de/api/v1/companies` antwortet HTTP 404; der Client liefert dann `found: False`. `HandelsregisterAPIClient` ist ein Platzhalter ohne Abruf. |
| flowsearch `UBOEngine` | `build_ownership_chain` endet bei einem Knoten, der auf sich selbst verweist, nicht (Speicherwachstum beobachtet, Lauf abgebrochen). |
| flowinvoice `SanctionsChecker.check_entity` | Scheitert bei **jedem** Cache-Fehlschlag mit `UnboundLocalError` (lokaler Import von `SanctionsResult` im Cache-Zweig). Der Dienst `search.sanctions.network` ist nicht mehr auflösbar. Die Listenangaben werden mit „heute, verifiziert“ erfunden. |
| flowinvoice `CompanyVerifier.validate_vat_id` | VIES antwortet mit `ns2:`-Präfixen (live bestätigt); gesucht wird `<valid>true</valid>` ohne Präfix → **jede** USt-IdNr. gilt als ungültig (`INVALID_VAT_ID`, kritisch). Ein SOAP-Fault mit HTTP 200 gilt ebenfalls als ungültig. |
| flowinvoice `search_offene_register` | SQL-Text wird aus dem Namen gebaut (Apostroph verdoppelt, Zeichen-Weißliste lehnt `/` und `'` ab); jeder Fehler inkl. HTTP 502 (live beobachtet) wird zu „nicht im Register“. |
| flowinvoice `_normalize_company_name` | Rechtsformen werden als Teilzeichenkette entfernt: `Hagen Metall AG → hen metall`. |
| flowinvoice `PEPChecker` | Ladefehler ergibt `is_clean=True`; `last_update` ist die Ladezeit, nicht der Listenstand; die Spalte `properties` gibt es in `targets.simple.csv` nicht, die Position bleibt immer leer. |
| audit-portal / flowinvoice XML-Parser | Beide identisch. Ein Geburtsjahr `1961` wird `1961-01-01`; nur die erste Anschrift/das erste Geburtsdatum wird gelesen, OFAC-Geburtsdaten und UN-`YEAR` gar nicht; Einträge ohne Namen verschwinden still; `xml.etree` ohne Schutz gegen Entity-Expansion. |
| flowworkshop `MultiSanctionsService` | Listen ohne Bestand werden still übersprungen; der CSV-Pfad indexiert auch Zeilen ohne Kennung/Namen. |
| audit_designer `registry.py` | Der Werkzeugeintrag nennt „phonetische Varianten“, der Dienst sagt „Ein phonetisches Verfahren ist nicht im Einsatz“. |
| riskanalysis `sanctions_screening.py` | Demo mit festen Einträgen, `SequenceMatcher`, Schwelle 82 und Klassen 99/90 — weitere Variante, nicht übernommen. |

## Korrigiertes Verhalten des Bibliotheksvertrags

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| REG-C01 | flowworkshop überspringt Listen ohne Bestand still. | Jede angefragte Liste hat einen `ListFinding`; ohne Bestand `searched=False` mit Hinweis; ohne Treffer bei fehlender Liste Status `INCOMPLETE`, ohne jede Liste `NOT_SEARCHED` (Designer-Verhalten). | Ein Nullbefund, der keiner ist, wirkt wie eine Unbedenklichkeit. |
| REG-C02 | Treffer, deren Wert erst durch Geburtsjahr-/Land-Malus unter den Mindestwert fällt, werden kommentarlos ausgegeben. | Weiter ausgegeben, aber `below_min_score` und Indikator `below_min_score_after_adjustment`; Rohwert und jede Anpassung mit Grund. | Nachvollziehbarkeit, keine stille Unterdrückung. |
| REG-C03 | Latin-1-Rückfall (Portal); leere Lieferung ergibt leeren Bestand (Designer/flowworkshop würden bei Lauf-ID alles austragen). | Nur UTF-8; fehlende Pflichtspalten, keine verwertbare Zeile → `FormatError`/`ParserError`. | Kein leerer Bestand aus einer defekten Lieferung. |
| REG-C04 | Datumsfelder werden zu `date`, Jahr → 1. Januar; nur erste Werte. | `xml_entries` behält die Schreibweise (`1961`), sammelt alle Geburtsdaten und Länder (`;`-getrennt), liest OFAC-`dateOfBirth` und UN-`YEAR`. `parse_xml_list(..., dates="legacy")` reproduziert das Original. | Keine erfundene Genauigkeit; Jahresabgleich braucht alle Daten. |
| REG-C05 | Einträge ohne Namen/Kennung verschwinden. | `RowIssue`; im Harvest-Lauf `RecordIssue`, Lauf `partial`. | Teilfehler sichtbar. |
| REG-C06 | `xml.etree.ElementTree.fromstring`. | `defusedxml` (Extra `xml`); Entity-Expansion wird abgelehnt. | Externe Großdokumente. |
| REG-C07 | VIES-Gültigkeit per Textsuche ohne Präfix. | XML-Auswertung unabhängig vom Präfix (`VALID`/`INVALID`). | Live bestätigtes Antwortformat. |
| REG-C08 | SOAP-Fault (HTTP 200) = ungültig; Zeitüberschreitung = `SERVICE_UNAVAILABLE`. | Fault, Serverfehler, Transportfehler → `UNAVAILABLE`, nie `INVALID`. | Nichtverfügbarkeit ist keine negative Auskunft. |
| REG-C09 | SQL-Text aus dem Firmennamen; Fehler → „nicht im Register“. | Datasette-Parameter (`:pattern`, `:limit`), kein SQL-Text aus Eingaben; `UNAVAILABLE` getrennt von `NOT_FOUND`, Prüfung als unvollständig markiert. | Sicherheit; kein Scheinbefund. |
| REG-C10 | Rechtsformen als Teilzeichenkette entfernt. | Als ganze Wortfolgen (gleiche Liste). | `Hagen` bleibt `hagen`. |
| REG-C11 | Nicht offengelegter Name (`---`) würde verglichen. | Kein Namensabgleich, Hinweis in `notes`. | Deutschland legt Namen in VIES nicht offen. |
| REG-C12 | Endlosschleife bei Selbstverweis. | `ownership_chain` stoppt und meldet `cycle`. | Terminierung. |
| REG-C13 | PEP-Ladefehler = „sauber“; Stand = Ladezeit. | Kein Bestand → `NOT_SEARCHED`; Stand wird vom Aufrufer übergeben (`as_of`). | Kein Scheinbefund, kein erfundener Stand. |
| REG-C14 | `check_entity` (sanctions.network) nicht lauffähig, erfundene Listenstände. | Nicht übernommen; Profil `flowinvoice.sanctions_network` nur `LEGACY_ONLY`. Listenstand kommt immer aus der Lieferung (`Last-Modified`, `as_of`). | Dienst tot, Aktualität nie erfinden. |
| REG-C15 | API ohne/mit falschem Schlüssel, `result.entity`, Fehler = kein Treffer. | `MatchClient`: Schlüssel aus dem Credential-Provider (`ApiKey`), dokumentierte Antwortform, `AuthError`/`RateLimitError`/`TransportError`/`ParserError` statt `found: False`; API-eigenes `match`-Urteil wird bei Abweichung ausgewiesen. | Fehler dürfen nicht wie Nullbefunde aussehen. |
| REG-C16 | Designer/flowworkshop kennzeichnen nach einem Lauf alle nicht berührten Einträge als ausgelistet (auch wenn Zeilen übersprungen wurden); flowinvoice löscht hart und fügt neu ein. | Adapter liefern einen Vollbestand; `snapshot_complete` nur ohne Zeilenprobleme, doppelte Kennungen oder abweichende Gesamtzahl. Auslisten bleibt Consumer-Entscheidung. | Kein Auslisten auf unvollständiger Lieferung. |
| REG-C17 | ZER-Gesamtzahl und „weniger als 53 Handwerkskammern“ nur als Konsolenausgabe. | Abweichung → Issue, Lauf `partial`. | Teilfehler sichtbar. |
| REG-C18 | flowworkshop nutzt gespeicherte Vergleichsformen, der Designer bildet sie neu. | Vergleichsform immer aus der Listenschreibweise mit dem benannten Profil. | Anfrage und Liste müssen dieselbe Regel nutzen. |

## Entscheidungen vom 23.09.2026 (DECIDED)

Nutzer, 23.09.2026: „alle empfehlungen, ... A2 abgedeckt durch nutzung, A3 sollte
jeder dann selber holen können“. Umgesetzt als **neue empfohlene Profile**
(Version 2026.09.2, `status: USER_DECIDED`, Abruf über `recommended_profile(zweck)`).
Die charakterisierten Quellprofile 2026.09.1 und alle Replays bleiben bitgenau;
ihre ursprünglichen Markierungen `HUMAN_DECISION_REQUIRED` dokumentieren den
Quellstand, der entschiedene Nachfolger ist jeweils benannt.

| ID | Entscheidung | Umsetzung |
|---|---|---|
| R1 | Designer-Screening-Profil und -Schwellen maßgeblich | `audit_designer.sanctions_screening` 2026.09.2 (`sanctions_screening`): Mindestwert 70, 50–100, mindestens 3 Zeichen; Normalisierung `audit_designer.sanctions` 2026.09.3. flowworkshop behält ein wählbares Profil. |
| R2 | Zerlegt geschriebene Umlaute überall per NFC | Designer bereits NFC; `flowworkshop.sanctions_screening` 2026.09.2 mit `flowworkshop.sanctions` 2026.09.3 (NFC); entity_matching-Profile mit `compose: "NFC"`. |
| R3 | flowinvoice-PEP an die mueller-Regel | `flowinvoice.pep_bulk` 2026.09.2 (`pep_bulk`) mit `flowinvoice.pep` 2026.09.2. |
| R4 | UBO nach GwG: 25 %, mittelbare Anteile eingerechnet | `flowsearch.ubo` 2026.09.2 (`ubo`): mehr als 25 % Kapital **oder** Stimmrechte, Anteile entlang der Kette multipliziert; Anteilseigner ohne Typ sind keine natürlichen Personen, sondern erscheinen in `unclassified_holders` zur Klärung. Grundlage § 3 Abs. 2 GwG. |
| R5 | KMU nach Anhang I AGVO | `flowsearch.kmu` 2026.09.2 (`sme`, Methode `agvo_annex_i`): Beschäftigte und Umsatz **oder** Bilanzsumme je Klasse (Kleinst 10/2 Mio./2 Mio., Klein 50/10/10, Mittel 250/50/43); verbundene Unternehmen voll, Partner anteilig; fehlende Werte → „Nicht bestimmbar“ mit Hinweis. Nicht ausgewertet (Hinweis im Ergebnis): Art. 3 Abs. 4 und Art. 4 Abs. 2 Anhang I. |
| R6 | PEP-Risikostufen wie bisher | `flowsearch.pep_risk` 2026.09.2 (`pep_risk`), Werte unverändert. |
| R7 | Gewichte der Firmenprüfung wie bisher | `flowinvoice.company_verification` 2026.09.2 (`company_verification`), Werte unverändert. |
| R8 | Kein Auslisten bei fehlerhaften Zeilen | Vertrag der Adapter (REG-C16): Zeilenprobleme → Lauf `partial`, `snapshot_complete` falsch; Consumer listen dann nicht aus. |
| R9 | Designer-Werkzeugeintrag („phonetische Varianten“) korrigieren | Consumer-Migration nach v0.3.0, siehe `consumer-migration.md`. |
| R10 | Korrigierte Verträge einsetzen, inkl. VIES in flowinvoice | Consumer-Migration nach v0.3.0, siehe `consumer-migration.md`. |
| A2 | OpenSanctions-Datennutzung „abgedeckt durch Nutzung“ | Im Quellenkatalog dokumentiert; Lizenz CC BY-NC 4.0 bleibt genannt, Verantwortung beim Betreiber. |
| A3 | API-Schlüssel holt sich jeder Betreiber selbst | `MatchClient(api_key=…)` oder `credentials_from_environment(os.environ)` (`OPENSANCTIONS_API_KEY`); ohne Schlüssel `status == "NOT_CONFIGURED"` und `AuthError` mit Bezugsquelle https://www.opensanctions.org/api/. |

Offen bleibt nur, was die Consumer bei ihrer Umstellung selbst ausführen (R9, R10).
