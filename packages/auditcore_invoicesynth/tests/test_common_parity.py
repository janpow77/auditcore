"""Gleichheit alt ↔ neu: Hashes, Steuersatz und Kennungen aus ``auditcore_common``.

Die Kopien unten sind die Implementierungen aus 0.1.2 (wörtlich). Datensatz-,
Konfigurations- und Plan-Hash stehen in Manifesten und Checkpoints; sie dürfen
sich durch die Umstellung nicht ändern.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from auditcore_invoicesynth import fonts
from auditcore_invoicesynth.dataset import dataset_hash, plan_summary
from auditcore_invoicesynth.formats import normalize_identifier, parse_rate
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset
from auditcore_invoicesynth.train import checkpoint, torch_backend
from auditcore_invoicesynth.train.cli import run_id_for
from auditcore_invoicesynth.train.profiles import PROFILES

FAMILIES = ("DejaVu Sans", "DejaVu Serif")


# formats.py :: parse_rate (0.1.2, wörtlich)
def alt_parse_rate(text: str) -> Decimal | None:
    match = re.fullmatch(r"(\d{1,2})(?:[.,](\d))?\s*%?", text.strip())
    if not match:
        return None
    value = Decimal(match[1] + ("." + match[2] if match[2] else ""))
    return value.quantize(Decimal(1)) if value == value.to_integral() else value


# formats.py :: normalize_identifier (0.1.2, wörtlich)
def alt_normalize_identifier(text: str) -> str:
    return "".join(text.split()).upper()


# fonts.py :: sha256_file (0.1.2, wörtlich; 64 KiB-Blöcke)
def alt_fonts_sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


# train/checkpoint.py :: _sha256 = train/torch_backend.py :: sha256_file (0.1.2; 1 MiB)
def alt_checkpoint_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# dataset.py :: _sha256 (0.1.2, wörtlich)
def alt_dataset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# dataset.py :: dataset_hash (0.1.2, wörtlich)
def alt_dataset_hash(files: dict[str, str]) -> str:
    lines = "".join(f"{path}\t{digest}\n" for path, digest in sorted(files.items()))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


RATES = ["19 %", "19%", "19,0 %", "7.5", " 7 ", "0", "05", "100", "19,05", "abc", "", "٣%", "7,5%"]
IDENTIFIERS = ["DE89 3704 0044 0532 0130 00", " atu 1234\t5678 ", "", "ß", "de\u00a0123", "ı"]


@pytest.mark.parametrize("text", RATES)
def test_parse_rate(text: str) -> None:
    assert repr(parse_rate(text)) == repr(alt_parse_rate(text))


@pytest.mark.parametrize("text", IDENTIFIERS)
def test_normalize_identifier(text: str) -> None:
    assert normalize_identifier(text) == alt_normalize_identifier(text)


@pytest.mark.parametrize("size", [0, 1, (1 << 16) - 1, 1 << 16, (1 << 16) + 1, (1 << 20) + 1])
def test_file_digests(tmp_path: Path, size: int) -> None:
    path = tmp_path / "blob.bin"
    path.write_bytes(random.Random(size).randbytes(size))
    expected = alt_fonts_sha256_file(path)
    assert alt_checkpoint_sha256(path) == alt_dataset_sha256(path) == expected
    assert fonts.sha256_file(path) == checkpoint.sha256_file(path) == expected
    assert torch_backend.sha256_file(path) == expected


def test_missing_file_fails_identically(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        fonts.sha256_file(tmp_path / "fehlt")
    with pytest.raises(FileNotFoundError):
        alt_fonts_sha256_file(tmp_path / "fehlt")


def test_dataset_hash() -> None:
    rng = random.Random(7)
    files = {f"train/{i:05d}-ä.png": f"{rng.getrandbits(256):064x}" for i in range(50)}
    assert dataset_hash(files) == alt_dataset_hash(files)
    assert dataset_hash({}) == alt_dataset_hash({})


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_config_hash(name: str) -> None:
    config = PROFILES[name]
    payload = json.dumps(config.to_dict(), sort_keys=True).encode("utf-8")
    assert config.config_hash == hashlib.sha256(payload).hexdigest()
    changed = replace(config, profile="prüfung-ä")
    payload = json.dumps(changed.to_dict(), sort_keys=True).encode("utf-8")
    assert changed.config_hash == hashlib.sha256(payload).hexdigest()


def test_plan_hash() -> None:
    config = SynthConfig(
        counts={"train": 20, "validation": 5, "test_synthetic": 5, "test_layout_holdout": 5}
    )
    specs = plan_dataset(config, FAMILIES)
    old = hashlib.sha256(
        json.dumps([s.to_dict() for s in specs], sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert plan_summary(config, FAMILIES)["plan_sha256"] == old


def test_run_id() -> None:
    old = hashlib.sha256(b"abc:def").hexdigest()[:16]
    assert run_id_for("abc", "def") == old
