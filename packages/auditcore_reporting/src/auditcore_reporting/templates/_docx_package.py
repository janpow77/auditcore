"""Security check of a DOCX/DOTX template package before anything is filled.

Rejected: ZIP bombs and oversized packages, unsafe entry names, encryption,
macros (VBA projects, macro-enabled content types), ActiveX, OLE objects,
``altChunk``/sub-documents/attached templates, external relationships other
than hyperlinks, fields that pull in content (``INCLUDETEXT``, ``DDE`` …) and
any XML with a DTD. Every XML part is parsed with ``defusedxml``.
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass

from ._docx_xml import Part
from .errors import UnsafeDocumentError

MAIN_DOCUMENT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
MAIN_TEMPLATE = "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml"
_CT_NS = "{http://schemas.openxmlformats.org/package/2006/content-types}"
_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_FORBIDDEN_TYPES = ("macroenabled", "vbaproject", "activex", "vbadata", "oleobject")
_FORBIDDEN_RELS = (
    "/attachedtemplate", "/oleobject", "/afchunk", "/subdocument", "/frame", "/control",
    "/vbaproject", "/activexcontrolbinary", "/wordvbadata", "/keymapcustomizations",
)  # fmt: skip
_FORBIDDEN_NAMES = re.compile(
    r"(^|/)(vbaproject\.bin|vbadata\.xml|activex/|customizations\.xml)|^customui/"
    r"|embeddings/.*\.(bin|docm|xlsm|pptm|dotm|xlam|exe|dll|js|vbs)$",
    re.IGNORECASE,
)
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_FORBIDDEN_ELEMENTS = frozenset(
    {
        f"{_W}altChunk",
        f"{_W}control",
        f"{_W}subDoc",
        "{urn:schemas-microsoft-com:office:office}OLEObject",
    }
)
_FORBIDDEN_FIELDS = re.compile(
    r"\b(INCLUDETEXT|INCLUDEPICTURE|INCLUDE|DDE|DDEAUTO|LINK|IMPORT|DATABASE|"
    r"MACROBUTTON|GOTOBUTTON|AUTOTEXT|AUTOTEXTLIST|PRINT)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DocxLimits:
    """Resource limits for a DOCX template and its output."""

    max_input_bytes: int = 20 * 1024 * 1024
    max_entries: int = 1_000
    max_uncompressed_bytes: int = 100 * 1024 * 1024
    max_compression_ratio: int = 100


@dataclass(frozen=True)
class Package:
    """Checked package: entries in source order and the main content type."""

    entries: tuple[tuple[str, bytes], ...]
    template: bool

    def get(self, name: str) -> bytes | None:
        """Entry by name."""
        return next((data for entry, data in self.entries if entry == name), None)


def _check_names(infos: list[zipfile.ZipInfo], limits: DocxLimits) -> None:
    if len(infos) > limits.max_entries:
        raise UnsafeDocumentError(f"Mehr als {limits.max_entries} Einträge im DOCX-Paket.")
    seen: set[str] = set()
    total = 0
    for info in infos:
        name = info.filename
        if name.startswith(("/", "\\")) or ".." in name.split("/") or "\\" in name or ":" in name:
            raise UnsafeDocumentError(f"Unsicherer Eintragsname {name!r}.")
        if name.lower() in seen:
            raise UnsafeDocumentError(f"Doppelter Eintrag {name!r}.")
        seen.add(name.lower())
        if info.flag_bits & 0x1:
            raise UnsafeDocumentError("Verschlüsselte DOCX-Dateien werden nicht verarbeitet.")
        if _FORBIDDEN_NAMES.search(name):
            raise UnsafeDocumentError(f"Makros, ActiveX oder ausführbare Einbettung: {name!r}.")
        ratio = info.file_size / max(info.compress_size, 1)
        if info.file_size > 1024 * 1024 and ratio > limits.max_compression_ratio:
            raise UnsafeDocumentError(f"{name}: verdächtige Kompressionsrate (ZIP-Bombe?).")
        total += info.file_size
    if total > limits.max_uncompressed_bytes:
        raise UnsafeDocumentError("DOCX-Paket entpackt zu groß.")


def _check_content_types(raw: bytes | None) -> bool:
    if raw is None:
        raise UnsafeDocumentError("[Content_Types].xml fehlt – keine DOCX-Datei.")
    root = Part("[Content_Types].xml", raw).root
    types = {
        e.get("PartName", ""): e.get("ContentType", "") for e in root.iter(f"{_CT_NS}Override")
    }
    types.update(
        {e.get("Extension", ""): e.get("ContentType", "") for e in root.iter(f"{_CT_NS}Default")}
    )
    for kind in types.values():
        if any(word in kind.lower() for word in _FORBIDDEN_TYPES):
            raise UnsafeDocumentError(f"Unzulässiger Inhaltstyp {kind!r} (Makros/ActiveX/OLE).")
    main = types.get("/word/document.xml")
    if main not in (MAIN_DOCUMENT, MAIN_TEMPLATE):
        raise UnsafeDocumentError(
            "word/document.xml ist kein Word-Dokument oder keine Word-Vorlage."
        )
    return main == MAIN_TEMPLATE


def _check_relationships(name: str, raw: bytes) -> None:
    for rel in Part(name, raw).root.iter(f"{_REL_NS}Relationship"):
        kind = rel.get("Type", "").lower()
        if kind.endswith(_FORBIDDEN_RELS):
            raise UnsafeDocumentError(f"{name}: unzulässige Beziehung {kind.rsplit('/', 1)[-1]!r}.")
        if rel.get("TargetMode", "").lower() == "external" and not kind.endswith("/hyperlink"):
            raise UnsafeDocumentError(
                f"{name}: externe Quelle {rel.get('Target', '')!r} nicht erlaubt."
            )


def _check_xml(name: str, raw: bytes) -> None:
    root = Part(name, raw).root
    instructions: list[str] = []
    for element in root.iter():
        if element.tag in _FORBIDDEN_ELEMENTS:
            raise UnsafeDocumentError(
                f"{name}: eingebettete Objekte oder Steuerelemente nicht erlaubt."
            )
        if element.tag == f"{_W}instrText":
            instructions.append(element.text or "")
        elif element.tag == f"{_W}fldSimple":
            instructions.append(" " + element.get(f"{_W}instr", ""))
    for text in (*instructions, "".join(instructions)):
        match = _FORBIDDEN_FIELDS.search(text)
        if match:
            raise UnsafeDocumentError(f"{name}: Feld {match.group(1).upper()} lädt fremde Inhalte.")


def read_package(data: bytes, limits: DocxLimits | None = None) -> Package:
    """Checked entries of a DOCX/DOTX; raises :class:`UnsafeDocumentError`."""
    limits = limits or DocxLimits()
    if len(data) > limits.max_input_bytes:
        raise UnsafeDocumentError(f"DOCX-Vorlage größer als {limits.max_input_bytes} Byte.")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        infos = archive.infolist()
        _check_names(infos, limits)
        entries = tuple((info.filename, archive.read(info)) for info in infos if not info.is_dir())
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, NotImplementedError) as exc:
        raise UnsafeDocumentError(f"Keine lesbare DOCX-Datei: {exc}") from exc
    package = Package(entries, False)
    template = _check_content_types(package.get("[Content_Types].xml"))
    if package.get("word/document.xml") is None:
        raise UnsafeDocumentError("word/document.xml fehlt.")
    for name, raw in entries:
        if name.endswith(".rels"):
            _check_relationships(name, raw)
        elif name.endswith(".xml"):
            _check_xml(name, raw)
    return Package(entries, template)
