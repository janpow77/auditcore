"""Pictures for templates (coats of arms, logos): PNG or JPEG as bytes, never paths or URLs.

The format and pixel size are read from the file header with the standard
library; anything else is rejected before it reaches a renderer. Images come
from the caller (:class:`RenderOptions`, :class:`DesignProfile`) or as base64
text in the template data – the library never opens files or the network.
"""

from __future__ import annotations

import base64
import binascii
import re
import struct
from dataclasses import dataclass, field

from .errors import TemplateError

#: Upper bound for one picture.
MAX_IMAGE_BYTES = 10 * 1024 * 1024
_NAME = re.compile(r"[a-z][a-z0-9_-]{0,63}")
_PNG = b"\x89PNG\r\n\x1a\n"
_DATA_URI = re.compile(r"data:image/(png|jpeg);base64,", re.IGNORECASE)
#: JPEG start-of-frame markers carrying the picture size (not DHT, JPG, DAC).
_SOF = frozenset(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    position = 2
    while position + 9 <= len(data):
        if data[position] != 0xFF:
            return None
        marker = data[position + 1]
        length = struct.unpack(">H", data[position + 2 : position + 4])[0]
        if marker in _SOF:
            height, width = struct.unpack(">HH", data[position + 5 : position + 9])
            return width, height
        position += 2 + length
    return None


def picture_size(data: bytes) -> tuple[str, int, int]:
    """``("png" | "jpeg", width, height)`` in pixels; :class:`TemplateError` otherwise."""
    size: tuple[int, int] | None = None
    kind = ""
    if data[:8] == _PNG and data[12:16] == b"IHDR" and len(data) >= 24:
        kind, size = "png", struct.unpack(">II", data[16:24])
    elif data[:3] == b"\xff\xd8\xff":
        kind, size = "jpeg", _jpeg_size(data)
    if size is None or not (0 < size[0] <= 20_000 and 0 < size[1] <= 20_000):
        raise TemplateError("Bild: nur PNG oder JPEG mit lesbarer Größe (höchstens 20000 px).")
    return kind, size[0], size[1]


@dataclass(frozen=True)
class ReportImage:
    """Named PNG/JPEG picture; ``kind``, ``width_px`` and ``height_px`` come from the header."""

    name: str
    data: bytes = field(repr=False)
    kind: str = field(init=False)
    width_px: int = field(init=False)
    height_px: int = field(init=False)

    def __post_init__(self) -> None:
        if not _NAME.fullmatch(self.name):
            raise TemplateError(f"Bild {self.name!r}: Name aus a-z, 0-9, _ und -.")
        if not isinstance(self.data, bytes) or len(self.data) > MAX_IMAGE_BYTES:
            raise TemplateError(f"Bild {self.name}: bytes, höchstens {MAX_IMAGE_BYTES} Bytes.")
        kind, width, height = picture_size(self.data)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "width_px", width)
        object.__setattr__(self, "height_px", height)


def decode_picture(value: object, where: str) -> bytes:
    """Bytes of base64 text (optionally a ``data:image/png|jpeg;base64,`` URI)."""
    if not isinstance(value, str) or not value.strip():
        raise TemplateError(f"{where}: Bild als Base64-Text erwartet.")
    text = "".join(_DATA_URI.sub("", value.strip(), count=1).split())
    if len(text) > MAX_IMAGE_BYTES * 4 // 3 + 4:
        raise TemplateError(f"{where}: Bild größer als {MAX_IMAGE_BYTES} Bytes.")
    try:
        return base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TemplateError(f"{where}: kein gültiges Base64.") from exc
