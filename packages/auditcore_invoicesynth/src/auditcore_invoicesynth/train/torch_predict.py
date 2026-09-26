"""Donut-Inferenz für die Bewertung (Extra ``train``; torch/transformers nur verzögert)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

Predictor = Callable[[Path], str]


def donut_predictor(model_dir: Path, *, prompt: str, max_length: int, device: str) -> Predictor:
    """Greedy-Dekodierung eines lokalen Donut-Modells (Extra ``train``)."""
    from PIL import Image

    from auditcore_invoicesynth.train.torch_backend import _modules

    torch, transformers = _modules()

    local = str(model_dir)
    # B615 trifft nicht zu: nur lokale Verzeichnisse, local_files_only=True.
    processor = transformers.DonutProcessor.from_pretrained(  # nosec B615
        local, local_files_only=True
    )
    model = transformers.VisionEncoderDecoderModel.from_pretrained(  # nosec B615
        local, local_files_only=True
    )
    chosen = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
    model.to(chosen).eval()
    tokenizer = processor.tokenizer
    prompt_ids = tokenizer(prompt, add_special_tokens=False, return_tensors="pt").input_ids

    def predict(path: Path) -> str:
        with Image.open(path) as image:
            pixels = processor(image.convert("RGB"), return_tensors="pt").pixel_values
        with torch.inference_mode():
            output = model.generate(
                pixels.to(chosen),
                decoder_input_ids=prompt_ids.to(chosen),
                max_length=max_length,
                num_beams=1,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                bad_words_ids=[[tokenizer.unk_token_id]],
            )
        return str(tokenizer.batch_decode(output, skip_special_tokens=False)[0])

    return predict
