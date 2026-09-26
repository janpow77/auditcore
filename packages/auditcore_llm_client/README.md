# auditcore_llm_client

## Zweck

Client für den ai-router und das Flow-Agent-Inferenz-Gateway: Chat, Streaming, Embeddings, Rerank, OCR und Health, mit Schwärzung, Wiederholungen und Circuit-Breaker.

Er ersetzt die fast gleichen AI-Router-Clients in audit_designer, flowinvoice
und audit-portal (zusammen rund 3.100 Zeilen) und den schlanken Client in
cockpit. Grundsatz: **FlowAgent ist der einzige GPU-Weg.** Die Bibliothek
spricht nur mit einer konfigurierten Gateway-URL (Flow-Agent oder ai-router);
direkte Aufrufe an Ollama, vLLM oder GPU-Hosts gibt es nicht, URLs mit dem
Ollama-Port 11434 werden abgelehnt, einen lokalen Fallback gibt es nicht.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_llm_client[http]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.1 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-llm-client/`):

```text
auditcore_llm_client @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_llm_client-0.1.1-py3-none-any.whl#sha256=2de349bda575a23398f6273f748769676fb9e58114911b0da2a9c75edaeda552
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-llm-client
```

Extras: `[http]` – httpx ≥ 0.23 (Debian: `python3-httpx`) für `LlmClient` und
`AsyncLlmClient`; ohne Extra nur der Kern (Konfiguration, Requests, Parser,
Schwärzung, Health, Retry, Breaker). `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Der Kern läuft ohne httpx und ohne Netzwerk:

```python
from auditcore_llm_client import (
    FLOWINVOICE, ConfigurationError, Mode, config_from_env, redact, strip_think_tags,
    validate_base_url,
)

env = {
    "FLOW_AGENT_URL": "https://gateway.example.invalid",
    "FLOW_AGENT_APP_ID": "flowinvoice",
    "FLOW_AGENT_APP_KEY": "geheim-123",
}
config = config_from_env(FLOWINVOICE, env)   # gesetzte FLOW_AGENT_URL → Flow-Agent-Modus
assert config.mode is Mode.FLOW_AGENT
assert "geheim-123" not in repr(config)      # Schlüssel erscheint nie im repr

try:
    validate_base_url("http://gpu-host:11434")
except ConfigurationError as error:
    assert "Ollama" in str(error)            # direkter GPU-Weg wird abgelehnt

assert strip_think_tags("<think>abwägen</think>Beleg ist vollständig.") == "Beleg ist vollständig."
```

```pycon
>>> redact("Fehler bei https://gateway.example.invalid/api mit Bearer abc.def")
'Fehler bei <url> mit Bearer <token>'
```

Mit dem Extra `[http]` und einem erreichbaren Gateway (nicht im Test ausgeführt):

```python no-run
from auditcore_llm_client import FLOWINVOICE, LlmClient, RouterHealth, config_from_env

config = config_from_env(FLOWINVOICE)          # liest FLOW_AGENT_URL bzw. LLM_ROUTER_URL …
health = RouterHealth.shared()                 # optional: /api/health-Status der App
with LlmClient(config, health=health) as client:
    antwort = client.generate("Prüfe den Beleg.", system="Du bist Prüfer.")
    vektoren = client.embed(["Text 1", "Text 2"]).embeddings
```

Asynchron identisch mit `AsyncLlmClient` (`await client.generate(...)`,
`async for event in client.stream_chat(...)`). Für Tests wird der Transport
injiziert: `LlmClient(config, transport=httpx.MockTransport(handler))`.

## API-Überblick


