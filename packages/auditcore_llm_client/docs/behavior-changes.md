# Bewusste Abweichungen vom Verhalten der Altclients

Grundlage: 60 ausgeführte Fälle der vier Altclients
(`tests/fixtures/legacy_clients_observed.json`, erzeugt mit
`tools/capture_legacy_clients.py`). `tests/test_legacy_parity.py` spielt jeden
Fall mit dem synchronen und dem asynchronen Client der Bibliothek nach. Anfragen
(Methode, URL, Header, Body) sind in allen 60 Fällen identisch; Ergebnisse und
Statuscodes ebenfalls, soweit unten nicht anders vermerkt.

| Nr. | Altverhalten | Bibliothek | Grund |
|---|---|---|---|
| B1 | Fehlermeldungen enthalten Antwortkörper (bis 200 Zeichen) und den Text der httpx-Exception ungefiltert; nur der Health-Speicher (alle) und die Safe-Wrapper von audit_designer schwärzen nach Mustern. | Jede Meldung (Exception, Log, Health, Safe-Wrapper) läuft durch `redact`: konfigurierter Schlüssel im Klartext, URLs, DSNs, Bearer, `X-Api-Key`, `sk-`/`gh*_`-Token, `api_key=`/`token=`-Parameter. Transportfehler nennen nur den Exception-Typ. | Token-Lecks (siehe Bericht, Befund S1–S4). Gilt ab jetzt für alle Apps; Vorlage war flowinvoice `_redact_error_message`. |
| B2 | `raise AiRouterError(...) from exc` – der Traceback enthält die httpx-Exception mit URL. | `raise … from None`; der Typ der Ursache steht in `cause_type`. | Tracebacks landen in Logs (`logger.exception`). |
| B3 | Standard-URLs im Code (`http://llm-router:7842`, cockpit zusätzlich `http://ai-router:7842` und eine feste Tailscale-Adresse). | Keine Standard-URL; fehlt die URL, gibt es `ConfigurationError`. Nur eine URL je Client, keine Adressraterei. | Öffentliches MIT-Paket darf keine internen Adressen tragen; explizite Konfiguration. |
| B4 | Flow-Agent-Modus ohne Schlüssel sendet ohne `Authorization` und läuft in 401. | `ConfigurationError` beim Erzeugen der Konfiguration (fail-closed vor dem ersten Request). | Früher, eindeutiger Fehler; kein unauthentisierter Request. |
| B5 | flowinvoice-Provider fällt bei Gateway-Fehlern auf einen lokalen Ollama (`OLLAMA_FALLBACK_HOST`) zurück. | Kein Fallback; URLs mit Port 11434 werden abgelehnt. | „FlowAgent ist der einzige GPU-Weg.“ |
| B6 | flowinvoice/audit-portal zählen Router-Fehler nur in den `safe_*`-Wrappern; audit_designer in jeder Funktion. | Wird dem Client eine `RouterHealth` übergeben, zählt er jeden Erfolg und Fehler zentral (sync und async gleich). | Einheitlicher Health-Status. Ohne übergebene `RouterHealth` wird nichts gezählt. |
| B7 | cockpit `chat_stream` liefert HTTP- und Transportfehler als Ereignis `{"error": …}`. | `stream_chat` wirft `RouterHttpError`/`RouterUnavailableError`; Fehlerzeilen *im* Stream bleiben Ereignisse (`StreamEventKind.ERROR`). | Einheitliche Fehlerverträge; ein Adapter in cockpit kann das Altformat mit `safe_call`/`to_dict` nachbilden. |
| B8 | audit_designer `health()` verliert den HTTP-Status (`status_code=None`). | Statuscode bleibt erhalten. | Strukturierte Fehler. |
| B9 | Rerank: Score-Liste falscher Länge wird still durch Nullen ersetzt (nur Log). | Weiterhin Nullen, aber `RerankResult.degraded=True`. | Fehlende Angaben sollen erkennbar sein. |
| B10 | Nicht-numerische Scores/Vektoren führen zu `TypeError`/`ValueError` außerhalb des Fehlervertrags; `content: null` wird bei flowinvoice zu `"None"`. | `InvalidResponseError`; `null` wird zu `""`. | Strukturierte Fehler. |
| B11 | Leere Eingabe bei `call_embed`/`call_rerank`: flowinvoice liefert `model=""`, audit_designer den Standardmodellnamen. | Immer der wirksame Modellname. | Vereinheitlicht, ohne Request. |
| B12 | Keine Wiederholungen, kein Circuit-Breaker im Client (flowinvoice: Breaker nur im Ollama-Provider, 3 Fehler/180 s). | `RetryPolicy` (Standard: 1 Versuch = Altverhalten) und `BreakerPolicy` (Standard 3/180 s) als Opt-in. | Funktionen aus dem Auftrag, ohne das Standardverhalten zu ändern. |

Nicht übernommen: `Redis ollama:mode=fallback` (flowinvoice), statische
Modellliste `get_available_models` (flowinvoice), Adressraterei (cockpit).
