"""Post-process internally generated SpreadsheetML only.

The Open XML SDK Font schema orders properties differently from openpyxl, and
openpyxl writes floats with 16 significant digits (``%.16g``), which loses the
last digit of some doubles (``0.1 + 0.2`` → ``0.3``) and turns the largest
finite double into infinity. No caller-provided Office archives are accepted
by the public API.
"""

import re
from collections.abc import Mapping
from io import BytesIO
from xml.etree.ElementTree import tostring
from zipfile import ZipFile

from defusedxml.ElementTree import fromstring

_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_FONT_ORDER = (
    "b",
    "i",
    "strike",
    "condense",
    "extend",
    "outline",
    "shadow",
    "u",
    "vertAlign",
    "sz",
    "color",
    "name",
    "family",
    "charset",
    "scheme",
)


def normalize_font_sequence(payload: bytes) -> bytes:
    """Preserve generated workbook contents while applying the schema font order."""
    output = BytesIO()
    with ZipFile(BytesIO(payload)) as source, ZipFile(output, "w") as target:
        for member in source.infolist():
            content = source.read(member)
            if member.filename == "xl/styles.xml":
                root = fromstring(content, forbid_dtd=True)
                for font in root.findall(f"{{{_NAMESPACE}}}fonts/{{{_NAMESPACE}}}font"):
                    children = list(font)
                    order = {f"{{{_NAMESPACE}}}{name}": i for i, name in enumerate(_FONT_ORDER)}
                    if any(child.tag not in order for child in children):
                        raise ValueError("Unexpected generated font property")
                    font[:] = sorted(children, key=lambda child: order[child.tag])
                content = tostring(root, encoding="utf-8")
            target.writestr(member, content)
    return output.getvalue()


_NUMERIC_CELL = re.compile(rb'(<c r="([A-Z]+[0-9]+)"[^>]*><v>)([^<]*)(</v>)')


def _replace_values(content: bytes, cells: Mapping[str, str]) -> bytes:
    """One pass over a worksheet; every listed cell must be replaced exactly once."""
    done: set[str] = set()

    def exact(match: re.Match[bytes]) -> bytes:
        ref = match[2].decode("ascii")
        if ref not in cells:
            return match[0]
        done.add(ref)
        return match[1] + cells[ref].encode("ascii") + match[4]

    result = _NUMERIC_CELL.sub(exact, content)
    if done != set(cells):
        raise ValueError("Generated cell not found for exact number")
    return result


def restore_exact_numbers(payload: bytes, exact: Mapping[str, Mapping[str, str]]) -> bytes:
    """Replace the written value of the given numeric cells with their exact text.

    ``exact`` maps a worksheet member (``xl/worksheets/sheet1.xml``) to
    ``{cell reference: repr(float)}``. A listed cell that is not found raises
    instead of leaving a lossy value behind.
    """
    output = BytesIO()
    with ZipFile(BytesIO(payload)) as source, ZipFile(output, "w") as target:
        for member in source.infolist():
            content = source.read(member)
            if member.filename in exact:
                content = _replace_values(content, exact[member.filename])
            target.writestr(member, content)
    return output.getvalue()
