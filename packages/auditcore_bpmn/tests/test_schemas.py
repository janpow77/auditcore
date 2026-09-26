"""XSD der Erweiterung, JSON-Schemata und ihre Aktualität."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from helpers import FIXTURES, STICHTAG

from auditcore_bpmn import validate
from auditcore_bpmn.namespaces import FLOWAUDIT_NAMESPACE
from auditcore_bpmn.profiles import available_profiles

ROOT = Path(__file__).parents[1]
SCHEMAS = ROOT / "src/auditcore_bpmn/schemas"


def _flowaudit_top_elements(xml: bytes) -> list:  # type: ignore[type-arg]
    etree = pytest.importorskip("lxml.etree")
    root = etree.fromstring(xml, etree.XMLParser(resolve_entities=False, no_network=True))
    return [
        node
        for node in root.iter()
        if isinstance(node.tag, str)
        and node.tag.startswith("{" + FLOWAUDIT_NAMESPACE)
        and not str(node.getparent().tag).startswith("{" + FLOWAUDIT_NAMESPACE)
    ]


def _xsd():  # type: ignore[no-untyped-def]
    etree = pytest.importorskip("lxml.etree")
    return etree.XMLSchema(etree.parse(str(SCHEMAS / "flowaudit-1.1.xsd")))


@pytest.mark.parametrize(
    "path",
    [*sorted((FIXTURES / "synthetic").glob("*.bpmn")), *sorted((ROOT / "src/auditcore_bpmn/templates").glob("*.bpmn"))],
    ids=lambda p: p.name,
)
def test_flowaudit_elements_conform_to_xsd(path: Path) -> None:
    schema = _xsd()
    etree = pytest.importorskip("lxml.etree")
    for element in _flowaudit_top_elements(path.read_bytes()):
        schema.assertValid(etree.ElementTree(element))


def test_xsd_rejects_invalid_values() -> None:
    schema = _xsd()
    etree = pytest.importorskip("lxml.etree")
    bad = etree.fromstring(f'<fa:pruefbezug xmlns:fa="{FLOWAUDIT_NAMESPACE}" ka="null"/>')
    assert not schema.validate(etree.ElementTree(bad))
    bad_info = etree.fromstring(f'<fa:diagrammInfo xmlns:fa="{FLOWAUDIT_NAMESPACE}" status="fertig"/>')
    assert not schema.validate(etree.ElementTree(bad_info))


def test_json_schemas_are_current_and_validate_outputs() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    sys.path.insert(0, str(ROOT / "tools"))
    from build_json_schemas import SCHEMAS as BUILDERS
    from build_json_schemas import render

    for name in BUILDERS:
        assert (SCHEMAS / name).read_text(encoding="utf-8") == render(name), (
            f"{name} veraltet: tools/build_json_schemas.py ausführen"
        )
    report = validate(
        (FIXTURES / "synthetic/antragsstrecke_altbestand.bpmn").read_text(encoding="utf-8"), reference_date=STICHTAG
    )
    jsonschema.validate(
        report.to_dict(), json.loads((SCHEMAS / "validation-report-1.schema.json").read_text(encoding="utf-8"))
    )
    profile_schema = json.loads((SCHEMAS / "profile-1.schema.json").read_text(encoding="utf-8"))
    for profile_id, version in available_profiles():
        data = json.loads(
            (ROOT / f"src/auditcore_bpmn/profiles/data/{profile_id}-{version}.json").read_text(encoding="utf-8")
        )
        jsonschema.validate(data, profile_schema)


def test_rules_document_is_current() -> None:
    sys.path.insert(0, str(ROOT / "tools"))
    from document_rules import render

    assert (ROOT / "docs/rules.md").read_text(encoding="utf-8") == render(), "tools/document_rules.py ausführen"
