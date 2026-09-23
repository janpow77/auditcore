"""SHA-256-Hashing für die Pipeline (aus flowinvoice ``app/pipeline/hashing.py``).

``compute_chain_hash`` des Originals hasht die Verkettung der Stufen-Hashes;
jeder Stufen-Hash ist unabhängig vom vorherigen (keine echte Hash-Kette,
PL-L02). ``linked_chain`` bietet ergänzend eine verkettete Variante.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class HashingService:
    ALGORITHM = "sha256"

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_string(text: str, encoding: str = "utf-8") -> str:
        return hashlib.sha256(text.encode(encoding)).hexdigest()

    @staticmethod
    def hash_json(obj: dict[str, Any] | list[Any]) -> str:
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_file(file_path: str | Path) -> str:
        digest = hashlib.sha256()
        with Path(file_path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def extend_chain(chain: list[str], new_hash: str) -> list[str]:
        chain.append(new_hash)
        return chain

    @staticmethod
    def compute_chain_hash(chain: list[str]) -> str:
        if not chain:
            return hashlib.sha256(b"").hexdigest()
        return hashlib.sha256("".join(chain).encode("utf-8")).hexdigest()

    @staticmethod
    def verify_chain(chain: list[str], expected_hash: str) -> bool:
        if not chain:
            return False
        return HashingService.compute_chain_hash(chain) == expected_hash

    @staticmethod
    def verify_bytes(data: bytes, expected_hash: str) -> bool:
        return HashingService.hash_bytes(data) == expected_hash

    @staticmethod
    def short_hash(full_hash: str, length: int = 8) -> str:
        return full_hash[:length] if len(full_hash) >= length else full_hash

    @staticmethod
    def linked_chain(stage_hashes: list[str], seed: str = "") -> list[str]:
        """Verkettete Kette: h_i = SHA-256(h_{i-1} || stage_hash_i) (Ergänzung, PL-C05)."""
        chain: list[str] = []
        previous = seed
        for stage_hash in stage_hashes:
            previous = hashlib.sha256((previous + stage_hash).encode("utf-8")).hexdigest()
            chain.append(previous)
        return chain