| Methode | ai-router | Flow-Agent (`/api/v1/ai/apps/{app_id}…`) |
|---|---|---|
| `generate(prompt, system=…)` | `/api/chat` (audit_designer, 404 → `/v1/chat/completions`) bzw. `/api/generate` | `/generate` (Qualitätsstufe statt Modell) |
| `chat(messages)` | `/v1/chat/completions` | `/v1/chat/completions`, Modell `flow-agent-<quality>` oder `flow-agent-model:<id>` |
| `stream_chat(messages)` | `/api/chat` NDJSON | `/v1/chat/completions` SSE |
| `embed(texts)` | `/v1/embeddings` bzw. `/api/embed` (404 → `/v1/embeddings`) | `/v1/embeddings` (Gateway wählt Modell) |
| `rerank(query, documents)` | `/v1/rerank` bzw. `/api/reranker` (404 → `/v1/rerank`) | `/v1/rerank` |
| `ocr(content)` | `/api/ocr` (`file`/`model`/`language`) | `/v1/ocr` (vision-service-Dialekt `image`/`backend`/`lang`) |
| `health(capability=…)` | `GET /health` | `GET /ready?capability=…`, sonst `NotAssignedError` |
| `list_models()`, `model_snapshot()` | `GET /api/tags` (cockpit-Cache: 60 s, Fehler 5–60 s, veraltet ≤ 300 s) | nicht angeboten |

Ergebnisse: `LlmResult` (mit `telemetry`: `X-Flow-Agent-Request-Id/-Model/-Workers`,
`X-Llm-Spoke/-Failover`), `EmbedResult`, `RerankResult` (`degraded` bei falscher
Score-Anzahl), `OcrResult`, `ModelInfo`, `StreamEvent`.

Header wie in den Apps: ai-router `X-App-Id` und optional `X-Api-Key`; Flow-Agent
`Authorization: Bearer <App-Schlüssel>`; optional `X-Flow-Sensitivity`
(`ClientConfig.sensitivity`) und weitere, nicht authentisierende Header
(`extra_headers`).

#### Sensitivität (Flow-Agent)

`X-Flow-Sensitivity` (`public|internal|confidential|restricted`): wirksam ist das
Maximum aus App-Default und Header – der Header kann nur hochstufen. Ohne Header
gilt der App-Default (`internal`, bisheriges Verhalten). Das Gateway antwortet
bei ungültigem Wert mit HTTP 400 → `SensitivityRejectedError`; lässt die
wirksame Sensitivität kein verfügbares Modell zu (z. B. `restricted` ohne lokales
Modell), mit HTTP 403 → `EgressDeniedError` (Audit `ai.egress-denied`, kein
Upstream-Aufruf). Erkannt werden beide am Response-Header `X-Flow-Agent-Error`
(`invalid-sensitivity`, `egress-denied`), bei älteren Gateways am `detail`-Text.
Beide sind Richtlinienentscheidungen: **nicht** wiederholt,
nicht im Circuit-Breaker und nicht im Health-Zähler.

#### Denken/Reasoning

`generate`, `chat` und `stream_chat` nehmen `reasoning_effort`
(`none|low|medium|high`). OpenAI-Routen bekommen das Feld unverändert, Ollama-
Routen (`/api/chat`, `/api/generate`) `think` (`none` → `false`). Ohne Angabe
setzt der ai-router für Modelle mit Präfix `qwen3.5` selbst
`reasoning_effort=none` bzw. `think=false` (`LLM_NO_THINK_MODEL_PREFIXES`). Der
Flow-Agent-Vertrag `/generate` kennt das Feld nicht; dort sendet das Gateway
immer `think=false`.

### Fehler

Alle Fehler sind `LlmClientError` (Alias `AiRouterError`) mit `kind`,
`status_code`, `endpoint`, `retry_after`: `ConfigurationError`,
`RouterUnavailableError`, `RouterTimeoutError`, `RouterHttpError`,
`InvalidResponseError`, `CircuitOpenError`, `NotAssignedError`,
`UnsupportedOperationError`. `safe_call`/`async_safe_call` liefern
`(ergebnis, None)` oder `(None, geschwärzte Meldung)`.

**Schlüssel erscheinen nie** in Meldungen, Logs, Health-Einträgen oder `repr`:
der konfigurierte Schlüssel wird im Klartext ersetzt, dazu URLs, DSNs, Bearer-,
`X-Api-Key`-, `sk-`- und GitHub-Token. Transportfehler werden nicht verkettet
(`from None`), damit Tracebacks keine URL enthalten. Schlüssel kommen nur aus
Konfiguration oder Umgebung; es gibt keine Standardschlüssel und keine
Standard-URL.

