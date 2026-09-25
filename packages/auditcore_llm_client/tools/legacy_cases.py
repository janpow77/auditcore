"""Characterisation cases: one legacy call, its canned responses and the library twin.

Each case names the legacy function (``legacy``), the equivalent library call
(``library``) and the responses the mock gateway returns in order. Bytes are
written as ``{"$bytes": "<latin-1 text>"}``. The API key is a neutral value that
none of the legacy redaction patterns recognise, to show whether the configured
key itself can leak.
"""

from __future__ import annotations

KEY = "k3y-Geheim-4711"
ROUTER = "http://router.test:7842"
AGENT = "https://agent.test"
PDF = {"$bytes": "%PDF-1.4 Prüfbeleg"}
MESSAGES = [{"role": "system", "content": "Du prüfst."}, {"role": "user", "content": "Hallo"}]
ECHO_403 = {"status": 403, "json": {"detail": f"Ungültiger X-Api-Key {KEY}"}}
CONNECT = {"raise": "connect", "message": f"connect failed http://user:{KEY}@router.test"}


def _case(case_id: str, legacy: dict[str, object], library: dict[str, object],
          responses: list[dict[str, object]]) -> dict[str, object]:
    return {"id": case_id, "legacy": legacy, "library": library, "responses": responses}


def call(fn: str, *args: object, **kwargs: object) -> dict[str, object]:
    """Call description (function or method name, positional and keyword arguments)."""
    return {"fn": fn, "args": list(args), "kwargs": kwargs}


OPENAI_ANSWER = {
    "model": "qwen3.5:35b",
    "choices": [{"message": {"role": "assistant", "content": "<think>t</think>Fallback"}}],
    "usage": {"prompt_tokens": 11, "completion_tokens": 3},
}

