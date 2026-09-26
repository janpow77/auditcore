"""SHA-256-Hashing für die Pipeline (aus flowinvoice ``app/pipeline/hashing.py``).

``compute_chain_hash`` des Originals hasht die Verkettung der Stufen-Hashes;
jeder Stufen-Hash ist unabhängig vom vorherigen (keine echte Hash-Kette,
PL-L02). ``linked_chain`` bietet ergänzend eine verkettete Variante.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from auditcore_common.hashing import canonical_sha256, sha256_file, sha256_text


class HashingService:
    ALGORITHM = "sha256"

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_string(text: str, encoding: str = "utf-8") -> str:
        return sha256_text(text, encoding)

    @staticmethod
    def hash_json(obj: dict[str, Any] | list[Any]) -> str:
        return canonical_sha256(obj, ensure_ascii=True, default=str)

    @staticmethod
    def hash_file(file_path: str | Path) -> str:
        return sha256_file(file_path, chunk_size=8192)

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
