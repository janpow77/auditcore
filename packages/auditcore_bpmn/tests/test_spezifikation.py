"""Invarianten aus docs/spezifikation.md als Eigenschaftstests (Hypothesis).

Die Diagramme entstehen aus synthetischen Bausteinen (``helpers``); kein Netz.
"""

from __future__ import annotations

from datetime import date

import pytest
from helpers import doc, ext, flow
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_bpmn import (
    LegalBasis,
    UnsafeXmlError,
    XmlTooLargeError,
    compare,
    find_citations,
    neutralize,
    parse_bpmn,
    parse_citation,
    parse_xml,
    serialize,
    set_extensions,
    validate,
)
from auditcore_bpmn.extensions import Extensions

EXAMPLES = settings(max_examples=60, deadline=None)
NAMES = st.text(
    st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"), whitelist_characters="-.,&<>\"'äöüß"),
    min_size=1,
    max_size=20,
)
ACT = st.sampled_from(["Verordnung (EU) 2021/1060", "Verordnung (EU) Nr. 1303/2013", "Verordnung (EU) 2018/1046"])
DELEGATED = "Delegierte Verordnung (EU) Nr. 480/2014"
NUMBERS = st.integers(1, 200).map(str)


@st.composite
def diagrams(draw: st.DrawFn) -> str:
    """Start → n Aufgaben (mit Namen, optional Rechtsgrundlage/Dokumentation) → Ende."""
    count = draw(st.integers(0, 6))
    names = draw(st.lists(NAMES, min_size=count, max_size=count))
    parts = ['<bpmn:startEvent id="S" name="Start"/>', '<bpmn:endEvent id="E" name="Ende"/>']
    for index, name in enumerate(names, start=1):
        escaped = name.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
        inner = ""
        if draw(st.booleans()):
            article, paragraph = draw(NUMBERS), draw(NUMBERS)
            inner = ext(
                f'<flowaudit:rechtsgrundlage norm="Verordnung (EU) 2021/1060" artikel="{article}" absatz="{paragraph}"/>'
            )
        if draw(st.booleans()):
            inner += f"<bpmn:documentation>{escaped}</bpmn:documentation>"
        parts.append(f'<bpmn:task id="T{index}" name="{escaped}">{inner}</bpmn:task>')
    ids = ["S", *(f"T{i}" for i in range(1, count + 1)), "E"]
    parts += [flow(f"F{i}", a, b) for i, (a, b) in enumerate(zip(ids, ids[1:], strict=False), start=1)]
    return doc("".join(parts))


@EXAMPLES
@given(diagrams())
def test_i1_serialize_is_a_fixed_point_after_one_round_trip(xml: str) -> None:
    """I1: Lesen–Schreiben–Lesen ist stabil: zweiter Rundlauf bytegleich, Elementmodell gleich."""
    once = serialize(parse_xml(xml))
    assert serialize(parse_xml(once)) == once
    before, after = parse_bpmn(xml), parse_bpmn(once)
    assert {k: (e.type, e.name) for k, e in before.elements.items()} == {
        k: (e.type, e.name) for k, e in after.elements.items()
    }


@EXAMPLES
@given(diagrams())
def test_i2_comparison_with_itself_has_no_differences(xml: str) -> None:
    """I2: Vergleich eines Diagramms mit sich selbst: nur „unveraendert“."""
    result = compare(xml, xml)
    assert result.unchanged
    assert {change.kind for change in result.changes} <= {"unveraendert"}


@EXAMPLES
@given(diagrams(), diagrams())
def test_i3_comparison_is_mirror_symmetric(old: str, new: str) -> None:
    """I3: Hinzugefügt (alt→neu) entspricht Entfallen (neu→alt) und umgekehrt."""
    forward, backward = compare(old, new), compare(new, old)
    assert len(forward.of_kind("hinzugefuegt")) == len(backward.of_kind("entfallen"))
    assert len(forward.of_kind("entfallen")) == len(backward.of_kind("hinzugefuegt"))
    assert len(forward.of_kind("geaendert")) == len(backward.of_kind("geaendert"))


