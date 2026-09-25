"""Normzitate in Freitext und syntaktische Auflösung von EU-Rechtsakten."""

from __future__ import annotations

import pytest

from auditcore_bpmn.citations import EuActResolver, enrich, eu_act, find_citations, parse_citation
from auditcore_bpmn.extensions import LegalBasis

TEXT = (
    "gemäß Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060 und Art. 74 Abs. 2 UAbs. 2 sowie "
    "§§ 23 und 44 LHO, VV Nummer 4.2 zu § 44 LHO, § 37 Absatz 2 Satz 2 HVwVfG; Anhang XIII der Verordnung "
    "(EU) 2021/1060; Art. 125 Abs. 4 Buchst. a VO (EU) Nr. 1303/2013"
)


def test_find_citations_forms_and_normal_form() -> None:
    hits = find_citations(TEXT)
    assert [h.form for h in hits] == ["lang", "kurz", "paragraphen", "paragraphen", "vv", "paragraph", "lang", "kurz"]
    assert [h.legal_basis.citation() for h in hits] == [
        "Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060",
        "Artikel 74 Absatz 2 Unterabsatz 2",
        "§ 23 LHO",
        "§ 44 LHO",
        "VV Nummer 4.2 zu § 44 LHO",
        "§ 37 Absatz 2 Satz 2 HVwVfG",
        "Anhang XIII der Verordnung (EU) 2021/1060",
        "Artikel 125 Absatz 4 Buchstabe a der Verordnung (EU) Nr. 1303/2013",
    ]
    assert hits[0].text.startswith("Artikel 73") and hits[0].start < hits[1].start


def test_no_citations_and_parse_single() -> None:
    assert find_citations("") == [] and find_citations("ohne Norm") == []
    single = parse_citation("Art. 74 Abs. 2 Buchst. a VO (EU) 2021/1060")
    assert single.is_structured and single.point == "a"
    assert parse_citation("Förderhandbuch Kapitel 3") == LegalBasis(text="Förderhandbuch Kapitel 3")


@pytest.mark.parametrize(
    ("act", "expected"),
    [
        ("VO (EU) 2021/1060", ("reg", 2021, 1060)),
        ("Verordnung (EU) Nr. 1303/2013", ("reg", 2013, 1303)),
        ("Delegierte Verordnung (EU) Nr. 480/2014", ("reg_del", 2014, 480)),
        ("Durchführungsverordnung (EU) 2015/207", ("reg_impl", 2015, 207)),
        ("Richtlinie 2014/24/EU", ("dir", 2014, 24)),
        ("Richtlinie (EU) 2017/1371", ("dir", 2017, 1371)),
        ("Verordnung (EU, Euratom) 2018/1046", ("reg", 2018, 1046)),
        ("Beschluss (EU) 2015/1234", ("dec", 2015, 1234)),
        ("BHO", None),
    ],
)
def test_eu_act_numbering(act: str, expected: tuple[str, int, int] | None) -> None:
    assert eu_act(act) == expected


def test_resolver_and_enrich_keep_existing_values() -> None:
    resolved = EuActResolver().resolve("VO (EU) 2021/1060")
    assert resolved is not None and resolved.celex == "32021R1060"
    assert resolved.eli == "http://data.europa.eu/eli/reg/2021/1060/oj"
    assert resolved.url is not None and resolved.url.endswith("CELEX:32021R1060")
    assert EuActResolver().resolve("Richtlinie 2014/24/EU").celex == "32014L0024"  # type: ignore[union-attr]
    enriched = enrich(LegalBasis(act="VO (EU) 2021/1060", article="74", celex="EIGEN"))
    assert enriched.celex == "EIGEN" and enriched.eli is not None
    assert enrich(LegalBasis(text="frei")) == LegalBasis(text="frei")
    assert enrich(LegalBasis(act="BHO", section="7")).celex is None
