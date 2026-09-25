"""Line decoders for streamed chat answers.

* :class:`NdjsonDecoder` – Ollama ``/api/chat`` via the ai-router (cockpit
  ``chat_stream``): one JSON object per line, ``done`` ends the stream.
* :class:`SseDecoder` – OpenAI server-sent events via the Flow-Agent
  (``data: {...}``, ``data: [DONE]``).

Both yield :class:`StreamEvent` objects and stop after ``DONE`` or ``ERROR``.
"""

from __future__ import annotations

import json

from auditcore_llm_client.jsontypes import JsonObject, as_int, as_list, as_object, as_text
from auditcore_llm_client.results import StreamEvent, StreamEventKind

#: Characters of an in-stream error kept in the event (legacy: 300).
STREAM_ERROR_CHARS = 300
_NANOS_PER_MS = 1_000_000


def _load(line: str) -> JsonObject | None:
    try:
        parsed: object = json.loads(line)
    except ValueError:
        return None
    return as_object(parsed) if isinstance(parsed, dict) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


class NdjsonDecoder:
    """Ollama NDJSON stream."""

    def __init__(self) -> None:
        self.finished = False

    def feed(self, line: str) -> list[StreamEvent]:
        """Events contained in one line (invalid lines are skipped as before)."""
        line = line.strip()
        if self.finished or not line:
            return []
        obj = _load(line)
        if obj is None:
            return []
        if obj.get("error"):
            self.finished = True
            error = as_text(obj.get("error"))[:STREAM_ERROR_CHARS]
            return [StreamEvent(StreamEventKind.ERROR, error=error)]
        events: list[StreamEvent] = []
        delta = as_text(as_object(obj.get("message")).get("content"))
        if delta:
            events.append(StreamEvent(StreamEventKind.DELTA, delta=delta))
        if obj.get("done"):
            self.finished = True
            events.append(self._done(obj))
        return events

    @staticmethod
    def _done(obj: JsonObject) -> StreamEvent:
        return StreamEvent(
            StreamEventKind.DONE,
            prompt_tokens=_optional_int(obj.get("prompt_eval_count")),
            completion_tokens=_optional_int(obj.get("eval_count")),
            eval_duration_ms=as_int(obj.get("eval_duration")) // _NANOS_PER_MS,
            total_duration_ms=as_int(obj.get("total_duration")) // _NANOS_PER_MS,
        )


class SseDecoder:
    """OpenAI-compatible server-sent events."""

    def __init__(self) -> None:
        self.finished = False
        self._usage: JsonObject = {}

    def feed(self, line: str) -> list[StreamEvent]:
        """Events contained in one ``data:`` line; other SSE fields are ignored."""
        line = line.strip()
        if self.finished or not line.startswith("data:"):
            return []
        data = line[len("data:"):].strip()
        if data == "[DONE]":
            return [self._done()]
        obj = _load(data)
        if obj is None:
            return []
        if obj.get("error"):
            self.finished = True
            error = as_text(obj.get("error"))[:STREAM_ERROR_CHARS]
            return [StreamEvent(StreamEventKind.ERROR, error=error)]
        if isinstance(obj.get("usage"), dict):
            self._usage = as_object(obj.get("usage"))
        return self._deltas(obj)

    @staticmethod
    def _deltas(obj: JsonObject) -> list[StreamEvent]:
        events: list[StreamEvent] = []
        for choice in as_list(obj.get("choices")):
            delta = as_text(as_object(as_object(choice).get("delta")).get("content"))
            if delta:
                events.append(StreamEvent(StreamEventKind.DELTA, delta=delta))
        return events

    def _done(self) -> StreamEvent:
        self.finished = True
        return StreamEvent(
            StreamEventKind.DONE,
            prompt_tokens=_optional_int(self._usage.get("prompt_tokens")),
            completion_tokens=_optional_int(self._usage.get("completion_tokens")),
        )


def decoder_for(path: str) -> NdjsonDecoder | SseDecoder:
    """SSE for OpenAI routes, NDJSON for the Ollama route."""
    return SseDecoder() if path.endswith("/v1/chat/completions") else NdjsonDecoder()
