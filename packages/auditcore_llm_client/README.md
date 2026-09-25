# auditcore_llm_client

Client für den **ai-router** und das **Flow-Agent-Inferenz-Gateway**. Er ersetzt die
fast gleichen AI-Router-Clients in audit_designer, flowinvoice und audit-portal
(zusammen rund 3.100 Zeilen) und den schlanken Client in cockpit.

Grundsatz: **FlowAgent ist der einzige GPU-Weg.** Die Bibliothek spricht nur mit
einer konfigurierten Gateway-URL (Flow-Agent oder ai-router). Direkte Aufrufe an
Ollama, vLLM oder GPU-Hosts gibt es nicht; URLs mit dem Ollama-Port 11434 werden
abgelehnt, einen lokalen Fallback gibt es nicht.

## Installation

```bash
pip install 'auditcore_llm_client[http]'   # mit httpx (sync + async Client)
pip install auditcore_llm_client           # nur Kern: Konfiguration, Requests, Parser, Schwärzung
```

Der Kern braucht nur die Standardbibliothek. `LlmClient` und `AsyncLlmClient`
benötigen das Extra `http` (httpx ≥ 0.23, Debian: `python3-httpx`).

## Schnellstart

```python
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

## API

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
(`public|internal|confidential|restricted`) und weitere, nicht
authentisierende Header (`extra_headers`).

## Fehler

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

## Wiederholungen und Circuit-Breaker

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

## Profile je App

| Profil | Umgebung | Unterschiede |
|---|---|---|
| `AUDIT_DESIGNER` | `LLM_ROUTER_URL/APP_ID/API_KEY`, Modell `VP_AI_EGPU_MODEL` → `OLLAMA_MODEL`, `VP_AI_LLM_KEEP_ALIVE` | `generate` über `/api/chat` mit festen Optionen (`num_ctx` 16384, `top_p` 0,8, `top_k` 20, `repeat_penalty` 1,05, `think=false`, `keep_alive`), Standard 0,2/4000 Tokens, `<think>` entfernen, Rerank/Embed mit 404-Rückfall, `/health` mit Auth-Headern |
| `FLOWINVOICE` | wie oben + `FLOW_AGENT_URL/APP_ID/APP_KEY/QUALITY`, `OLLAMA_DEFAULT_MODEL`, `EMBEDDING_MODEL`, `RERANKER_MODEL` | `/api/generate`, OpenAI-Rerank/Embed, `/health` ohne Header; gesetzte `FLOW_AGENT_URL` schaltet in den Flow-Agent-Modus |
| `AUDIT_PORTAL` | wie flowinvoice ohne Flow-Agent, App-ID `audit-portal` | Metering über `ClientConfig.usage_hook` (ersetzt `record_llm_usage`) |
| `COCKPIT` | `AI_ROUTER_URL/APP_ID/API_KEY` | Modellliste und NDJSON-Streaming |
| `GENERIC` | `AI_ROUTER_*`, `FLOW_AGENT_*` | neutrale Voreinstellung für neue Consumer |

Abweichungen vom Altverhalten: [docs/behavior-changes.md](docs/behavior-changes.md).
Charakterisierung: 60 ausgeführte Altfälle in `tests/fixtures/legacy_clients_observed.json`.
