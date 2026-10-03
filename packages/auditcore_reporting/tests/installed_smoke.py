"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution

from auditcore_reporting import get_number_format


def main() -> None:
    """Exercise real formatting behavior and the independent distribution contract."""
    package = distribution("auditcore_reporting")
    assert package.version == "0.3.1"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_common==0.2.1"], runtime
    assert get_number_format("Betrag", 123.45) == '#,##0.00 "EUR"'
    assert get_number_format("Quote", 0.25) == "0.00%"
    assert get_number_format("Datum") == "DD.MM.YYYY"
    assert get_number_format("Anzahl") == "#,##0"
    assert get_number_format("Stunden") == "#,##0.00"
    assert get_number_format("unbekannt", object()) == "General"
    assert get_number_format("Gesamtrate") == '#,##0.00 "EUR"'
    try:
        get_number_format(None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("Legacy TypeError contract changed")
    from auditcore_reporting.templates import builtin_registry, render

    registry = builtin_registry()
    assert [t.id for t in registry.latest()] == ["pruefbericht", "vermerk"]
    memo = registry.get("vermerk")
    first = render(memo, memo.sample, "docx").content
    assert first[:2] == b"PK" and first == render(memo, memo.sample, "docx").content
    assert "Vermerk" in render(memo, memo.sample, "html").content.decode("utf-8")
    print("PASS: installed auditcore_reporting behavior and independent runtime")


if __name__ == "__main__":
    main()
