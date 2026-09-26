"""Paritätstests gegen Nutzerdiagramme – nur lokal, nie im Repository.

``AUDITCORE_BPMN_LOCAL_FIXTURES`` zeigt auf einen Ordner mit ``*.bpmn``/``*.xml``.
Ohne Variable wird übersprungen. Geprüft wird nur, dass alles gelesen,
rundlauftreu geschrieben, geprüft, analysiert, angereichert und
neutralisiert werden kann; Inhalte werden nicht ausgegeben.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from auditcore_bpmn import analyze_bpmn, neutralize, parse_bpmn, serialize, suggest, validate

LOCAL = os.environ.get("AUDITCORE_BPMN_LOCAL_FIXTURES")
FILES = sorted(p for p in Path(LOCAL).glob("*") if p.suffix in (".bpmn", ".xml")) if LOCAL else []


@pytest.mark.skipif(not LOCAL, reason="AUDITCORE_BPMN_LOCAL_FIXTURES nicht gesetzt")
@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_user_diagram_parity(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    document = parse_bpmn(text)
    written = serialize(document.parsed)
    assert ET.canonicalize(written, strip_text=True) == ET.canonicalize(text, strip_text=True)
    assert validate(document).profile
    assert analyze_bpmn(text)["total_tasks"] >= 0
    assert isinstance(suggest(document), list)
    neutral = parse_bpmn(neutralize(document).xml)
    texts = " ".join([*neutral.root.itertext(), *(e.name or "" for e in neutral)])
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", texts)
