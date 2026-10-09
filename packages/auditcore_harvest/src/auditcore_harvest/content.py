"""Binary payload of a record (for example a PDF) with its media type.

The bytes travel natively inside :class:`~auditcore_harvest.model.HarvestRecord`;
only the JSON view (``to_dict``) encodes them as Base64.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryContent:
    """Raw document bytes and their declared media type (``application/pdf``, ...)."""

    data: bytes
    media_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes):
            raise TypeError("BinaryContent.data muss bytes sein.")
        if not self.media_type or "/" not in self.media_type:
            raise ValueError("BinaryContent braucht einen Medientyp der Form 'typ/untertyp'.")

    @property
    def size(self) -> int:
        """Number of bytes."""
        return len(self.data)

    @property
    def sha256(self) -> str:
        """Hex SHA-256 over the bytes; part of the record's content hash."""
        return hashlib.sha256(self.data).hexdigest()

    def to_dict(self, *, include_data: bool = True) -> dict[str, str | int]:
        """JSON view; ``include_data=False`` keeps only media type, size and hash."""
        view: dict[str, str | int] = {
            "media_type": self.media_type,
            "size": self.size,
            "sha256": self.sha256,
        }
        if include_data:
            view["data_b64"] = base64.b64encode(self.data).decode("ascii")
        return view

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> BinaryContent:
        """Inverse of :meth:`to_dict` (with data); a hash mismatch is a ``ValueError``."""
        try:
            raw = base64.b64decode(str(data["data_b64"]), validate=True)
        except (KeyError, binascii.Error) as exc:
            raise ValueError("Binärinhalt ohne gültiges 'data_b64'.") from exc
        content = cls(raw, str(data.get("media_type", "application/octet-stream")))
        expected = data.get("sha256")
        if expected is not None and expected != content.sha256:
            raise ValueError("Binärinhalt passt nicht zur angegebenen Prüfsumme.")
        return content