AUDIT_DESIGNER_CASES = [
    _case("ad-generate", call("call_llm", "System", "Frage"),
          call("generate", "Frage", system="System"),
          [{"json": {"model": "qwen3.5:35b", "prompt_eval_count": 5, "eval_count": 7,
                     "message": {"role": "assistant", "content": "<think>x</think>Antwort"}}}]),
    _case("ad-generate-options",
          call("call_llm", "S", "U", max_tokens=50, temperature=0.7, model="m1", seed=7,
               json_mode=True),
          call("generate", "U", system="S", max_tokens=50, temperature=0.7, model="m1", seed=7,
               json_mode=True),
          [{"json": {"message": {"content": "{}"}}}]),
    _case("ad-generate-fallback-404", call("call_llm", "S", "U"),
          call("generate", "U", system="S"),
          [{"status": 404, "text": "not found"}, {"json": OPENAI_ANSWER}]),
    _case("ad-generate-http-500", call("call_llm", "S", "U"), call("generate", "U", system="S"),
          [{"status": 500, "text": "upstream kaputt"}]),
    _case("ad-generate-key-echo", call("call_llm", "S", "U"), call("generate", "U", system="S"),
          [ECHO_403]),
    _case("ad-generate-unreachable", call("call_llm", "S", "U"),
          call("generate", "U", system="S"), [CONNECT]),
    _case("ad-chat", call("call_llm_with_messages", MESSAGES), call("chat", MESSAGES),
          [{"json": OPENAI_ANSWER}]),
    _case("ad-chat-params",
          call("call_llm_with_messages", MESSAGES, max_tokens=10, temperature=0.1, model="m2"),
          call("chat", MESSAGES, max_tokens=10, temperature=0.1, model="m2"),
          [{"json": {"choices": []}}]),
    _case("ad-ocr", call("call_ocr", PDF, "rechnung.pdf"),
          call("ocr", PDF, filename="rechnung.pdf"),
          [{"json": {"text": "Seite 1", "pages": [{"page": 1, "text": "Seite 1", "boxes": []}],
                     "spoke": "vision", "model": "tesseract", "duration_ms": 12,
                     "confidence": 0.91, "fields": {"iban": "DE00"}}}]),
    _case("ad-rerank", call("call_rerank", "frage", ["a", "b", "c"], top_k=2),
          call("rerank", "frage", ["a", "b", "c"], top_k=2),
          [{"json": {"results": [{"index": 2, "score": 0.9, "document": "c"},
                                 {"index": 0, "score": 0.1, "document": "a"},
                                 {"index": "x", "score": 1}],
                     "model": "bge-reranker-v2-m3", "spoke": "gpu", "duration_ms": 4}}]),
    _case("ad-rerank-fallback-404", call("call_rerank", "frage", ["a", "b", "c"]),
          call("rerank", "frage", ["a", "b", "c"]),
          [{"status": 404, "text": "not found"}, {"json": {"scores": [0.2, 0.3, 0.1]}}]),
    _case("ad-rerank-length-mismatch", call("call_rerank", "frage", ["a", "b"]),
          call("rerank", "frage", ["a", "b"]), [{"json": {"scores": [0.2]}}]),
    _case("ad-rerank-empty", call("call_rerank", "frage", []), call("rerank", "frage", []), []),
    _case("ad-embed", call("call_embed", ["a", "b"]), call("embed", ["a", "b"]),
          [{"json": {"embeddings": [[0.1, 0.2], [0.3, 0.4]], "model": "bge-m3", "spoke": "s",
                     "duration_ms": 3}}]),
    _case("ad-embed-fallback-404", call("call_embed", ["a", "b"]), call("embed", ["a", "b"]),
          [{"status": 404, "text": "nope"},
           {"json": {"data": [{"index": 1, "embedding": [2.0]}, {"index": 0, "embedding": [1.0]}],
                     "model": "bge-m3"}}]),
    _case("ad-embed-count-mismatch", call("call_embed", ["a", "b"]), call("embed", ["a", "b"]),
          [{"json": {"embeddings": [[0.1]]}}]),
    _case("ad-health", call("health"), call("health"),
          [{"json": {"status": "ok", "spokes": []}}]),
    _case("ad-health-503", call("health"), call("health"), [{"status": 503, "text": "degraded"}]),
    _case("ad-safe-llm-key-echo", call("safe_call_llm", "S", "U"),
          call("safe:generate", "U", system="S"), [ECHO_403]),
]

FI_GENERATE = {"model": "qwen3:14b", "response": "Antwort", "prompt_eval_count": 3,
               "eval_count": 4, "total_duration": 5_000_000}
FI_CHAT = {"model": "qwen3:14b", "choices": [{"message": {"content": "Chat"}}],
           "usage": {"prompt_tokens": 2, "completion_tokens": 1}}