@EXAMPLES
@given(diagrams(), st.from_regex(r"[a-z0-9._+-]{1,10}@[a-z0-9-]{1,10}(\.[a-z]{2,5}){1,2}", fullmatch=True))
def test_i4_neutralization_is_idempotent_and_removes_mail_addresses(xml: str, mail: str) -> None:
    """I4: Neutralisieren entfernt E-Mail-Adressen (Form ``lokal@domain.tld``); zweites Neutralisieren ändert nichts."""
    xml = xml.replace('name="Ende"', f'name="Ende {mail}"')
    once = neutralize(xml).xml
    assert mail not in once
    assert neutralize(once).xml == once


@EXAMPLES
@given(diagrams())
def test_i5_validation_is_deterministic_and_valid_means_no_errors(xml: str) -> None:
    """I5: gleiche Eingabe und Stichtag → gleicher Bericht; gültig genau ohne Fehler-Treffer."""
    first = validate(xml, reference_date=date(2026, 9, 25))
    second = validate(parse_bpmn(xml), reference_date=date(2026, 9, 25))
    assert first.to_dict() == second.to_dict()
    assert first.is_valid == (not first.errors)
    assert all(issue.rule_id.startswith("BPMN-") for issue in first.issues)


@EXAMPLES
@given(diagrams(), st.sampled_from(["<!DOCTYPE x>", '<!DOCTYPE x [<!ENTITY e "a">]>']))
def test_i6_hardened_parser_rejects_dtd_and_oversize(xml: str, doctype: str) -> None:
    """I6: DTD/Entitäten werden abgewiesen; Dokumente über ``max_size`` ebenso."""
    head, _, rest = xml.partition("\n")
    with pytest.raises(UnsafeXmlError):
        parse_xml(f"{head}\n{doctype}{rest}")
    with pytest.raises(XmlTooLargeError):
        parse_xml(xml, max_size=len(xml) - 1)


@EXAMPLES
@given(ACT, NUMBERS, st.one_of(st.none(), NUMBERS), st.one_of(st.none(), st.sampled_from("abcd")))
def test_i7_structured_citation_round_trip(act: str, article: str, paragraph: str | None, point: str | None) -> None:
    """I7: ausgeschriebene Normalform einer EU-Verordnung wird wieder gleich strukturiert gelesen."""
    basis = LegalBasis(act=act, article=article, paragraph=paragraph, point=point)
    parsed = parse_citation(basis.citation())
    assert (parsed.article, parsed.paragraph, parsed.point) == (article, paragraph, point)
    assert parsed.citation() == basis.citation()
    assert basis.normalized().normalized() == basis.normalized()


@pytest.mark.xfail(
    strict=True,
    reason="Befund B1 (docs/spezifikation.md): „der Delegierten Verordnung“ wird als Norm "
    "„Delegierten Verordnung …“ gelesen; die Normalform verliert dann den Artikel „der“.",
)
@settings(max_examples=5, deadline=None)
@given(NUMBERS)
def test_i7_befund_b1_declined_delegated_act(article: str) -> None:
    """I7 (Befund B1): der Rundlauf gilt noch nicht für gebeugte Normnamen wie „der Delegierten Verordnung“."""
    basis = LegalBasis(act=DELEGATED, article=article)
    assert parse_citation(basis.citation()).citation() == basis.citation()


@EXAMPLES
@given(st.lists(st.tuples(ACT, NUMBERS), max_size=4), st.text(max_size=30))
def test_i8_found_citations_do_not_overlap(citations: list[tuple[str, str]], noise: str) -> None:
    """I8: Treffer von ``find_citations`` sind nach Position sortiert und überlappungsfrei."""
    text = noise.join(LegalBasis(act=a, article=n).citation() for a, n in citations)
    hits = find_citations(text)
    assert all(a.end <= b.start for a, b in zip(hits, hits[1:], strict=False))
    assert all(text[hit.start : hit.end] == hit.text for hit in hits)


@EXAMPLES
@given(diagrams(), ACT, NUMBERS)
def test_i9_writing_extensions_is_idempotent(xml: str, act: str, article: str) -> None:
    """I9: dieselben Angaben zweimal schreiben ergibt dasselbe Dokument wie einmal."""
    extensions = Extensions(legal_bases=(LegalBasis(act=act, article=article),))
    once = set_extensions(xml, "S", extensions)
    assert set_extensions(once, "S", extensions) == once
    written = parse_bpmn(once).elements["S"].extensions.legal_bases
    assert [(b.article, b.text) for b in written] == [(article, LegalBasis(act=act, article=article).citation())]
