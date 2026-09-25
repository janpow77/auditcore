# auditcore_llm_client

## Zweck

Client für den ai-router und das Flow-Agent-Inferenz-Gateway – Chat, Streaming, Embeddings, Reranking, OCR und Health – mit App-Profilen, Schwärzung, Wiederholungen und Circuit-Breaker.

Ersetzt die fast gleichen AI-Router-Clients in audit_designer, flowinvoice und
audit-portal und den schlanken Client in cockpit. Grundsatz: **FlowAgent ist
der einzige GPU-Weg** – die Bibliothek spricht nur mit einer konfigurierten
Gateway-URL; direkte Aufrufe an Ollama, vLLM oder GPU-Hosts, eine Standard-URL
und ein lokaler Fallback gehören ausdrücklich nicht dazu.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_llm_client[http]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Version 0.1.1 ist noch in keinem Release veröffentlicht. Nach der
Veröffentlichung steht die Direkt-URL mit Hash im Index unter
`https://janpow77.github.io/auditcore/simple/auditcore-llm-client/`; Muster für
eine hashgebundene `requirements.txt`:

```text
auditcore_llm_client @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_llm_client-0.1.1-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)); das Paket schlägt
`python3-httpx` vor:

```bash
sudo apt-get install python3-auditcore-llm-client python3-httpx
```

Extras: `[http]` – synchroner und asynchroner HTTP-Client über httpx;
`[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Ohne Extra: Konfiguration aus der Umgebung, Request-Aufbau und Schwärzung.

```python
from auditcore_llm_client import AUDIT_DESIGNER, config_from_env, redact
from auditcore_llm_client.wire import request_headers
from auditcore_llm_client.wire_llm import Sampling, build_generate

config = config_from_env(AUDIT_DESIGNER, {"LLM_ROUTER_URL": "http://router.test:7842",
                                          "LLM_ROUTER_API_KEY": "k3y-4711"})
request = build_generate(config, "Prüfe den Beleg.", "Du bist Prüfer.", Sampling())
assert request.path == "/api/chat" and request.fallback_on_404 is not None
assert request_headers(config, request.headers)["X-App-Id"] == "audit_designer"
assert "k3y-4711" not in repr(config)
assert redact("Fehler: k3y-4711", secrets=config.secrets) == "Fehler: <redacted>"
```

```pycon
>>> request.json_body["options"]["num_ctx"]
16384
```

Mit Extra `[http]` (Transport für Tests injizierbar):

```python no-run
import httpx
from auditcore_llm_client import LlmClient, RouterHealth

def gateway(req: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"message": {"content": "<think>…</think>Antwort"}})

with LlmClient(config, transport=httpx.MockTransport(gateway),
               health=RouterHealth.shared()) as client:
    assert client.generate("Prüfe den Beleg.", system="Du bist Prüfer.").content == "Antwort"
```

`AsyncLlmClient` bietet dieselben Methoden asynchron (`await client.chat(...)`,
`async for event in client.stream_chat(...)`).

## API-Überblick

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

`config_from_env(profile, environ, secret_resolver=None)` liest die
Umgebungsnamen der jeweiligen App. Es gibt **keine** Standard-URL und keinen
Standardschlüssel; eine fehlende URL ist ein `ConfigurationError`.

| Profil | Umgebung | Unterschiede |
|---|---|---|
| `AUDIT_DESIGNER` | `LLM_ROUTER_URL/APP_ID/API_KEY`, Modell `VP_AI_EGPU_MODEL` → `OLLAMA_MODEL`, `VP_AI_LLM_KEEP_ALIVE` | `generate` über `/api/chat` mit festen Optionen (`num_ctx` 16384, `top_p` 0,8, `top_k` 20, `repeat_penalty` 1,05, `think=false`, `keep_alive` 10m), Standard 0,2/4000 Tokens, `<think>` entfernen, Rerank/Embed mit 404-Rückfall, `/health` mit Auth-Headern |
| `FLOWINVOICE` | wie oben + `FLOW_AGENT_URL/APP_ID/APP_KEY/QUALITY`, `OLLAMA_DEFAULT_MODEL`, `EMBEDDING_MODEL`, `RERANKER_MODEL` | `/api/generate`, OpenAI-Rerank/Embed, `/health` ohne Header; gesetzte `FLOW_AGENT_URL` schaltet auf die app-gebundenen Flow-Agent-Routen (Bearer, Qualitätsstufe statt Modell, `/ready?capability`) |
| `AUDIT_PORTAL` | wie flowinvoice ohne Flow-Agent, App-ID `audit-portal` | Metering über `ClientConfig.usage_hook` |
| `COCKPIT` (**abgekündigt**) | `AI_ROUTER_URL/APP_ID/API_KEY` | Modellliste mit Cache, NDJSON-Streaming; cockpit wird abgeschaltet (flow-agent #50) |
| `GENERIC` | `AI_ROUTER_*`, `FLOW_AGENT_*` | neutrale Voreinstellung für neue Anwendungen |

Laufparameter in `ClientConfig`: `timeouts` (LLM 600 s, OCR 180 s, Rerank 30 s,
Embed 60 s, Health 10 s, Modelle 6 s), `retry` (`RetryPolicy`, Standard ein
Versuch), `breaker` (`BreakerPolicy`, Standard aus; 3 Ausfälle/180 s),
`quality` (`fast|balanced|high`), `sensitivity`, `extra_headers`, `usage_hook`.

**Sensitivität (Flow-Agent):** `X-Flow-Sensitivity`
(`public|internal|confidential|restricted`); wirksam ist das Maximum aus
App-Default und Header, der Header kann nur hochstufen, ohne Header gilt
`internal`. Ungültiger Wert → HTTP 400 → `SensitivityRejectedError`; lässt die
wirksame Sensitivität kein Modell zu → HTTP 403 → `EgressDeniedError` (Audit
`ai.egress-denied`, kein Upstream-Aufruf). Erkannt am Header
`X-Flow-Agent-Error` (`invalid-sensitivity`, `egress-denied`), bei älteren
Gateways am `detail`-Text. Beide werden nicht wiederholt und weder vom Breaker
noch von `RouterHealth` gezählt.

**Denken:** `reasoning_effort` (`none|low|medium|high`) für `generate`, `chat`,
`stream_chat`; Ollama-Routen erhalten `think`. Ohne Angabe setzt der ai-router
für `qwen3.5*` selbst `reasoning_effort=none` bzw. `think=false`.

## Herkunft und Charakterisierung

Neuimplementierung nach dem ausgeführten Verhalten der Altclients
(`provenance.json`, Blob-SHAs je Datei): audit_designer `ccd6524`
(`backend/app/utils/ai_router_client.py`), flowinvoice `fb2d185`
(`backend/app/clients/ai_router_client.py`, `backend/app/llm/ollama.py`),
audit-portal `d8eefa4`, cockpit `df203d4`
(`src/cockpit/services/ai_router_client.py`); Routen und Verträge gelesen aus
ai-router `426cd78` und flow-agent `873636a`.
`tools/capture_legacy_clients.py` lässt die vier Altclients gegen
`httpx.MockTransport` laufen: 60 Fälle in
`tests/fixtures/legacy_clients_observed.json`. Die Bibliothek erzeugt in allen
60 Fällen dieselben Anfragen (Methode, URL, Header, Body) und Ergebnisse,
synchron wie asynchron.

## Bewusste Verhaltensabweichungen

Schwärzung aller Meldungen, Logs und Health-Einträge inkl. des konfigurierten
Schlüssels, keine verketteten Transport-Exceptions, keine Standard-URL,
Flow-Agent ohne Schlüssel fail-closed, kein Ollama-Fallback, Stream-Fehler als
Exception, eigene Fehlerarten für Sensitivität/Egress – vollständig mit
Begründung in [docs/behavior-changes.md](docs/behavior-changes.md) (B1–B13).

## Abhängigkeiten

Python ≥ 3.11. Keine Pflichtabhängigkeiten; der Kern nutzt nur die
Standardbibliothek. Extra `http`: httpx ≥ 0.23 (Debian `python3-httpx`).
Bewusst keine Abhängigkeit auf `flow_agent_client` – ein Secret-Resolver wird
injiziert.

## Sicherheit und Datenschutz

- Netzwerk nur zur konfigurierten Gateway-URL; URLs mit Zugangsdaten, Query
  oder dem Ollama-Port 11434 werden abgelehnt.
- Prompts, Dokumente (OCR) und Texte können personenbezogene Daten enthalten;
  die Bibliothek speichert nichts und loggt keine Inhalte, Header oder Bodies.
- Schlüssel nur aus Konfiguration/Umgebung, gehalten als `SecretValue` (nie im
  `repr`); bevorzugt als `secret://<anbieter>/<name>`-Referenz, aufgelöst über
  Flow-Agent `POST /api/v1/secrets/use` mit einem injizierten Resolver, z. B.
  `flow_agent_client.secret_refs.SecretResolver.from_env().resolve`. Ohne
  Resolver ist eine Referenz ein `ConfigurationError`.
- Jede Fehlermeldung, jeder Log- und Health-Eintrag wird geschwärzt
  (konfigurierter Schlüssel, URLs, DSNs, Bearer-, `X-Api-Key`-, `sk-`-,
  GitHub-Token).

## Lizenz und Herkunftsnachweis

MIT ([LICENSE](LICENSE)); Freigabe des Rechteinhabers vom 22.09.2026 nur für
diese Bibliothek, die Quellrepositories behalten ihre Lizenz. Herkunft und
Freigabe: [NOTICE](NOTICE), [provenance.json](provenance.json).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
