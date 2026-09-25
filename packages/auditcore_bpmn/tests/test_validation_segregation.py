"""Funktionstrennung BPMN-FT… aus dem Profil."""

from __future__ import annotations

from dataclasses import replace

from helpers import doc, ext, flow
from rulecheck import hits

from auditcore_bpmn.profiles import SegregationRule, Selection, load_profile


def _lanes(*lanes: tuple[str, str, str | None, list[str]]) -> str:
    rendered = []
    for lane_id, role, name, nodes in lanes:
        actor = ext(f'<flowaudit:akteur rolle="{role}"' + (f' anzeigename="{name}"' if name else "") + "/>")
        refs = "".join(f"<bpmn:flowNodeRef>{n}</bpmn:flowNodeRef>" for n in nodes)
        rendered.append(f'<bpmn:lane id="{lane_id}" name="{lane_id}">{actor}{refs}</bpmn:lane>')
    return '<bpmn:laneSet id="LS">' + "".join(rendered) + "</bpmn:laneSet>"


def _task(task_id: str, *children: str) -> str:
    return f'<bpmn:task id="{task_id}" name="{task_id}">{ext(*children)}</bpmn:task>'


def _chain(*ids: str) -> str:
    nodes = ["S", *ids, "E"]
    return '<bpmn:startEvent id="S"/><bpmn:endEvent id="E"/>' + "".join(
        flow(f"F{i}", a, b) for i, (a, b) in enumerate(zip(nodes, nodes[1:], strict=False))
    )


def test_ft01_approval_and_payment_in_same_body() -> None:
    tasks = _task("Bewilligen", '<flowaudit:kennzeichen typ="bewilligung"/>') + _task(
        "Zahlen", '<flowaudit:kennzeichen typ="zahlung"/>'
    )
    same = doc(_lanes(("L1", "zgs", None, ["S", "Bewilligen", "Zahlen", "E"])) + tasks + _chain("Bewilligen", "Zahlen"))
    found = hits(same, "BPMN-FT01")
    assert len(found) == 1 and found[0].params["a"] == "Bewilligen" and found[0].severity == "warnung"
    assert "Approval and payment in the same body" in found[0].message("en")
    split = doc(
        _lanes(("L1", "zgs", "Bewilligung", ["S", "Bewilligen"]), ("L2", "zgs", "Kasse", ["Zahlen", "E"]))
        + tasks
        + _chain("Bewilligen", "Zahlen")
    )
    assert not hits(split, "BPMN-FT01")


def test_ft02_ft03_ft04_audit_types_and_roles() -> None:
    verwk = _task("VerwK", '<flowaudit:pruefbezug ka="4" art="verwk"/>')
    audit = _task("Pruefung", '<flowaudit:pruefbezug ka="12" art="systempruefung"/>')
    xml = doc(_lanes(("L1", "pb", None, ["S", "VerwK", "Pruefung", "E"])) + verwk + audit + _chain("VerwK", "Pruefung"))
    assert hits(xml, "BPMN-FT02") and hits(xml, "BPMN-FT03")[0].params["rolle"] == "pb"
    managed = doc(_lanes(("L1", "vb", None, ["S", "Pruefung", "E"])) + audit + _chain("Pruefung"))
    assert hits(managed, "BPMN-FT04")[0].severity == "fehler"


def test_ft05_four_eyes() -> None:
    marked = _task("Pruefen", '<flowaudit:kennzeichen typ="vier_augen"/>')
    alone = doc(
        _lanes(("L1", "vb", None, ["S", "Pruefen", "Zeichnen", "E"]))
        + marked
        + _task("Zeichnen")
        + _chain("Pruefen", "Zeichnen")
    )
    assert hits(alone, "BPMN-FT05")
    second = doc(
        _lanes(("L1", "vb", "A", ["S", "Pruefen"]), ("L2", "vb", "B", ["Zeichnen", "E"]))
        + marked
        + _task("Zeichnen")
        + _chain("Pruefen", "Zeichnen")
    )
    assert not hits(second, "BPMN-FT05")
    by_control = doc(
        _lanes(("L1", "vb", None, ["S", "Pruefen", "E"]))
        + _task(
            "Pruefen",
            '<flowaudit:kennzeichen typ="vier_augen"/>',
            '<flowaudit:kontrolle id="K" verantwortlich="zgs" nachweis="V"/>',
        )
        + _chain("Pruefen")
    )
    assert not hits(by_control, "BPMN-FT05")


def test_rules_are_configurable_per_profile() -> None:
    marked = _task("Pruefen", '<flowaudit:kennzeichen typ="vier_augen"/>')
    xml = doc(_lanes(("L1", "vb", None, ["S", "Pruefen", "E"])) + marked + _chain("Pruefen"))
    without = replace(load_profile(), segregation_rules=())
    assert not hits(xml, "BPMN-FT05", profile=without)
    custom = replace(
        load_profile(),
        segregation_rules=(
            SegregationRule(
                "FT99",
                "excluded_role",
                "hinweis",
                {"de": "Eigene Regel"},
                selection=Selection(markers=("vier_augen",)),
                roles=("vb",),
            ),
            SegregationRule("FT98", "unbekannt", "fehler", {"de": "Unbekannte Art"}),
        ),
    )
    found = hits(xml, "BPMN-FT99", profile=custom)
    assert found[0].severity == "hinweis" and found[0].message().startswith("Eigene Regel:")