FLOWINVOICE_CASES = [
    _case("fi-generate", call("call_llm", "Frage"), call("generate", "Frage"),
          [{"json": FI_GENERATE}]),
    _case("fi-generate-options",
          call("call_llm", "Frage", system="Sys", model="m", temperature=0.2, max_tokens=9,
               json_mode=True, extra_options={"num_ctx": 8192, "top_p": 0.9}),
          call("generate", "Frage", system="Sys", model="m", temperature=0.2, max_tokens=9,
               json_mode=True, options={"num_ctx": 8192, "top_p": 0.9}),
          [{"json": FI_GENERATE}]),
    _case("fi-generate-http-502", call("call_llm", "Frage"), call("generate", "Frage"),
          [{"status": 502, "text": "bad gateway"}]),
    _case("fi-chat", call("call_llm_with_messages", MESSAGES), call("chat", MESSAGES),
          [{"json": FI_CHAT}]),
    _case("fi-chat-json",
          call("call_llm_with_messages", MESSAGES, temperature=0.0, max_tokens=5, json_mode=True),
          call("chat", MESSAGES, temperature=0.0, max_tokens=5, json_mode=True),
          [{"json": FI_CHAT}]),
    _case("fi-ocr",
          call("call_ocr", PDF, filename="beleg.png", content_type="image/png",
               model="tesseract", language="deu"),
          call("ocr", PDF, filename="beleg.png", content_type="image/png", model="tesseract",
               language="deu"),
          [{"json": {"text": "Beleg", "pages": [], "spoke": "vision", "model": "tesseract",
                     "duration_ms": 9, "confidence": 0.5}}]),
    _case("fi-rerank", call("call_rerank", "q", ["a", "b"], top_k=1),
          call("rerank", "q", ["a", "b"], top_k=1),
          [{"json": {"scores": [0.4, 0.6], "model": "ce", "duration_ms": 2}}]),
    _case("fi-rerank-results", call("call_rerank", "q", ["a", "b"]),
          call("rerank", "q", ["a", "b"]),
          [{"json": {"results": [{"index": 1, "score": 0.8, "document": "b"}]}}]),
    _case("fi-rerank-length-mismatch", call("call_rerank", "q", ["a", "b"]),
          call("rerank", "q", ["a", "b"]), [{"json": {"scores": [1.0]}}]),
    _case("fi-embed", call("call_embed", ["a", "b"]), call("embed", ["a", "b"]),
          [{"json": {"data": [{"index": 1, "embedding": [0.2]}, {"index": 0, "embedding": [0.1]}],
                     "model": "bge-m3"}}]),
    _case("fi-embed-count-mismatch", call("call_embed", ["a", "b"]), call("embed", ["a", "b"]),
          [{"json": {"data": []}}]),
    _case("fi-embed-unreachable", call("call_embed", ["a"]), call("embed", ["a"]), [CONNECT]),
    _case("fi-health", call("health"), call("health"), [{"json": {"status": "ok"}}]),
    _case("fi-health-not-json", call("health"), call("health"), [{"text": "OK"}]),
    _case("fi-safe-llm-key-echo", call("safe_call_llm", MESSAGES), call("safe:chat", MESSAGES),
          [ECHO_403]),
]

FA_GENERATE = {"request_id": "r1", "app_id": "flowinvoice", "model_id": "qwen3:32b",
               "worker_ids": ["w1"], "content": "Antwort", "route_mode": "local"}
FA_HEADERS = {"X-Flow-Agent-Request-Id": "r1", "X-Flow-Agent-Model": "qwen3:32b",
              "X-Flow-Agent-Workers": "w1,w2"}

FLOW_AGENT_CASES = [
    _case("fa-generate",
          call("call_llm", "Frage", system="Sys", max_tokens=100, json_mode=True,
               extra_options={"num_ctx": 16384}),
          call("generate", "Frage", system="Sys", max_tokens=100, json_mode=True,
               options={"num_ctx": 16384}),
          [{"json": FA_GENERATE, "headers": FA_HEADERS}]),
    _case("fa-generate-defaults", call("call_llm", "Frage"), call("generate", "Frage"),
          [{"json": FA_GENERATE}]),
    _case("fa-chat", call("call_llm_with_messages", MESSAGES, model="gpt-4"),
          call("chat", MESSAGES, model="gpt-4"),
          [{"json": FI_CHAT, "headers": FA_HEADERS}]),
    _case("fa-ocr",
          call("call_ocr", PDF, filename="scan.png", content_type="image/png", model="Tesseract",
               language="de"),
          call("ocr", PDF, filename="scan.png", content_type="image/png", model="Tesseract",
               language="de"),
          [{"json": {"backend": "tesseract", "text": "Hallo", "confidence": 0.8,
                     "duration_ms": 40}, "headers": {"X-Flow-Agent-Capability": "ocr"}}]),
    _case("fa-ocr-auto", call("call_ocr", PDF), call("ocr", PDF),
          [{"json": {"text": "Hallo"}}]),
    _case("fa-rerank", call("call_rerank", "q", ["a", "b"], top_k=1, model="ignored"),
          call("rerank", "q", ["a", "b"], top_k=1, model="ignored"),
          [{"json": {"scores": [0.1, 0.9]}}]),
    _case("fa-embed", call("call_embed", ["a"], model="ignored"),
          call("embed", ["a"], model="ignored"),
          [{"json": {"data": [{"index": 0, "embedding": [0.5]}]}}]),
    _case("fa-health", call("health"), call("health"),
          [{"json": {"status": "assigned", "request_id": "r", "app_id": "flowinvoice"}}]),
    _case("fa-health-embedding", call("health", capability="embedding"),
          call("health", capability="embedding"), [{"json": {"status": "assigned"}}]),
    _case("fa-health-not-assigned", call("health"), call("health"),
          [{"json": {"status": "rejected", "reasons": ["kein Worker"]}}]),
    _case("fa-generate-401", call("call_llm", "Frage"), call("generate", "Frage"),
          [{"status": 401, "json": {"detail": "Ungueltiger AI-Schluessel."}}]),
]

