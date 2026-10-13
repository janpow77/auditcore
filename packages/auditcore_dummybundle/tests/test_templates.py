"""Vorlagenprofile: Daten statt Code, belegte Spalten, neutrale Platzhalter, Kennzeichnung."""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from importlib import import_module
from importlib.resources import files
from pathlib import Path

import pytest
from auditcore_common.hashing import canonical_sha256
from conftest import config

import auditcore_dummybundle
from auditcore_dummybundle import (
    MARKING,
    BundleError,
    Options,
    anomaly_codes,
    build_bundle,
    generate_templates,
    get_template,
    templates,
)
from auditcore_dummybundle.templates import project

PACKAGE = Path(auditcore_dummybundle.__file__).parent
templates_module = import_module("auditcore_dummybundle.templates")
ALL = list(templates())
PUBLIC = [key for key, template in templates().items() if template.public]
#: Bezeichnungen, die in einem öffentlichen Paket nichts zu suchen haben. Die Namen
#: einzelner Stellen sind zusammengesetzt, damit auch diese Datei sie nicht nennt.
FORBIDDEN = (
    "WI" + "Bank",
    "Wirtschafts- und Infra" + "strukturbank",
    "Kunden" + "portal",
    "Hes" + "sen",
    "hes" + "sisch",
    "HM" + "WVW",
    "Test" + "land",
    "2021" + "DE16",
    "Nor" + "dex",
    "Iso" + "ver",
    "SA" + "P-",
    "Fa" + "ker",
    "QCh" + "ess",
)


def _headers(template_id: str, table: int = 0) -> list[str]:
    return [column.header for column in templates()[template_id].tables[table].columns]


