"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec


def main() -> None:
    """Exercise every module of the installed distribution."""
    package = distribution("auditcore_common")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None

    from auditcore_common.clock import require_aware, utc_now
    from auditcore_common.frozen import freeze, thaw
    from auditcore_common.hashing import canonical_json, canonical_sha256
    from auditcore_common.html_text import anchor_links, has_html_marker
    from auditcore_common.ids import new_uuid
    from auditcore_common.json_values import decode_json, jsonable
    from auditcore_common.numeric import numpy_pairwise_sum, numpy_round, parse_percent_rate
    from auditcore_common.optional import require_module
    from auditcore_common.profiles import packaged_profile_ids
    from auditcore_common.text import compact_upper, group_thousands_de

    assert canonical_json({"b": 1, "a": "ä"}) == '{"a":"ä","b":1}'
    assert canonical_sha256({}) == (
        "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
    )
    assert jsonable({"d": [1, (2,)]}) == {"d": [1, [2]]}
    assert decode_json(b"[1]", ValueError) == [1]
    assert thaw(freeze({"a": [1]})) == {"a": [1]}
    assert anchor_links("<a href='/x'> A  b </a>") == [("/x", "A b")]
    assert has_html_marker("<!DOCTYPE html>")
    assert numpy_pairwise_sum([0.1 * i for i in range(16)]) == 12.0  # naive sum: 12.000000000000002
    assert numpy_round(2.5, 0) == 2.0 and numpy_round(2.675, 2) == 2.68
    assert str(parse_percent_rate("19,0 %")) == "19"
    assert group_thousands_de(1234567) == "1.234.567"
    assert compact_upper("de 123") == "DE123"
    assert require_aware(utc_now()).tzinfo is not None
    assert len(new_uuid()) == 36
    assert require_module("json", ValueError, "x").__name__ == "json"
    assert packaged_profile_ids("email") == ()

    from auditcore_common.aio import run_sync
    from auditcore_common.filenames import dashed_slug, path_component
    from auditcore_common.numeric import as_float, share_percent

    async def answer() -> int:
        return 42

    assert run_sync(answer()) == 42
    assert share_percent(1, 3) == 33.33 and share_percent(1, 0) == 0.0
    assert as_float("") is None and as_float("", blank_as_none=True) is None
    assert as_float("1.5") == 1.5 and as_float("x") is None
    assert path_component("../a/b.txt") == "b.txt"
    assert dashed_slug("Aral Tankstelle!", "tankstelle") == "aral-tankstelle"  # stdlib package without profiles
    if find_spec("defusedxml") is not None:
        from auditcore_common.safe_xml import parse_xml

        assert parse_xml(b"<a><b/></a>", error=ImportError, message="x")[0].tag == "b"
    else:
        from auditcore_common.safe_xml import parse_xml

        try:
            parse_xml(b"<a/>", error=ImportError, message="xml-Extra fehlt")
        except ImportError as error:
            assert str(error) == "xml-Extra fehlt"
        else:
            raise AssertionError("Without the xml extra parse_xml must fail")
    print("PASS: installed auditcore_common modules")


if __name__ == "__main__":
    main()
