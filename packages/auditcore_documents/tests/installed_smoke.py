"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

import auditcore_documents as ad
from auditcore_documents.legacy import DocumentCompareService


def main() -> None:
    """Pure comparison, article-law commands, reasons port and extra boundaries."""
    package = distribution("auditcore_documents")
    assert package.version == "0.1.0"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert find_spec("auditcore") is None
    assert DocumentCompareService.VERSION == "1.1.0"
    old = [ad.CompareItem("0", text="Die Prüfbehörde prüft das Vorhaben.", location="§ 1, Absatz 1")]
    new = [
        ad.CompareItem("0", text="Der Begünstigte legt Belege vor.", location="§ 1, Absatz 1"),
        ad.CompareItem("1", text="Die Prüfbehörde prüft das Vorhaben.", location="§ 1, Absatz 2"),
    ]
    rows, counts = ad.compare_items(old, new, mode="text", profile=ad.LEGACY_DIFFLIB)
    assert counts["matched_count"] == 1 and counts["added_count"] == 1, counts
    base = [ad.LawParagraph("§ 11", 1, "gelten § 9 des BSI-Gesetzes sowie")]
    paragraphs, open_commands, recognised = ad.apply_commands(
        base,
        [
            "In § 11 Absatz 1 Satz 1 wird die Angabe „§ 9 des BSI-Gesetzes“ "
            "durch die Angabe „§ 52 des BSI-Gesetzes“ ersetzt."
        ],
    )
    assert recognised == 1 and not open_commands
    assert paragraphs[0].new_text == "gelten § 52 des BSI-Gesetzes sowie"
    reason, meta = ad.generate_reason(
        "Frist nach § 5", "Frist nach § 6", provider=lambda *_: {"begruendung": "Nach § 7."}
    )
    assert reason == "Nach § 7." and meta["missing_references"] == ["§ 7"]
    assert ad.sanitise_settings({"threshold": 5})["threshold"] == 70
    if find_spec("rapidfuzz") is None:
        try:
            ad.get_scorer("rapidfuzz-token-set")
        except ad.DependencyError:
            pass
        else:
            raise AssertionError("rapidfuzz scorer must require the optional extra")
    print("PASS: installed auditcore_documents comparison, synopsis, reasons and extra boundary")


if __name__ == "__main__":
    main()
