"""Canonical JSON, text and file digests against the package copies (differential)."""

from __future__ import annotations

import json
import random
from pathlib import Path

import legacy_reference as legacy
import pytest
from samples import SAMPLES, assert_same_outcome, random_json, random_value, rng

from auditcore_common.hashing import canonical_json, canonical_sha256, sha256_file, sha256_text

COMPACT = {
    "dataprotection.canonical_sha256": legacy.dataprotection_canonical_sha256,
    "entity_matching.fingerprint": legacy.entity_fingerprint,
    "harvest.canonical_hash": legacy.harvest_canonical_hash,
    "funding_sources.fingerprint": legacy.fingerprint,
}


@pytest.mark.parametrize("name", sorted(COMPACT))
def test_compact_canonical_sha256(name: str) -> None:
    old = COMPACT[name]
    r = rng(len(name))
    for _ in range(SAMPLES):
        value = random_json(r)
        assert_same_outcome(lambda: old(value), lambda: canonical_sha256(value))  # type: ignore[arg-type]


def test_documents_profile_form_uses_default_separators() -> None:
    r = rng(3)
    for _ in range(SAMPLES):
        value = {"k": random_json(r), "Ä": random_json(r)}
        assert_same_outcome(
            lambda: legacy.documents_profile_fingerprint(value),
            lambda: canonical_sha256(value, compact=False),
        )


def test_documents_hash_json_form_is_ascii_with_str_default() -> None:
    r = rng(4)
    for _ in range(SAMPLES):
        value = [random_value(r)]
        assert_same_outcome(
            lambda: legacy.documents_hash_json(value),
            lambda: canonical_sha256(value, ensure_ascii=True, default=str),
        )


def test_mixed_keys_fail_identically() -> None:
    value = {1: "a", "b": 2}
    assert_same_outcome(
        lambda: legacy.entity_fingerprint(value),  # type: ignore[arg-type]
        lambda: canonical_sha256(value),
    )
    assert canonical_json({"b": 1, "a": [1, 2]}) == '{"a":[1,2],"b":1}'


@pytest.mark.parametrize("encoding", ["utf-8", "latin-1", "utf-16", "ascii"])
def test_sha256_text(encoding: str) -> None:
    r = rng(5)
    for _ in range(500):
        text = "".join(r.choice("aÄß€日\x00 ") for _ in range(r.randint(0, 20)))
        assert_same_outcome(
            lambda: legacy.documents_hash_string(text, encoding),
            lambda: sha256_text(text, encoding),
        )


SIZES = [0, 1, 8191, 8192, 8193, 65535, 65536, 65537, (1 << 20) - 1, 1 << 20, (1 << 20) + 1]


def test_sha256_file_equals_every_copy(tmp_path: Path) -> None:
    r = random.Random(6)
    sizes = SIZES + [r.randint(0, 3 << 20) for _ in range(6)]
    copies = (
        legacy.documents_sha256_file,
        legacy.invoicesynth_sha256_file,
        legacy.invoicesynth_sha256,
        lambda p: legacy.documents_hash_file(str(p)),
    )
    for index, size in enumerate(sizes):
        path = tmp_path / f"f{index}.bin"
        path.write_bytes(r.randbytes(size))
        expected = legacy.documents_sha256_file(path)
        for copy in copies:
            assert copy(path) == expected
        assert sha256_file(path) == expected
        assert sha256_file(str(path), chunk_size=7) == expected


def test_sha256_file_errors_match(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    assert_same_outcome(
        lambda: legacy.documents_sha256_file(missing), lambda: sha256_file(missing)
    )
    assert_same_outcome(
        lambda: legacy.documents_sha256_file(tmp_path), lambda: sha256_file(tmp_path)
    )
    with pytest.raises(ValueError):
        sha256_file(missing, chunk_size=0)


def test_price_sources_form_is_default_separators_and_ascii() -> None:
    r = rng(8)
    for _ in range(SAMPLES):
        body = json.dumps(random_json(r)).encode()
        if r.random() < 0.1:
            body = body[:-1]
        assert_same_outcome(
            lambda: legacy.price_sources_canonical_json_bytes(body),
            lambda: canonical_json(json.loads(body), compact=False, ensure_ascii=True).encode(),
        )
