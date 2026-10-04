"""Per-call render options: document properties such as author, title and creation time.

Nothing is taken from the clock or the environment: a creation time appears
in the output only when the caller passes it, so identical input still gives
identical bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from .errors import TemplateError
from .images import ReportImage
from .values import CONTROL

_MAX_TEXT = 255


def _checked(value: str, name: str) -> str:
    if len(value) > _MAX_TEXT or CONTROL.search(value) or "\n" in value or "\r" in value:
        raise TemplateError(f"Render-Optionen: {name} höchstens {_MAX_TEXT} Zeichen, einzeilig.")
    return value


@dataclass(frozen=True)
class RenderOptions:
    """Document properties written to DOCX core properties, PDF info and HTML meta.

    ``title`` replaces the resolved template title as document property only
    (the visible text is unchanged); ``created`` must carry a time zone and is
    written in UTC (DOCX ``dcterms:created``/``modified``, PDF ``CreationDate``/
    ``ModDate``). ``images`` supply pictures for ``image`` blocks. Empty
    values leave the output exactly as without options.
    """

    author: str = ""
    title: str = ""
    created: datetime | None = None
    #: Pictures for ``image`` blocks; they take precedence over the design profile's.
    images: tuple[ReportImage, ...] = ()

    def __post_init__(self) -> None:
        _checked(self.author, "author")
        _checked(self.title, "title")
        if not all(isinstance(image, ReportImage) for image in self.images):
            raise TemplateError("Render-Optionen: images als ReportImage.")
        if self.created is not None and self.created.utcoffset() is None:
            raise TemplateError("Render-Optionen: created braucht eine Zeitzone.")

    @property
    def created_utc(self) -> datetime | None:
        """``created`` in UTC without microseconds, or ``None``."""
        if self.created is None:
            return None
        return self.created.astimezone(UTC).replace(microsecond=0)

    def document_title(self, resolved: str) -> str:
        """Title property: the option if set, else the resolved template title."""
        return self.title or resolved


DEFAULT_OPTIONS = RenderOptions()
