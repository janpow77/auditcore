"""Canonical JSON and SHA-256 digests.

The canonical form of the profile fingerprints is ``sort_keys=True``,
``ensure_ascii=False`` and compact separators, encoded as UTF-8. The two
older forms still bound to stored fingerprints are explicit keywords:
``compact=False`` (default separators ``", "``/``": "``) and
``ensure_ascii=True, default=str``.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path

_COMPACT = (",", ":")


def canonical_json(
    value: object,
    *,
    compact: bool = True,
    ensure_ascii: bool = False,
    default: Callable[[object], object] | None = None,
) -> str:
    """``json.dumps`` with sorted keys; compact separators unless ``compact=False``."""
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=ensure_ascii,
        separators=_COMPACT if compact else None,
        default=default,
    )


def canonical_sha256(
    value: object,
    *,
    compact: bool = True,
    ensure_ascii: bool = False,
    default: Callable[[object], object] | None = None,
) -> str:
    """SHA-256 hex digest of :func:`canonical_json` encoded as UTF-8."""
    text = canonical_json(value, compact=compact, ensure_ascii=ensure_ascii, default=default)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_text(text: str, encoding: str = "utf-8") -> str:
    """SHA-256 hex digest of ``text`` in ``encoding``."""
    return hashlib.sha256(text.encode(encoding)).hexdigest()


def sha256_file(path: str | os.PathLike[str], *, chunk_size: int = 1 << 20) -> str:
    """SHA-256 hex digest of a file, read in chunks (the digest is chunk-size independent)."""
    if chunk_size < 1:
        raise ValueError("chunk_size muss positiv sein.")
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()
