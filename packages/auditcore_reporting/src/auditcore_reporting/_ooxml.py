"""Normalize the font sequence in internally generated SpreadsheetML only.

The Open XML SDK Font schema orders properties differently from openpyxl.
No caller-provided Office archives are accepted by the public API.
"""

from io import BytesIO
from xml.etree.ElementTree import tostring
from zipfile import ZipFile

from defusedxml.ElementTree import fromstring

_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_FONT_ORDER = (
    "b", "i", "strike", "condense", "extend", "outline", "shadow", "u", "vertAlign",
    "sz", "color", "name", "family", "charset", "scheme",
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