AUDIT_PORTAL_CASES = [
    _case("ap-generate", call("call_llm", "Frage"), call("generate", "Frage"),
          [{"json": FI_GENERATE}]),
    _case("ap-chat", call("call_llm_with_messages", MESSAGES), call("chat", MESSAGES),
          [{"json": FI_CHAT}]),
    _case("ap-embed", call("call_embed", ["a"]), call("embed", ["a"]),
          [{"json": {"data": [{"index": 0, "embedding": [1.5]}]}}]),
    _case("ap-health", call("health"), call("health"), [{"json": {"status": "ok"}}]),
]

TAGS = {"models": [
    {"name": "qwen3:14b", "size": 123, "details": {"parameter_size": "14B", "family": "qwen3"}},
    "kaputt",
    {"name": "bge-m3", "size": "n/a", "details": "none"},
]}
STREAM_LINES = [
    '{"message": {"content": "Hal"}}', "kein json", "",
    '{"message": {"content": "lo"}, "done": false}',
    '{"message": {"content": ""}, "done": true, "eval_count": 2, "prompt_eval_count": 3, '
    '"eval_duration": 2000000, "total_duration": 5000000}',
    '{"message": {"content": "nachlauf"}}',
]

COCKPIT_CASES = [
    _case("ck-models", call("_fetch_models"), call("snapshot"), [{"json": TAGS}]),
    _case("ck-models-empty", call("_fetch_models"), call("snapshot"),
          [{"json": {"models": []}}]),
    _case("ck-models-429", call("_fetch_models"), call("snapshot"),
          [{"status": 429, "text": "slow down", "headers": {"Retry-After": "7"}}]),
    _case("ck-models-401", call("_fetch_models"), call("snapshot"),
          [{"status": 401, "text": "no"}]),
    _case("ck-models-500", call("_fetch_models"), call("snapshot"),
          [{"status": 500, "text": "boom"}]),
    _case("ck-models-invalid", call("_fetch_models"), call("snapshot"),
          [{"json": {"foo": 1}}]),
    _case("ck-models-unreachable", call("_fetch_models"), call("snapshot"), [CONNECT]),
    _case("ck-stream", call("chat_stream", "qwen3:14b", MESSAGES, options={"num_ctx": 4096},
                            think=False),
          call("stream", MESSAGES, model="qwen3:14b", options={"num_ctx": 4096}, think=False),
          [{"lines": STREAM_LINES}]),
    _case("ck-stream-error-line", call("chat_stream", "qwen3:14b", MESSAGES),
          call("stream", MESSAGES, model="qwen3:14b"),
          [{"lines": ['{"message": {"content": "a"}}', '{"error": "model not found"}']}]),
    _case("ck-stream-http-500", call("chat_stream", "qwen3:14b", MESSAGES),
          call("stream", MESSAGES, model="qwen3:14b"),
          [{"status": 500, "text": f"proxy error for key {KEY}"}]),
    _case("ck-stream-unreachable", call("chat_stream", "qwen3:14b", MESSAGES),
          call("stream", MESSAGES, model="qwen3:14b"), [CONNECT]),
]
