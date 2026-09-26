# Changelog – auditcore_llm_client

## 0.1.2 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1.

## 0.1.1 – Stabiler Fehlercode des Flow-Agents

- `SensitivityRejectedError`/`EgressDeniedError` werden primär am Response-Header
  `X-Flow-Agent-Error` erkannt (`invalid-sensitivity` mit HTTP 400,
  `egress-denied` mit HTTP 403; flow-agent #56, main `873636a4`). Die
  Texterkennung („Sensitivität“/„Egress“ im `detail`) bleibt Rückfall für
  Gateways ohne Header. Ein Header-Code mit unpassendem Status ergibt einen
  gewöhnlichen `RouterHttpError`.

## 0.1.0 – Erste Fassung

- Client für ai-router und Flow-Agent-Gateway, synchron (`LlmClient`) und
  asynchron (`AsyncLlmClient`, ein httpx-Client je Event-Loop); Transport
  injizierbar, httpx nur im Extra `http`.
- Operationen: `generate`, `chat`, `stream_chat` (NDJSON/SSE), `embed`,
  `rerank`, `ocr`, `health` (Flow-Agent-Readiness je Capability),
  `list_models`/`model_snapshot` (cockpit-Cache).
- Profile `AUDIT_DESIGNER`, `FLOWINVOICE`, `AUDIT_PORTAL`, `COCKPIT`, `GENERIC`
  bilden die charakterisierten Unterschiede der Altclients ab;
  `config_from_env` liest die Umgebungsnamen der Apps, ohne Standard-URL und
  ohne Standardschlüssel.
- Strukturierte Fehler, Schwärzung aller Meldungen/Logs/Health-Einträge
  (konfigurierter Schlüssel, URLs, DSNs, Token), keine verketteten
  Transport-Exceptions.
- `RetryPolicy` (exponentielles Backoff, `Retry-After`), `CircuitBreaker`,
  `RouterHealth` (60 s/3 Fehler), `safe_call`/`async_safe_call`, `usage_hook`.
- Flow-Agent-Richtlinien: `SensitivityRejectedError` (HTTP 400) und
  `EgressDeniedError` (HTTP 403) als eigene Fehlerarten, ohne Wiederholung,
  Breaker- oder Health-Zählung (Vertrag flow-agent `1d49ec3c`).
- `reasoning_effort` für `generate`/`chat`/`stream_chat` (Ollama: `think`).
- `secret://`-Schlüssel über injizierten Resolver (`config_from_env(...,
  secret_resolver=...)`), ohne Abhängigkeit auf `flow_agent_client`.
- Profil `COCKPIT` als abgekündigt markiert (`Profile.deprecated`).
- Charakterisierung: 60 ausgeführte Fälle der vier Altclients, Parität für
  Anfragen und Antwortverarbeitung (sync und async), Abweichungen B1–B12.
