# auditcore_llm_client 0.1.0 – Paketbericht

Ziel: Gruppe 2 der App-Helfer-Inventur („AI-Router-Client“, ~3.100 fast gleiche
Zeilen in audit_designer, flowinvoice, audit-portal; schlanke Variante in
cockpit) als eine Bibliothek. Grundsatz: **FlowAgent ist der einzige GPU-Weg** –
nur ai-router-/Flow-Agent-Routen, keine direkten Ollama-/vLLM-/GPU-Aufrufe.

## Nachweise

| Prüfung | Ergebnis |
|---|---|
| Paket-Tests (`pytest tests`) | 190 passed (davon 120 Paritätsfälle: 60 Altfälle × sync/async) |
| `ruff check .`, `mypy --strict src`, `bandit -ll -r src` | PASS |
| Code-Qualitätsgate (`--package auditcore_llm_client`) | alle Metriken 0, Baseline-Eintrag 0 |
| pip (`verify_domain_packages.py`) | PASS: Hash-gebundene Installation, isolierte Herkunft, Smoke, selektive Installation ohne Extra, Entfernen |
| APT (`--apt`) | 22/22 PASS; Wheel-SHA256 `e6b7f7458b1ba0b036e79807eabe21de8ee06a24197ea00999b294830f624b70`; `Depends: python3 (>= 3.11)`, `Suggests: python3-httpx (>= 0.23)` |
| `tests/test_release_preparation.py` (neuer `EXPECTED_SOURCES`-Eintrag) | 35 passed |
| Plattform-Tests, Root-`ruff check .` | 343 passed, PASS |

Herkunft (`provenance.json`, Blob-SHAs je Datei): audit_designer `ccd6524`,
flowinvoice `fb2d185`, audit-portal `d8eefa4`, cockpit `df203d4`,
ai-router `426cd78` (Routen/Auth gelesen), flow-agent `149e14b`
(App-Routen, `AiGenerateRequest`, `X-Flow-Sensitivity` gelesen). Lizenz MIT
(USER_AUTHORIZED_MIT vom 22.09.2026, nur für die Bibliothek).

## Charakterisierung

`tools/capture_legacy_clients.py` lädt die vier Altclients aus den gebundenen
Commits (`git show`), ersetzt nur die App-Settings durch Stubs und lässt sie
gegen `httpx.MockTransport` laufen. 60 Fälle in 5 Gruppen (audit_designer 19,
flowinvoice ai-router 15, flowinvoice Flow-Agent 11, audit-portal 4, cockpit 11)
mit Anfrage (Methode, URL, Header, Body/Multipart), Ergebnis oder Fehler,
Health-Eintrag, Metering-Aufrufen und der Frage, ob der Schlüssel in Fehler,
Rückgabe, Health oder Log auftaucht. Die Bibliothek erzeugt in allen 60 Fällen
dieselben Anfragen und dieselben Ergebnisse; Abweichungen B1–B12 in
`packages/auditcore_llm_client/docs/behavior-changes.md`.

## Profile je App

| Profil | Unterschiede (als Konfiguration) |
|---|---|
| `AUDIT_DESIGNER` | `/api/chat` mit festen Ollama-Optionen, `think=false`, `keep_alive`, Standard 0,2/4000, 404-Rückfall auf OpenAI-Routen (Chat, Rerank `documents`→`passages`, Embed), `<think>` entfernen, `/health` mit Auth-Headern |
| `FLOWINVOICE` | `/api/generate`, OpenAI-Rerank/Embed mit Modell, `/health` ohne Header; mit `FLOW_AGENT_URL`: App-Routen, Bearer, Qualitätsstufe statt Modell, OCR im vision-service-Dialekt, `/ready?capability` |
| `AUDIT_PORTAL` | wie flowinvoice (Altstand ohne Flow-Agent), App-ID `audit-portal`, Metering über `usage_hook` |
| `COCKPIT` | `AI_ROUTER_*`, Modellliste mit Cache (60/5/300 s), NDJSON-Streaming |
| `GENERIC` | neutrale Voreinstellung für neue Consumer |

## Befunde (Sicherheit)

Beobachtet mit einem neutralen Testschlüssel, den keine der Alt-Schwärzungsregeln
erkennt (Fälle in `tests/fixtures/legacy_clients_observed.json`):

- **S1 audit_designer** – `AiRouterError` übernimmt Antwortkörper (200 Zeichen)
  und httpx-Exception-Text ungefiltert. Ein Schlüssel im Antworttext landet in
  der Exception **und im `RouterHealth`-Eintrag, der über `/api/health` ans
  Frontend geht** (`ad-generate-key-echo`); `safe_call_*` gibt ihn zurück
  (`ad-safe-llm-key-echo`); Zugangsdaten aus der URL stehen in der Exception
  (`ad-generate-unreachable`). Außerdem sendet `health()` den `X-Api-Key` an den
  öffentlichen `/health`.
- **S2 flowinvoice** – `safe_call_*` geben `str(exc)` ungeschwärzt zurück **und
  loggen ihn** (`logger.warning(... %s, exc)`), der Health-Eintrag enthält den
  Schlüssel ebenfalls (`fi-safe-llm-key-echo`); Transportfehler tragen den
  httpx-Text inkl. URL-Zugangsdaten (`fi-embed-unreachable`). Die
  `_redact_error_message`-Muster greifen nur beim Health-Speicher und erkennen
  den konfigurierten Schlüssel nicht. `app/llm/ollama.py` reicht
  `f"Gateway nicht erreichbar: {exc}"` in `LLMResponse.error` weiter und loggt
  per `logger.exception(f"... {e}")` (Code-Lektüre, nicht ausgeführt).
- **S3 audit-portal** – Fork des flowinvoice-Standes, gleiche Muster wie S2
  (Code identisch, Diff geprüft).
- **S4 cockpit** – `chat_stream` gibt bis zu 300 Zeichen Antwortkörper bzw. den
  httpx-Text als `{"error": …}` an den Browser weiter; Schlüssel/URL-Zugangsdaten
  werden sichtbar (`ck-stream-http-500`, `ck-stream-unreachable`). Standard-URL
  ist eine fest eingetragene Tailscale-IP.
- **S5 flowinvoice** – `OllamaProvider` fällt bei Gateway-Fehlern auf einen
  direkten Ollama (`OLLAMA_FALLBACK_HOST`, Redis `ollama:mode=fallback`) zurück –
  Verstoß gegen „FlowAgent ist der einzige GPU-Weg“.
- **S6 audit-portal** – fällt der Setting-Wert weg, meldet sich der Client als
  `flowinvoice` (Quote/Metering vermischt).

In der Bibliothek behoben: Schwärzung aller Meldungen/Logs/Health-Einträge
inkl. des konfigurierten Schlüssels im Klartext, keine verketteten
Transport-Exceptions, keine Standard-URL/-Schlüssel, Port 11434 abgelehnt,
Flow-Agent fail-closed ohne Schlüssel (Tests `test_errors_and_logs_never_contain_the_key`,
`test_traceback_of_client_error_contains_no_secret`, Parität prüft je Fall
„Schlüssel nicht in Fehler/Health“).

## Offen

- Consumer-Migration (audit_designer, flowinvoice, audit-portal, cockpit) nicht
  Teil dieses Auftrags (App-Repos nur gelesen): Requirements um
  `auditcore_llm_client[http]` ergänzen, `ai_router_client.py` durch Adapter auf
  `LlmClient`/`AsyncLlmClient` mit dem jeweiligen Profil ersetzen, S5 entfernen.
- Kein Release erzeugt.
