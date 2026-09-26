"""Torch-/Transformers-Anbindung des Donut-Nachtrainings (Extra ``train``).

* Lädt das Startmodell **nur** aus einem lokalen Verzeichnis
  (``local_files_only``); optional wird die SHA-256 der Gewichtsdatei geprüft.
* Ergänzt Task-Token und Feld-Tags des Ziel-JSON ``auditcore_invoice_v1`` und
  vergrößert die Decoder-Embeddings.
* bf16-Autocast auf CUDA, Gradient Checkpointing, AdamW oder 8-bit-AdamW
  (``bitsandbytes``), Cosinus-Scheduler mit Warm-up, Gradient Accumulation.
* DDP, wenn ``WORLD_SIZE`` > 1 (``torchrun``); nur Rang 0 schreibt Checkpoints.
* Zustand je Checkpoint: Modell (safetensors), Tokenizer, Prozessor, Optimierer,
  Scheduler und alle RNG-Zustände.

``build_tiny_base`` erzeugt ein winziges, zufällig initialisiertes Modell mit
Zeichen-Tokenizer für den CPU-Rauchtest (kein Download, kein echtes Training).
"""

from __future__ import annotations

import io
import os
import random
from pathlib import Path
from types import ModuleType
from typing import Any

from auditcore_common.hashing import sha256_file

from auditcore_invoicesynth.dataset import load_split
from auditcore_invoicesynth.schema import TASK_TOKEN, special_tokens, to_sequence
from auditcore_invoicesynth.train.loop import total_steps
from auditcore_invoicesynth.train.profiles import TrainConfig

WEIGHTS = "model.safetensors"
TINY_CHARS = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,:;-/#()%€&+äöüÄÖÜßéè'\"_"
)


class TrainDependencyError(ImportError):
    """Das Extra ``train`` (torch, transformers, sentencepiece, pillow) fehlt."""


def _modules() -> tuple[ModuleType, ModuleType]:
    try:
        import torch
        import transformers
    except ImportError as exc:  # pragma: no cover - abhängig von der Installation
        raise TrainDependencyError("Bitte auditcore_invoicesynth[train] installieren") from exc
    return torch, transformers


def build_tiny_base(target: Path, image_size: tuple[int, int] = (64, 48)) -> Path:
    """Winziges Donut-Modell (Swin + MBart) mit Zeichen-Tokenizer, nur für Rauchtests."""
    torch, transformers = _modules()
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers

    torch.manual_seed(0)
    vocab = {"<pad>": 0, "<s>": 1, "</s>": 2, "<unk>": 3}
    for char in TINY_CHARS:
        vocab.setdefault(char, len(vocab))
    core = Tokenizer(models.WordLevel(vocab=vocab, unk_token="<unk>"))
    core.pre_tokenizer = pre_tokenizers.Split(pattern="", behavior="isolated")
    core.decoder = decoders.Fuse()
    tokenizer = transformers.PreTrainedTokenizerFast(
        tokenizer_object=core,
        bos_token="<s>",
        eos_token="</s>",
        pad_token="<pad>",
        unk_token="<unk>",
    )
    height, width = image_size
    encoder = transformers.DonutSwinConfig(
        image_size=[height, width],
        patch_size=4,
        embed_dim=16,
        depths=[1, 1],
        num_heads=[1, 2],
        window_size=4,
    )
    decoder = transformers.MBartConfig(
        vocab_size=len(tokenizer),
        d_model=32,
        encoder_layers=1,
        decoder_layers=1,
        encoder_attention_heads=2,
        decoder_attention_heads=2,
        decoder_ffn_dim=64,
        encoder_ffn_dim=64,
        max_position_embeddings=128,
        is_decoder=True,
        add_cross_attention=True,
    )
    config = transformers.VisionEncoderDecoderConfig.from_encoder_decoder_configs(encoder, decoder)
    model = transformers.VisionEncoderDecoderModel(config=config)
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.decoder_start_token_id = tokenizer.bos_token_id
    processor = transformers.DonutImageProcessor(
        size={"height": height, "width": width}, do_align_long_axis=False
    )
    target.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(target)
    tokenizer.save_pretrained(target)
    processor.save_pretrained(target)
    return target