**Bevorzugt als Secret-Referenz:** Schlüssel stehen in der Umgebung als
`secret://<anbieter>/<name>` und werden beim Start über die Flow-Agent-Control-
Plane (`POST /api/v1/secrets/use`, auditiert) aufgelöst:

```python
from flow_agent_client.secret_refs import SecretResolver   # nicht Teil dieser Bibliothek
config = config_from_env(FLOWINVOICE, secret_resolver=SecretResolver.from_env().resolve)
```

Ohne Resolver ist eine `secret://`-Referenz ein `ConfigurationError`; sie wird
nie als Schlüssel gesendet. Fehler des Resolvers werden ohne dessen Text gemeldet.

### Wiederholungen und Circuit-Breaker

Standard wie bisher: ein Versuch, kein Breaker. Opt-in:

```python
import dataclasses
from auditcore_llm_client import BreakerPolicy, RetryPolicy
config = dataclasses.replace(config, retry=RetryPolicy(max_attempts=3),
                             breaker=BreakerPolicy(failure_threshold=3, reset_timeout=180))
```

Wiederholt werden 429/502/503/504 und Verbindungsfehler (exponentiell 0,5 s …
8 s, `Retry-After` wird beachtet), Zeitüberschreitungen nur mit
`retry_timeout=True`. Der Breaker öffnet nach Ausfällen (Verbindung, Timeout,
5xx, 429) und lässt nach `reset_timeout` genau einen Probeaufruf durch.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_llm_client.__all__` (63):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `AUDIT_DESIGNER` | Konstante | – | `profiles` |
| `AUDIT_PORTAL` | Konstante | – | `profiles` |
| `COCKPIT` | Konstante | – | `profiles` |
| `FLOWINVOICE` | Konstante | – | `profiles` |
| `GENERIC` | Konstante | Neutral profile for new consumers: OpenAI-compatible routes, no fixed options. | `profiles` |
| `PROFILES` | Konstante | – | `profiles` |
| `AiRouterError` | Wert | Migration alias for the name used in audit_designer, flowinvoice and audit-portal. | `errors` |
| `async_safe_call` | Funktion | Async variant of :func:`safe_call`. | `health` |
| `AsyncLlmClient` | Klasse | ai-router/Flow-Agent client with async API. | `async_client` |
| `BreakerPolicy` | Datenklasse | Circuit breaker thresholds (legacy flowinvoice: 3 failures, 180 s). | `resilience` |
| `BreakerState` | Aufzählung | Circuit breaker state. | `resilience` |
| `CircuitBreaker` | Klasse | Closed → open after ``failure_threshold`` outages; one trial after ``reset_timeout``. | `resilience` |
| `CircuitOpenError` | Ausnahme | The circuit breaker is open; the call was not sent. | `errors` |
| `ClientConfig` | Datenklasse | Everything a client needs; build it directly or via ``config_from_env``. | `config` |
| `config_from_env` | Funktion | Read URL, app id, key, quality and model names for ``profile``. | `environment` |
| `ConfigurationError` | Ausnahme | Missing or unsafe configuration (no URL, missing key, direct GPU host). | `errors` |
| `EgressDeniedError` | Ausnahme | Flow-Agent HTTP 403: the effective sensitivity allows no available model. | `errors` |
| `EmbedResult` | Datenklasse | Answer of ``embed``; vectors follow the order of the input texts. | `results` |
| `EmbedRoute` | Aufzählung | Embedding route of the ai-router. | `profiles` |
| `EnvNames` | Datenklasse | Environment variable names read by ``config_from_env``. | `profiles` |
| `ErrorKind` | Aufzählung | Why a call failed. | `errors` |
| `GenerateRoute` | Aufzählung | How a single prompt (plus optional system prompt) is sent to the ai-router. | `profiles` |
| `get_profile` | Funktion | Look up a profile by name (``audit_designer``, ``flowinvoice``, …). | `profiles` |
| `HealthAuth` | Aufzählung | Headers of the ai-router ``GET /health`` call. | `profiles` |
| `InvalidResponseError` | Ausnahme | The response did not match the expected schema. | `errors` |
| `is_secret_reference` | Funktion | True for Flow-Agent secret references (``secret://<anbieter>/<name>``). | `environment` |
| `LlmClient` | Klasse | ai-router/Flow-Agent client with sync API. | `sync_client` |
| `LlmClientError` | Ausnahme | Base error of all client calls (legacy name: ``AiRouterError``). | `errors` |
| `LlmResult` | Datenklasse | Answer of ``generate``/``chat``. | `results` |
| `Mode` | Aufzählung | Which gateway dialect the client speaks. | `config` |
| `model_defaults_from_env` | Funktion | Model names from the profile's environment chain, else the profile defaults. | `environment` |
| `ModelCatalog` | Klasse | Cache logic only; the client supplies the fetch and the lock. | `catalog` |
| `ModelDefaults` | Datenklasse | Model names used when a call names none (ai-router mode only). | `profiles` |
| `ModelInfo` | Datenklasse | One entry of the ai-router model list (``/api/tags``). | `results` |
| `ModelSnapshot` | Datenklasse | Model list plus the state of the last fetch. | `catalog` |
| `NotAssignedError` | Ausnahme | Flow-Agent readiness: the capability is not assigned to a healthy worker. | `errors` |
| `OcrResult` | Datenklasse | Answer of ``ocr`` (mapped from the ai-router ``OcrResponse``). | `results` |
| `Profile` | Datenklasse | Dialect of one application. | `profiles` |
| `Quality` | Aufzählung | Flow-Agent quality selector; the gateway picks the model. | `config` |
| `redact` | Funktion | Return ``text`` without secrets, URLs, DSNs and tokens, truncated to ``max_len``. | `redaction` |
| `RerankResult` | Datenklasse | Answer of ``rerank``; ``scores`` follow the order of the input documents. | `results` |
| `RerankRoute` | Aufzählung | Reranker route of the ai-router. | `profiles` |
| `RerankScore` | Datenklasse | One scored document. | `results` |
| `resolve_secret` | Funktion | Plain value or resolved ``secret://`` reference; the value never enters messages. | `environment` |
| `ResponseTelemetry` | Datenklasse | Routing information the gateway returns in response headers. | `results` |
| `RetryPolicy` | Datenklasse | How often and how long to retry. ``max_attempts=1`` disables retries. | `resilience` |
| `RouterHealth` | Klasse | Last success, last error and consecutive failures of the gateway. | `health` |
| `RouterHttpError` | Ausnahme | The router answered with an HTTP error status. | `errors` |
| `RouterTimeoutError` | Ausnahme | The call exceeded its timeout. | `errors` |
| `RouterUnavailableError` | Ausnahme | Router/gateway not reachable (connection error). | `errors` |
| `safe_call` | Funktion | Run ``func``; return ``(result, None)`` or ``(None, redacted message)``. | `health` |
| `SecretRefResolver` | Typalias | Resolves a ``secret://`` reference to the plain value (injected, e.g. flow-agent client). | `environment` |
| `SecretValue` | Klasse | A credential that does not reveal itself in ``repr``/``str``. | `config` |
| `Sensitivity` | Aufzählung | Value of ``X-Flow-Sensitivity`` (Flow-Agent egress policy). | `config` |
| `SensitivityRejectedError` | Ausnahme | Flow-Agent HTTP 400: invalid ``X-Flow-Sensitivity`` value (policy, not an outage). | `errors` |
| `StreamEvent` | Datenklasse | One event of ``stream_chat``. | `results` |
| `StreamEventKind` | Aufzählung | Kind of a streamed chat event. | `results` |
| `strip_think_tags` | Funktion | Remove ``<think>…</think>`` reasoning blocks (Qwen3/DeepSeek). | `parsing` |
| `Timeouts` | Datenklasse | Per-operation timeouts in seconds (defaults of all legacy clients). | `config` |
| `UnsupportedOperationError` | Ausnahme | The operation is not offered in the configured mode. | `errors` |
| `unwrap_secret` | Funktion | Accept ``str``, pydantic ``SecretStr`` or ``None`` (legacy ``_unwrap_secret``). | `config` |
| `UsageRecord` | Datenklasse | Passed to ``ClientConfig.usage_hook`` after every LLM answer (audit-portal F3). | `results` |
| `validate_base_url` | Funktion | Normalise and check the gateway URL; raise :class:`ConfigurationError`. | `config` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_llm_client.async_client` | Asynchronous client (httpx ``AsyncClient``); transport injectable for tests. |
| `auditcore_llm_client.catalog` | Cached model list with explicit fetch state (cockpit ``model_snapshot``). |
| `auditcore_llm_client.config` | Client configuration: target, credentials, timeouts, resilience, profile. |
| `auditcore_llm_client.engine` | Transport-independent call bookkeeping shared by the sync and async clients. |
| `auditcore_llm_client.environment` | Build a :class:`ClientConfig` from environment variables of a profile. |
| `auditcore_llm_client.errors` | Structured errors. Every message is redacted; no exception carries a secret. |
| `auditcore_llm_client.health` | Router reachability tracking and graceful-degradation wrappers. |
| `auditcore_llm_client.jsontypes` | JSON value types and tolerant readers for router responses (stdlib only). |
| `auditcore_llm_client.operations` | Public operations as (request, parser) pairs – identical for sync and async. |
| `auditcore_llm_client.parsing` | Turn gateway responses into result objects (legacy field mapping). |
| `auditcore_llm_client.parsing_rerank` | Reranker answers: ``{"scores": [...]}`` (``/v1/rerank``) or ``{"results": [...]}``. |
| `auditcore_llm_client.profiles` | App profiles: the characterised differences of the legacy clients as data. |
| `auditcore_llm_client.received` | Transport-neutral view of a gateway response and the HTTP error mapping. |
| `auditcore_llm_client.redaction` | Remove secrets from any text that leaves the client (messages, logs, health). |
| `auditcore_llm_client.resilience` | Retries with exponential backoff and a thread-safe circuit breaker. |
| `auditcore_llm_client.results` | Result types of all operations (field names follow the legacy dataclasses). |
| `auditcore_llm_client.streaming` | Line decoders for streamed chat answers. |
| `auditcore_llm_client.sync_client` | Synchronous client (httpx ``Client``); transport injectable for tests. |
| `auditcore_llm_client.transport` | httpx binding: build requests, convert responses, map transport errors. |
| `auditcore_llm_client.wire` | Transport-neutral request description and header construction (stdlib only). |
| `auditcore_llm_client.wire_llm` | Request builders for text generation, chat and streaming. |
| `auditcore_llm_client.wire_services` | Request builders for embeddings, reranking, OCR, health and the model list. |
<!-- api-overview:end -->

