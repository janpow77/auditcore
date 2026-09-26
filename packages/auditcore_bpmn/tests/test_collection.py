"""Diagrammsammlung: Ordner, Tags, Reihenfolge, Auszug, Abfragen, Regeln, Freigaben, JSON, Speicher."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from helpers import STICHTAG, doc, ext, fixture_text, flow, linear

from auditcore_bpmn.collection import (
    COLLECTION_SCHEMA,
    DiagramCollection,
    FileStorage,
    collection_from_dict,
    excerpt_from_document,
    sha256_xml,
)
from auditcore_bpmn.errors import CollectionError
from auditcore_bpmn.model import parse_bpmn

VOLL = fixture_text("synthetic/flowaudit_1_1_vollstaendig.bpmn")
TYPEN = fixture_text("synthetic/typen_kollaboration.bpmn")


def _called() -> str:
    body = (
        '<bpmn:startEvent id="S"/><bpmn:endEvent id="E"/>'
        + flow("F1", "S", "E")
        + '<bpmn:intermediateCatchEvent id="Fang"><bpmn:linkEventDefinition name="weiter"/></bpmn:intermediateCatchEvent>'
    )
    return doc(body, process='id="Process_Auszahlung"')


def _collection() -> DiagramCollection:
    collection = DiagramCollection("s1", "Prüfbehörde Beispiel")
    collection.add_folder("verwk", "Verwaltungskontrolle")
    collection.add_folder("verwk-2026", "2026", "verwk")
    collection.add_folder("pruef", "Prüfungen")
    collection.add_tag("s03", "Systemprüfung S03", "#1976d2")
    collection.add_tag("vorlage", "Vorlage")
    collection.add_diagram("voll", VOLL, folder_id="verwk-2026", tags=["s03"])
    collection.add_diagram("typen", TYPEN, folder_id="verwk", tags=["s03", "vorlage"])
    collection.add_diagram("aufgerufen", _called(), name="Auszahlung", folder_id="pruef")
    return collection


def test_folders_tree_order_and_moves() -> None:
    collection = _collection()
    tree = collection.tree()
    assert [node.folder.id for node in tree.children if node.folder] == ["verwk", "pruef"]
    assert [d.id for d in collection.diagrams_in("verwk")] == ["typen", "voll"]
    assert [d.id for d in collection.diagrams_in("verwk", recursive=False)] == ["typen"]
    collection.move_diagram("voll", "verwk", position=0)
    assert [d.id for d in collection.in_folder("verwk")] == ["voll", "typen"]
    collection.set_order("verwk", ["typen", "voll"])
    assert [d.id for d in collection.in_folder("verwk")] == ["typen", "voll"]
    with pytest.raises(CollectionError):
        collection.set_order("verwk", ["typen"])
    collection.move_folder("verwk-2026", "pruef")
    with pytest.raises(CollectionError):
        collection.move_folder("pruef", "verwk-2026")
    with pytest.raises(CollectionError):
        collection.remove_folder("pruef")
    collection.remove_folder("verwk-2026")
    assert "verwk-2026" not in collection.folders


@pytest.mark.parametrize(
    "action",
    [
        lambda c: c.add_folder("verwk", "doppelt"),
        lambda c: c.add_folder("neu", "x", "fehlt"),
        lambda c: c.add_folder("../ausbruch", "x"),
        lambda c: c.add_diagram("voll"),
        lambda c: c.add_diagram("neu", folder_id="fehlt"),
        lambda c: c.add_diagram("neu", tags=["fehlt"]),
        lambda c: c.set_tags("voll", ["fehlt"]),
        lambda c: c.move_diagram("voll", "fehlt"),
        lambda c: c.entry("fehlt"),
        lambda c: c.move_folder("fehlt", None),
    ],
)
def test_invalid_changes_are_rejected(action) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(CollectionError):
        action(_collection())


def test_excerpt_and_key_lookup() -> None:
    excerpt = excerpt_from_document(parse_bpmn(VOLL))
    assert excerpt.activities == 2 and excerpt.activities_with_legal_basis == 2
    assert excerpt.keys["ka"]["4"] == ["Pruefen", "Collaboration_V"]
    collection = _collection()
    assert collection.elements_by_key("prueffeld", "3.21") == [("voll", "Pruefen")]
    assert collection.elements_by_key("feststellung_ref", "T01 F1") == [("voll", "Pruefen")]
    assert collection.elements_by_key("register", "A1") == [("voll", "Collaboration_V")]
    assert collection.elements_by_key("rolle", "fb") == [("typen", "Pool_Stelle"), ("typen", "Lane_Sach")]
    assert collection.elements_by_key("ka", " 4 ") == [("voll", "Pruefen"), ("voll", "Collaboration_V")]
    with pytest.raises(CollectionError):
        collection.elements_by_key("datenbank_id", "1")


def test_search_and_overview() -> None:
    collection = _collection()
    assert [d.id for d in collection.search("verwk")] == ["voll"]
    assert [d.id for d in collection.search(status="in_pruefung")] == ["typen"]
    assert [d.id for d in collection.search(tag="vorlage")] == ["typen"]
    overview = collection.overview("verwk", reference_date=date(2028, 1, 1))
    assert overview.count == 2 and overview.status_distribution == {"freigegeben": 1, "in_pruefung": 1}
    assert overview.expired == ("typen", "voll") and overview.key_requirement_coverage == {4: ("voll",)}
    assert overview.legal_basis_coverage is not None and 0 < overview.legal_basis_coverage < 1
    whole = collection.overview(reference_date=STICHTAG)
    assert whole.count == 3 and whole.status_distribution["ohne_status"] == 1
    assert collection.overview(tag_id="s03").diagrams == ("voll", "typen")
    assert collection.overview("pruef").legal_basis_coverage is None
    assert json.loads(json.dumps(whole.to_dict()))["key_requirement_coverage"] == {"4": ["voll"]}


def test_references_between_diagrams_and_rules() -> None:
    collection = _collection()
    references = {(r.kind, r.key): r for r in collection.references()}
    assert references[("aufruf", "Process_Auszahlung")].target_diagram == "aufgerufen"
    assert collection.validate() == []
    collection.remove_diagram("aufgerufen")
    rule_ids = {i.rule_id for i in collection.validate()}
    assert rule_ids == {"BPMN-K001"}
    thrower = doc(
        '<bpmn:startEvent id="S"/><bpmn:intermediateThrowEvent id="W"><bpmn:linkEventDefinition name="nirgends"/>'
        "</bpmn:intermediateThrowEvent>" + flow("F", "S", "W"),
        process='id="P_Link"',
    )
    collection.add_diagram("link", thrower)
    found = [i for i in collection.validate() if i.rule_id == "BPMN-K002"]
    assert found[0].diagram_id == "link" and found[0].params["link"] == "nirgends"


def test_collection_rules_k003_k005_k007() -> None:
    collection = _collection()
    collection.add_diagram("kopie", VOLL)
    ist = VOLL.replace('variante="soll"', 'variante="ist" bezugDiagramm="gibt-es-nicht"')
    collection.add_diagram("ist", ist)
    collection.diagrams["kopie"].tags.append("geloescht")
    rule_ids = sorted(i.rule_id for i in collection.validate())
    assert rule_ids == ["BPMN-K003", "BPMN-K005", "BPMN-K007"]
    assert collection.target_actual_pairs() == [("ist", "gibt-es-nicht")]


def test_folder_cycle_detected_on_load_and_in_rules() -> None:
    collection = _collection()
    collection.folders["verwk"].parent_id = "verwk-2026"
    assert any(i.rule_id == "BPMN-K004" for i in collection.validate())
    with pytest.raises(CollectionError, match="Zyklus"):
        collection_from_dict(collection.to_dict())


def test_approvals_are_immutable() -> None:
    collection = _collection()
    approval = collection.approve("voll", VOLL, "1.2", cutoff_date="2026-06-30", approved_by="Leitung")
    assert approval.sha256 == sha256_xml(VOLL) and collection.approve("voll", VOLL, "1.2") == approval
    with pytest.raises(CollectionError, match="neue Version"):
        collection.approve("voll", VOLL + " ", "1.2")
    assert collection.check_approval("voll", VOLL) is None
    changed = collection.check_approval("voll", VOLL.replace("1.2", "1.3"), "1.2")
    assert changed is not None and changed.rule_id == "BPMN-K008" and changed.diagram_id == "voll"
    with pytest.raises(CollectionError):
        collection.check_approval("typen", TYPEN)


def test_json_roundtrip_and_schema() -> None:
    collection = _collection()
    collection.approve("voll", VOLL, "1")
    data = collection.to_dict()
    assert data["schema"] == COLLECTION_SCHEMA
    again = DiagramCollection.from_json(collection.to_json())
    assert again.to_dict() == data and again.diagrams["voll"].info == collection.diagrams["voll"].info
    jsonschema = pytest.importorskip("jsonschema")
    schema_path = Path(__file__).parents[1] / "src/auditcore_bpmn/schemas/diagram-collection-1.schema.json"
    jsonschema.validate(data, json.loads(schema_path.read_text(encoding="utf-8")))
    with pytest.raises(CollectionError):
        DiagramCollection.from_dict({"schema": "anders"})
    with pytest.raises(CollectionError):
        DiagramCollection.from_dict({"schema": COLLECTION_SCHEMA, "folders": [{"name": "ohne id"}]})


def test_file_storage(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path)
    assert storage.load_collection() is None
    collection = _collection()
    storage.save_collection(collection)
    storage.save_diagram("voll", VOLL)
    assert storage.load_collection().to_dict() == collection.to_dict()  # type: ignore[union-attr]
    assert storage.load_diagram("voll") == VOLL and storage.diagram_ids() == ["voll"]
    storage.save_approved("voll", "1", VOLL)
    storage.save_approved("voll", "1", VOLL)
    with pytest.raises(CollectionError, match="unveränderlich"):
        storage.save_approved("voll", "1", VOLL + "x")
    assert storage.load_approved("voll", "1") == VOLL
    storage.delete_diagram("voll")
    with pytest.raises(CollectionError):
        storage.load_diagram("voll")
    with pytest.raises(CollectionError):
        storage.load_approved("voll", "2")
    with pytest.raises(CollectionError):
        storage.save_diagram("../raus", VOLL)
    assert not list(tmp_path.glob("**/.tmp-*"))


def test_refresh_takes_title_and_ext_keys() -> None:
    collection = DiagramCollection()
    entry = collection.add_diagram("d1", doc(ext('<flowaudit:diagrammInfo titel="Titel aus XML"/>') + linear("T1")))
    assert entry.name == "Titel aus XML" and entry.title == "Titel aus XML" and entry.status is None