class TorchDonutBackend:
    """``TrainBackend`` für ``VisionEncoderDecoderModel`` (Donut)."""

    def __init__(
        self,
        dataset_dir: Path,
        base_model_dir: Path,
        *,
        split: str = "train",
        base_model_sha256: str | None = None,
        device: str = "auto",
    ) -> None:
        self.dataset_dir = Path(dataset_dir)
        self.base_model_dir = Path(base_model_dir)
        self.split = split
        self.base_model_sha256 = base_model_sha256
        self.requested_device = device
        self.world_size = int(os.environ.get("WORLD_SIZE", "1"))
        self.rank = int(os.environ.get("RANK", "0"))
        self.rows = load_split(self.dataset_dir, split)

    # -- Aufbau --------------------------------------------------------------
    def setup(self, config: TrainConfig, samples: int) -> None:
        torch, transformers = _modules()
        self.torch = torch
        self.config = config
        self._verify_base_model()
        if self.world_size > 1 and not torch.distributed.is_initialized():
            torch.distributed.init_process_group(
                backend="nccl" if torch.cuda.is_available() else "gloo"
            )
        local_rank = int(os.environ.get("LOCAL_RANK", "0"))
        self._select_device(torch, local_rank)
        torch.manual_seed(config.seed + self.rank)
        random.seed(config.seed + self.rank)
        model = self._load_model(transformers, config)
        model.to(self.device)
        self.model = model
        self.module = model
        if self.world_size > 1:
            self.model = torch.nn.parallel.DistributedDataParallel(
                model, device_ids=[local_rank] if self.device.startswith("cuda") else None
            )
        self.optimizer = _optimizer(torch, config, self.model.parameters())
        self.scheduler = transformers.get_cosine_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=config.warmup_steps,
            num_training_steps=total_steps(config, samples, self.world_size),
        )

    def _verify_base_model(self) -> None:
        if self.base_model_sha256 is not None:
            actual = sha256_file(self.base_model_dir / WEIGHTS)
            if actual != self.base_model_sha256:
                raise ValueError("SHA-256 des Startmodells weicht ab")

    def _select_device(self, torch: ModuleType, local_rank: int) -> None:
        if self.requested_device == "auto":
            self.device = f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu"
        else:
            self.device = self.requested_device
        if self.device.startswith("cuda"):
            torch.cuda.set_device(self.device)
            torch.cuda.reset_peak_memory_stats()

    def _load_model(self, transformers: ModuleType, config: TrainConfig) -> Any:
        """Tokenizer, Bildprozessor und Modell nur aus dem lokalen Startmodell."""
        local = str(self.base_model_dir)
        # B615 trifft nicht zu: nur lokales Verzeichnis, local_files_only=True.
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(  # nosec B615
            local, local_files_only=True
        )
        self.processor = transformers.DonutImageProcessor.from_pretrained(  # nosec B615
            local, local_files_only=True
        )
        height, width = config.image_size
        self.processor.size = {"height": height, "width": width}
        if hasattr(self.processor, "do_align_long_axis"):
            self.processor.do_align_long_axis = False
        model = transformers.VisionEncoderDecoderModel.from_pretrained(  # nosec B615
            local, local_files_only=True
        )
        added = self.tokenizer.add_tokens(special_tokens(), special_tokens=True)
        if added:
            model.decoder.resize_token_embeddings(len(self.tokenizer))
        model.config.pad_token_id = self.tokenizer.pad_token_id
        model.config.decoder_start_token_id = self.tokenizer.convert_tokens_to_ids(TASK_TOKEN)
        model.config.eos_token_id = self.tokenizer.eos_token_id
        if config.gradient_checkpointing:
            try:
                model.gradient_checkpointing_enable()
            except (ValueError, NotImplementedError, AttributeError):
                model.encoder.gradient_checkpointing_enable()
        return model

    # -- Schritt -------------------------------------------------------------
    def _batch(self, indices: list[int]) -> tuple[Any, Any, Any]:
        from PIL import Image

        images = []
        texts = []
        for index in indices:
            row = self.rows[index]
            with Image.open(self.dataset_dir / self.split / row["file_name"]) as image:
                images.append(image.convert("RGB"))
            texts.append(to_sequence(row["gt_parse"]) + self.tokenizer.eos_token)
        pixel_values = self.processor(images, return_tensors="pt").pixel_values
        encoded = self.tokenizer(
            texts,
            add_special_tokens=False,
            padding=True,
            truncation=True,
            max_length=self.config.max_length,
            return_tensors="pt",
        )
        ids = encoded.input_ids
        labels = ids[:, 1:].clone()
        labels[labels == self.tokenizer.pad_token_id] = -100
        return pixel_values.to(self.device), ids[:, :-1].to(self.device), labels.to(self.device)

    def train_step(self, microbatches: list[list[int]]) -> float:
        torch = self.torch
        mine = microbatches[self.rank :: self.world_size]
        self.model.train()
        total = 0.0
        use_bf16 = self.config.precision == "bf16" and self.device.startswith("cuda")
        for number, batch in enumerate(mine):
            pixel_values, decoder_ids, labels = self._batch(batch)
            last = number == len(mine) - 1
            context = self.model.no_sync() if self.world_size > 1 and not last else _nullcontext()
            with context, torch.autocast("cuda", dtype=torch.bfloat16, enabled=use_bf16):
                output = self.model(
                    pixel_values=pixel_values, decoder_input_ids=decoder_ids, labels=labels
                )
                loss = output.loss / len(mine)
            loss.backward()
            total += float(loss.detach().item())
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
        self.optimizer.step()
        self.scheduler.step()
        self.optimizer.zero_grad(set_to_none=True)
        if self.world_size > 1:
            value = torch.tensor([total], device=self.device)
            torch.distributed.all_reduce(value)
            total = float(value.item()) / self.world_size
        return total

    # -- Zustand -------------------------------------------------------------
    def save(self, directory: Path) -> None:
        torch = self.torch
        self.module.save_pretrained(directory, safe_serialization=True)
        self.tokenizer.save_pretrained(directory)
        self.processor.save_pretrained(directory)
        torch.save(self.optimizer.state_dict(), directory / "optimizer.pt")
        torch.save(self.scheduler.state_dict(), directory / "scheduler.pt")
        rng = {
            "python": random.getstate(),
            "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        }
        buffer = io.BytesIO()
        torch.save(rng, buffer)
        (directory / "rng.pt").write_bytes(buffer.getvalue())

    def load(self, directory: Path) -> None:
        torch, transformers = _modules()
        # Eigener, per Prüfsumme bestätigter Checkpoint; nur lokal (B615 trifft nicht zu).
        restored = transformers.VisionEncoderDecoderModel.from_pretrained(  # nosec B615
            str(directory), local_files_only=True
        )
        self.module.load_state_dict(restored.state_dict())
        self.optimizer.load_state_dict(
            torch.load(directory / "optimizer.pt", map_location=self.device, weights_only=True)
        )
        self.scheduler.load_state_dict(torch.load(directory / "scheduler.pt", weights_only=True))
        rng = torch.load(directory / "rng.pt", weights_only=True)
        random.setstate(rng["python"])
        torch.set_rng_state(rng["torch"])
        if rng.get("cuda") is not None and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(rng["cuda"])

    def vram_peak_gib(self) -> float | None:
        if not self.device.startswith("cuda"):
            return None
        return round(float(self.torch.cuda.max_memory_allocated()) / 2**30, 3)

    def barrier(self) -> None:
        if self.world_size > 1:
            self.torch.distributed.barrier()


class _nullcontext:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> None:
        return None


def _optimizer(torch: ModuleType, config: TrainConfig, parameters: Any) -> Any:
    """AdamW, auf Wunsch 8-bit über bitsandbytes (nur verzögert importiert)."""
    if config.optimizer == "adamw8bit":
        try:
            import bitsandbytes
        except ImportError as exc:
            raise TrainDependencyError("8-bit-AdamW benötigt bitsandbytes") from exc
        return bitsandbytes.optim.AdamW8bit(parameters, lr=config.learning_rate)
    return torch.optim.AdamW(parameters, lr=config.learning_rate)
