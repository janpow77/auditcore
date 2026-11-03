"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from auditcore_reportgates import BoundValue, Verdict, check_paragraph, exact, release, unit_of


def main() -> None:
    """Prose gate and release decision on a synthetic paragraph."""
    values = [BoundValue(exact(15_782_365), unit_of("Euro"), "Tabelle 1")]
    result = check_paragraph("Bewilligt wurden 15,8 Mio. Euro.", values)
    assert result.verdict is Verdict.PASSED
    assert release([result], ["prose_numbers"]).released
    print("auditcore_reportgates ok")


if __name__ == "__main__":
    main()
