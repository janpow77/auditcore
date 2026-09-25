"""Donut-Port: strukturierte Belegfelder aus einem Seitenbild (Plan 2a).

Drei Umsetzungen desselben Vertrags ``DonutPort``:

* ``HttpDonut`` – gegen den vision-service (``POST /v1/vision/parse``) oder die
  FlowAgent-Plattform (``flowagent_donut``); der Transport ist ein Port wie
  ``post``/``fetch_url``. Ohne Port: ``DONUT_NOT_CONFIGURED`` statt Netzwerk.
* ``LocalDonut`` – Offline-Inferenz im Prozess (Extra ``donut``: torch,
  transformers, sentencepiece, pillow). Lädt nur ein lokales Verzeichnis
  (``local_files_only``) und verweigert das Laden bei abweichender
  SHA-256 der Gewichtsdatei (``DONUT_MODEL_HASH_MISMATCH``).
* ``FakeDonut`` – Contract-Tests ohne Torch.

Donut-Ausgaben sind **Vorschlagswerte**: Übernommen werden sie erst durch
``DonutFieldMergeStage`` nach Pflicht-Plausibilitätsprüfung.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from auditcore_common.hashing import sha256_file

from auditcore_documents.pipeline.stages.base import StageError

SCHEMA_VERSION = "auditcore_invoice_v1"
TASK_TOKEN = f"<s_{SCHEMA_VERSION}>"
SEPARATOR = "<sep/>"
LIST_FIELDS = frozenset({"vat_lines"})
WEIGHTS_FILE = "model.safetensors"


@dataclass(frozen=True)
class DonutResult:
    """Ergebnis einer Seite."""

    fields: dict[str, Any]
    raw_sequence: str = ""
    field_confidence: dict[str, float] = field(default_factory=dict)
    model_id: str = "unknown"
    model_sha256: str = ""
    duration_ms: int = 0
    device: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": self.fields,
            "raw_sequence": self.raw_sequence,
            "field_confidence": self.field_confidence,
            "model_id": self.model_id,
            "model_sha256": self.model_sha256,
            "duration_ms": self.duration_ms,
            "device": self.device,
        }


class DonutPort(Protocol):
    def available(self) -> bool: ...

    def parse(self, page_png: bytes) -> DonutResult: ...


def _error(code: str, message: str, *, recoverable: bool = False) -> StageError:
    return StageError(stage="ocr", error_code=code, message=message, recoverable=recoverable)


# --------------------------------------------------------------------------- Tokenfolge
_OPEN = re.compile(r"<s_([a-z_0-9]+)>")


def _decode(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    position = 0
    while True:
        match = _OPEN.search(text, position)
        if match is None:
            return result
        key = match[1]
        close = f"</s_{key}>"
        end = text.find(close, match.end())
        if end == -1:
            position = match.end()
            continue
        content = text[match.end() : end]
        position = end + len(close)
        if key in LIST_FIELDS:
            result[key] = [_decode(p) for p in content.split(SEPARATOR) if _OPEN.search(p)]
        elif _OPEN.search(content):
            result[key] = _decode(content)
        else:
            result[key] = content.strip()


def parse_donut_sequence(sequence: str) -> dict[str, Any]:
    """Donut-Tokenfolge (``<s_feld>wert</s_feld>``) → Ziel-JSON; Fragmente werden verworfen."""
    text = sequence.replace("</s>", "").replace("<s>", "").replace("<pad>", "")
    return _decode(text.replace(TASK_TOKEN, "", 1))


def field_confidences(tokens: Sequence[str], probabilities: Sequence[float]) -> dict[str, float]:
    """Minimale Tokenwahrscheinlichkeit je Blattfeld (``supplier.vat_id``, ``vat_lines.0.rate``)."""
    stack: list[str] = []
    list_index: dict[str, int] = {}
    result: dict[str, float] = {}
    for token, probability in zip(tokens, probabilities, strict=True):
        opening = re.fullmatch(r"<s_([a-z_0-9]+)>", token)
        closing = re.fullmatch(r"</s_([a-z_0-9]+)>", token)
        if opening and opening[1] != SCHEMA_VERSION:
            stack.append(opening[1])
            if opening[1] in LIST_FIELDS:
                list_index.setdefault(opening[1], 0)
            continue
        if closing:
            if stack and stack[-1] == closing[1]:
                stack.pop()
            continue
        if token == SEPARATOR and stack and stack[-1] in LIST_FIELDS:
            list_index[stack[-1]] += 1
            continue
        if not stack:
            continue
        parts: list[str] = []
        for name in stack:
            parts.append(name)
            if name in LIST_FIELDS:
                parts.append(str(list_index.get(name, 0)))
        key = ".".join(parts)
        result[key] = min(result.get(key, 1.0), float(probability))
    return result


# --------------------------------------------------------------------------- Fake
class FakeDonut:
    """Vorgegebene Ergebnisse (Liste der Reihe nach oder Funktion des Seitenbilds)."""

    def __init__(
        self,
        results: Sequence[DonutResult] | Callable[[bytes], DonutResult],
        *,
        is_available: bool = True,
    ) -> None:
        self._results = results
        self._available = is_available
        self.calls: list[bytes] = []

    def available(self) -> bool:
        return self._available

    def parse(self, page_png: bytes) -> DonutResult:
        self.calls.append(page_png)
        if callable(self._results):
            return self._results(page_png)
        index = min(len(self.calls), len(self._results)) - 1
        return self._results[index]


# --------------------------------------------------------------------------- HTTP
class MultipartPost(Protocol):
    def __call__(
        self,
        url: str,
        *,
        files: Mapping[str, tuple[str, bytes, str]],
        data: Mapping[str, str],
        timeout: float,
    ) -> tuple[int, bytes]: ...


class HttpDonut:
    """vision-service ``/v1/vision/parse`` bzw. FlowAgent-Plattform über den ``post``-Port."""

    def __init__(
        self,
        post: MultipartPost | None,
        base_url: str,
        *,
        model: str = "donut-invoice-de",
        path: str = "/v1/vision/parse",
        timeout: float = 300.0,
        expected_model_sha256: str | None = None,
        timer: Callable[[], float] = time.monotonic,
    ) -> None:
        self.post = post
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.path = path
        self.timeout = timeout
        self.expected_model_sha256 = expected_model_sha256
        self.timer = timer

    def available(self) -> bool:
        return self.post is not None and bool(self.base_url)

    def parse(self, page_png: bytes) -> DonutResult:
        if not self.available() or self.post is None:
            raise _error("DONUT_NOT_CONFIGURED", "Kein Donut-Transport konfiguriert")
        start = self.timer()
        try:
            status, body = self.post(
                self.base_url + self.path,
                files={"image": ("seite.png", page_png, "image/png")},
                data={"model": self.model},
                timeout=self.timeout,
            )
        except StageError:
            raise
        except Exception as exc:  # noqa: BLE001 - Transportfehler des Ports
            raise _error(
                "DONUT_UNAVAILABLE", f"Donut-Dienst nicht erreichbar: {exc}", recoverable=True
            ) from exc
        if status >= 500 or status == 429:
            raise _error("DONUT_UNAVAILABLE", f"Donut-Dienst antwortet {status}", recoverable=True)
        if status >= 400:
            raise _error("DONUT_FAILED", f"Donut-Dienst lehnt ab: {status}")
        try:
            payload = json.loads(body)
        except ValueError as exc:
            raise _error("DONUT_FAILED", "Antwort ist kein JSON") from exc
        return self.result_from_payload(payload, int((self.timer() - start) * 1000))

    def result_from_payload(self, payload: Mapping[str, Any], elapsed_ms: int) -> DonutResult:
        """Antwort des vision-service/der Plattform auf ``DonutResult`` abbilden."""
        raw = str(payload.get("raw") or payload.get("raw_sequence") or "")
        parsed = payload.get("json")
        if not isinstance(parsed, dict) or not parsed:
            parsed = parse_donut_sequence(raw) if TASK_TOKEN in raw else payload.get("fields")
        if not isinstance(parsed, dict):
            raise _error("DONUT_FAILED", "Antwort enthält keine Felder")
        sha = str(payload.get("model_sha256") or "")
        if self.expected_model_sha256 and sha != self.expected_model_sha256:
            raise _error("DONUT_MODEL_HASH_MISMATCH", "Modell-Prüfsumme des Dienstes weicht ab")
        confidence = payload.get("field_confidence") or {}
        return DonutResult(
            fields=parsed,
            raw_sequence=raw,
            field_confidence={str(k): float(v) for k, v in dict(confidence).items()},
            model_id=str(payload.get("model_id") or payload.get("model") or self.model),
            model_sha256=sha,
            duration_ms=int(payload.get("duration_ms") or elapsed_ms),
            device=str(payload.get("device") or "unknown"),
        )


def flowagent_donut(
    post: MultipartPost | None, platform_url: str, *, app: str = "flowinvoice", **kwargs: Any
) -> HttpDonut:
    """Donut über die FlowAgent-Plattform (Spoke-Wahl durch die Plattform, E7)."""
    return HttpDonut(post, platform_url, path=f"/api/v1/ai/apps/{app}/v1/vision/parse", **kwargs)


# --------------------------------------------------------------------------- Lokal
def verify_model_dir(model_dir: Path, expected_sha256: str) -> str:
    """SHA-256 der Gewichtsdatei prüfen, bevor irgendetwas geladen wird."""
    weights = model_dir / WEIGHTS_FILE
    if not weights.is_file():
        raise _error("DONUT_MODEL_MISSING", f"Gewichtsdatei fehlt: {weights}")
    actual = sha256_file(weights)
    if actual != expected_sha256:
        raise _error("DONUT_MODEL_HASH_MISMATCH", "SHA-256 der Donut-Gewichte weicht ab")
    return actual


class LocalDonut:
    """Offline-Inferenz (Extra ``donut``); nie Netzwerkzugriff, Prüfsumme vor dem Laden."""

    def __init__(
        self,
        model_dir: Path,
        expected_sha256: str,
        *,
        device: str = "auto",
        model_id: str = "auditcore-donut-invoice-de",
        max_length: int = 512,
        timer: Callable[[], float] = time.monotonic,
    ) -> None:
        self.model_dir = Path(model_dir)
        self.expected_sha256 = expected_sha256
        self.device = device
        self.model_id = model_id
        self.max_length = max_length
        self.timer = timer
        self._loaded: tuple[Any, Any, Any, str] | None = None

    def available(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError:
            return False
        return (self.model_dir / WEIGHTS_FILE).is_file()

    def _load(self) -> tuple[Any, Any, Any, str]:
        if self._loaded is not None:
            return self._loaded
        verify_model_dir(self.model_dir, self.expected_sha256)
        try:
            import torch
            from transformers import (
                AutoTokenizer,
                DonutImageProcessor,
                VisionEncoderDecoderModel,
            )
        except ImportError as exc:
            raise _error(
                "DONUT_DEPENDENCY_MISSING", "Bitte auditcore_documents[donut] installieren"
            ) from exc
        device = self.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        # B615 trifft nicht zu: geladen wird nur ein lokales, zuvor per SHA-256 geprüftes
        # Verzeichnis mit local_files_only=True; ein Hub-Download ist ausgeschlossen
        # (Test test_local_donut_verifies_hash_before_loading).
        local = str(self.model_dir)
        processor = DonutImageProcessor.from_pretrained(local, local_files_only=True)  # nosec B615
        tokenizer = AutoTokenizer.from_pretrained(local, local_files_only=True)  # nosec B615
        model = VisionEncoderDecoderModel.from_pretrained(  # nosec B615
            local, use_safetensors=True, local_files_only=True
        )
        model.to(device)
        model.eval()
        self._loaded = (processor, tokenizer, model, device)
        return self._loaded

    def parse(self, page_png: bytes) -> DonutResult:
        import io

        processor, tokenizer, model, device = self._load()
        import torch
        from PIL import Image

        start = self.timer()
        image = Image.open(io.BytesIO(page_png)).convert("RGB")
        pixel_values = processor(image, return_tensors="pt").pixel_values.to(device)
        prompt = tokenizer(TASK_TOKEN, add_special_tokens=False, return_tensors="pt").input_ids
        with torch.no_grad():
            output = model.generate(
                pixel_values,
                decoder_input_ids=prompt.to(device),
                max_length=self.max_length,
                num_beams=1,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                return_dict_in_generate=True,
                output_scores=True,
            )
        generated = output.sequences[0, prompt.shape[1] :].tolist()
        probabilities = [
            float(torch.softmax(score[0], dim=-1)[token].item())
            for score, token in zip(output.scores, generated, strict=False)
        ]
        tokens = tokenizer.convert_ids_to_tokens(generated[: len(probabilities)])
        sequence = tokenizer.decode(generated, skip_special_tokens=False)
        return DonutResult(
            fields=parse_donut_sequence(sequence),
            raw_sequence=sequence,
            field_confidence=field_confidences([t.replace("▁", "") for t in tokens], probabilities),
            model_id=self.model_id,
            model_sha256=self.expected_sha256,
            duration_ms=int((self.timer() - start) * 1000),
            device=device,
        )