## Profile und Konfiguration


| Profil | Umgebung | Unterschiede |
|---|---|---|
| `AUDIT_DESIGNER` | `LLM_ROUTER_URL/APP_ID/API_KEY`, Modell `VP_AI_EGPU_MODEL` → `OLLAMA_MODEL`, `VP_AI_LLM_KEEP_ALIVE` | `generate` über `/api/chat` mit festen Optionen (`num_ctx` 16384, `top_p` 0,8, `top_k` 20, `repeat_penalty` 1,05, `think=false`, `keep_alive`), Standard 0,2/4000 Tokens, `<think>` entfernen, Rerank/Embed mit 404-Rückfall, `/health` mit Auth-Headern |
| `FLOWINVOICE` | wie oben + `FLOW_AGENT_URL/APP_ID/APP_KEY/QUALITY`, `OLLAMA_DEFAULT_MODEL`, `EMBEDDING_MODEL`, `RERANKER_MODEL` | `/api/generate`, OpenAI-Rerank/Embed, `/health` ohne Header; gesetzte `FLOW_AGENT_URL` schaltet in den Flow-Agent-Modus |
| `AUDIT_PORTAL` | wie flowinvoice ohne Flow-Agent, App-ID `audit-portal` | Metering über `ClientConfig.usage_hook` (ersetzt `record_llm_usage`) |
| `COCKPIT` (**abgekündigt**) | `AI_ROUTER_URL/APP_ID/API_KEY` | Modellliste und NDJSON-Streaming; cockpit wird abgeschaltet (Funktionen in flow-agent #50), Profil bleibt nur für bestehende Tests |
| `GENERIC` | `AI_ROUTER_*`, `FLOW_AGENT_*` | neutrale Voreinstellung für neue Consumer |

`config_from_env(profile, environ=None, *, secret_resolver=None)` liest die
Umgebungsnamen des Profils; es gibt weder Standard-URL noch Standardschlüssel.
Zeitgrenzen stehen in `Timeouts`, Sensitivität in `ClientConfig.sensitivity`,
zusätzliche nicht authentisierende Header in `extra_headers`, Metering über
`usage_hook`.

## Herkunft und Charakterisierung

Neuimplementierung gegen charakterisierte Verträge: Verhalten der ausgeführten
ai-router-Clients von audit_designer, flowinvoice (ai-router- und
Flow-Agent-Modus), audit-portal und cockpit; Routen und Verträge aus ai-router
und flow-agent gelesen. Zeitgrenzen, Health-Schwellen, Routen-Rückfälle,
Feldabbildungen und Schwärzungsmuster wurden übernommen, der Code neu
geschrieben; Commits und Blob-SHAs stehen in `provenance.json`.
Charakterisierung: 60 ausgeführte Altfälle in
`tests/fixtures/legacy_clients_observed.json`, Parität für Anfragen und
Antwortverarbeitung (sync und async).

## Bewusste Verhaltensabweichungen

Vollständig in [docs/behavior-changes.md](docs/behavior-changes.md) (B1–B13).
Kurz: jede Meldung wird geschwärzt, Transportfehler ohne verkettete Ursache
(`from None`); keine Standard-URLs und kein lokaler Ollama-Fallback;
Flow-Agent ohne Schlüssel scheitert schon bei der Konfiguration; Health-Zählung
zentral, sobald eine `RouterHealth` übergeben wird; `stream_chat` wirft
HTTP-/Transportfehler statt Fehlerereignisse; Rerank mit falscher Score-Anzahl
setzt `degraded=True`; Retry und Breaker nur als Opt-in; Flow-Agent-Ablehnungen
als eigene Fehlerarten.

## Abhängigkeiten

Python ≥ 3.11, Kern nur Standardbibliothek. Extra `[http]`: `httpx>=0.23`
(BSD-3-Clause). `flow_agent_client` (Secret-Referenzen) ist keine
Abhängigkeit, der Resolver wird injiziert.

## Sicherheit und Datenschutz

- **Datenabfluss:** Prompts, Dokumente (OCR) und Texte (Embeddings, Rerank)
  gehen an das konfigurierte Gateway. Welche Modelle sie sehen dürfen, steuert
  die Sensitivität `X-Flow-Sensitivity` (nur hochstufbar); `restricted` ohne
  lokales Modell endet in `EgressDeniedError`, nicht in einem externen Aufruf.
- **Schlüssel:** nur aus Konfiguration oder Umgebung, bevorzugt als
  `secret://`-Referenz; nie in Meldungen, Logs, Health-Einträgen oder `repr`.
  Zugangsdaten, Query und Fragment in der Gateway-URL werden abgelehnt.
- **Zeitgrenzen:** je Operation über `Timeouts`; Zeitüberschreitungen werden
  nur mit `retry_timeout=True` wiederholt.
- Die Bibliothek speichert keine Prompts oder Antworten; `usage_hook` erhält
  nur Nutzungsdaten (`UsageRecord`).

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Der Rechteinhaber hat am 22.09.2026 entschieden, dass die
Bibliotheken unter MIT stehen, die Anwendungen nicht (`USER_AUTHORIZED_MIT`
nur für diese Bibliothek); Auftrag zum Bau vom 25.09.2026. Kein Code Dritter
enthalten. Quellen und Erklärung: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