def test_expected_templates_are_all_public() -> None:
    assert ALL == ["V0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "N1"]
    assert PUBLIC == ALL
    assert "V10" not in ALL and "V11" not in ALL
    titles = {key: template.title for key, template in templates().items()}
    assert titles["V1"] == "Belegliste zum Mittelabruf (ausführlich, 37 Spalten)"
    assert titles["V3"] == "Gesamtbelegliste des Vorhabens"
    assert titles["N1"] == "Belegliste zum Mittelabruf (kompakt)"


def test_non_public_profiles_need_explicit_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    """Der Schalter ``public`` bleibt wirksam, auch wenn ihn derzeit kein Profil ausschaltet."""
    hidden = {key: replace(value, public=key != "V8") for key, value in templates().items()}
    monkeypatch.setattr(templates_module, "templates", lambda: hidden)
    with pytest.raises(BundleError) as error:
        get_template("V8")
    assert error.value.code == "unknown_template"
    with pytest.raises(BundleError):
        generate_templates(config(), ["V8"])
    assert generate_templates(config(), ["V8"], Options(include_private=True)).tables


def test_profiles_are_released_by_the_rights_holder_with_hash() -> None:
    folder = files("auditcore_dummybundle").joinpath("template_data")
    hashes = set()
    for key in ALL:
        raw = json.loads(folder.joinpath(f"{key.lower()}.json").read_text(encoding="utf-8"))
        review = raw["review"]
        assert raw["status"] == "Freigegeben"
        assert review["human_release_approval"] == "GRANTED"
        assert review["approved_on"] == "2026-10-13" and "Rechteinhaber" in review["approved_by"]
        assert "elf Vorlagenprofile von auditcore_dummybundle 0.1.0" in review["scope"]
        assert "auditcore_dummygenerator" in review["not_covered"]
        assert raw["content_hash"] == canonical_sha256(templates_module.profile_content(raw))
        assert templates()[key].content_hash == raw["content_hash"]
        assert ("third_party" in review) == (key in {"V5", "V6"})
        hashes.add(raw["content_hash"])
    assert len(hashes) == 11
    union = dict(templates()["V5"].release)["third_party"]
    assert "Unionsrecht" in union and "erstreckt sich nicht" in union


def test_changed_profile_content_is_rejected() -> None:
    folder = files("auditcore_dummybundle").joinpath("template_data")
    raw = json.loads(folder.joinpath("v0.json").read_text(encoding="utf-8"))
    raw["title"] = "Anderer Titel"
    with pytest.raises(BundleError) as error:
        templates_module._template(raw)
    assert error.value.code == "profile_hash"


def test_released_profiles_of_the_field_generator_stay_untouched() -> None:
    from auditcore_dummygenerator import list_profiles

    profiles = list_profiles()
    assert len(profiles) == 27
    assert {p["review"]["human_release_approval"] for p in profiles} == {"NOT_GRANTED"}
    assert {p["status"] for p in profiles} == {"Draft"}


def test_column_counts_match_the_documented_layouts() -> None:
    assert len(_headers("V1")) == 37
    assert len(_headers("V3")) == 38 and _headers("V3")[0] == "Quelldatei"
    assert len(_headers("V2")) == 26
    assert len(_headers("V8")) == 27
    assert len(_headers("V9")) == 22
    assert len(_headers("V4")) == 13
    assert _headers("V1").count("Währung") == 7


def test_official_annex_columns_carry_their_letters() -> None:
    main = _headers("V5", 1)
    assert [h[:3] for h in main[2:7]] == ["(A)", "(B)", "(C)", "(D)", "(E)"]
    assert main[3].endswith(
        "gemäß Artikel 91 Absatz 3 Buchstabe a und Artikel 91 Absatz 4 Buchstabe c"
    )
    annexes = {table.name: table for table in templates()["V6"].tables}
    assert list(annexes) == ["RL Kopf", *(f"RL Anlage {n}" for n in range(1, 8))]
    annex4 = [column.header for column in annexes["RL Anlage 4"].columns]
    assert annex4[5:7] == ["(E = A - C) Differenz", "(F = B - D) Differenz"]
    assert annex4[7].startswith("(G) Bemerkungen (bei Differenz für jede Art von Abzug")
    assert annexes["RL Anlage 2"].title.startswith("Anlage 2: Während des Geschäftsjahres")
    for template_id in ("V5", "V6"):
        sources = " ".join(templates()[template_id].sources)
        assert "ABl. L 231" in sources and "abgerufen am 13.10.2026" in sources


@pytest.mark.parametrize("template_id", ALL)
def test_every_column_resolves_against_a_bundle(template_id: str) -> None:
    bundle = build_bundle(config(3, corrections=6))
    template = get_template(template_id, include_private=True)
    tables, _ = project(bundle, template)
    assert tables
    for table in tables:
        assert len(table.name) <= 27
        assert all(len(row) == len(table.columns) for row in table.rows)


@pytest.mark.parametrize("template_id", ALL)
def test_unproven_columns_stay_empty_and_say_why(template_id: str) -> None:
    template = get_template(template_id, include_private=True)
    for table in template.tables:
        for column in table.columns:
            if column.field is None and column.const is None:
                assert column.note, (template_id, column.header)


def test_placeholders_are_recognisable() -> None:
    result = generate_templates(config(5, reduction_share=Decimal("1.00")), ["V0", "N1", "V7"])
    cells = {str(cell) for table in result.tables for row in table.rows for cell in row}
    assert "Kürzungsgrund (Platzhalter)" in cells
    assert "Feststellungsart (Platzhalter)" in cells
    assert any("Spezifisches Ziel" in cell and "(Platzhalter)" in cell for cell in cells)
    assert "2021XX16SYPR001" not in cells  # nur in V5/V6


def test_no_named_bodies_in_sources_profiles_and_documentation() -> None:
    """Quelltext und Daten ohne alle Begriffe; die Doku darf Werkzeuge nennen, Stellen nicht."""
    # Quellbaum – auch beim Test gegen das installierte Wheel.
    root = Path(__file__).resolve().parents[1]
    code = [*PACKAGE.rglob("*.json"), *PACKAGE.rglob("*.py"), *(root / "tests").glob("*.py")]
    candidates = (*root.glob("*.md"), root / "NOTICE", *(root / "docs").glob("*.md"))
    prose = [path for path in candidates if path.is_file()]
    assert len(code) >= 30
    for paths, words in ((code, FORBIDDEN), (prose, FORBIDDEN[:8])):
        for path in sorted(paths):
            text = path.read_text(encoding="utf-8")
            for word in words:
                assert word not in text, (path.name, word)


def test_no_named_bodies_in_catalogue_and_generated_files() -> None:
    from auditcore_dummybundle import document, web

    cfg = config(13, operations=6, corrections=6, anomalies=anomaly_codes())
    generated = document(generate_templates(cfg, ALL, Options(solution=True, marking_column=True)))
    recipes = [
        web.recipe_from_template({"template": key, "run": {"seed": 1, "base_date": "2026-01-01"}})
        for key, template in templates().items()
        if template.free_table is not None
    ]
    for data in (web.catalogue(), generated, recipes):
        text = json.dumps(data, ensure_ascii=False)
        for word in FORBIDDEN:
            assert word not in text, word
    names = [table["name"] + table["title"] for table in generated["tables"]]
    assert not any(word in name for name in names for word in FORBIDDEN)


def test_template_files_are_plain_data_with_identity() -> None:
    folder = files("auditcore_dummybundle").joinpath("template_data")
    names = sorted(entry.name for entry in folder.iterdir())
    assert names == sorted(f"{key.lower()}.json" for key in ALL)
    for name in names:
        raw = json.loads(folder.joinpath(name).read_text(encoding="utf-8"))
        assert raw["artifact_id"] == f"auditcore.dummybundle.template.{raw['id'].lower()}"
        assert raw["version"] == "0.1.0"
        assert raw["legal_basis"] and raw["sources"]
    assert not (PACKAGE / "template_code").exists()


def test_v2_has_one_list_per_claim_with_total_row_on_top() -> None:
    cfg = config(8, operations=2)
    bundle = build_bundle(cfg)
    result = generate_templates(cfg, ["V2"])
    assert len(result.tables) == len(bundle.table("claims"))
    for table, claim in zip(result.tables, bundle.table("claims"), strict=True):
        headers = [column.header for column in table.columns]
        eligible = headers.index("Förderfähig lt. zwischengeschalteter Stelle")
        assert table.rows[0][0] is None  # Summenzeile ohne laufende Nummer
        assert table.rows[0][eligible] == claim["eligible"]
        assert sum(row[eligible] for row in table.rows[1:]) == claim["eligible"]  # type: ignore[misc]
        difference = headers.index("Differenz")
        assert {row[difference] for row in table.rows} == {Decimal("0.00")}


def test_marking_is_in_metadata_and_optional_column() -> None:
    plain = generate_templates(config(), ["V0"])
    marked = generate_templates(config(), ["V0"], Options(marking_column=True))
    assert plain.meta["marking"] == MARKING == "SYNTHETISCH"
    assert plain.meta["version"] == auditcore_dummybundle.__version__
    assert plain.meta["seed"] == 42 and plain.meta["base_date"] == "2026-01-01"
    assert marked.tables[0].columns[-1].header == "synthetisch"
    assert {row[-1] for row in marked.tables[0].rows} == {MARKING}
    assert len(marked.tables[0].columns) == len(plain.tables[0].columns) + 1


def test_too_many_tables_are_refused() -> None:
    with pytest.raises(BundleError) as error:
        generate_templates(config(operations=12), ["V2"], Options(max_tables=5))
    assert error.value.code == "too_large"
