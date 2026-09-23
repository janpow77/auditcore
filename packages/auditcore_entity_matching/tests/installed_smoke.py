"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_entity_matching import (
    DependencyError,
    available_profiles,
    check_lei,
    extract_lei,
    legacy,
    load_profile,
    normalize,
    pair_score,
    recommended_profile,
)


def main() -> None:
    """Exercise normalisation, LEI checks and the optional fuzzy boundary."""
    package = distribution("auditcore_entity_matching")
    assert package.version == "0.2.0"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert find_spec("auditcore") is None
    assert len(available_profiles()) == 15
    assert check_lei("529900T8BM49AURSDO55").valid
    assert not check_lei("7LTWFZYICNSX8D621K87").valid
    assert legacy.flowworkshop_is_valid_lei("7LTWFZYICNSX8D621K87")
    assert extract_lei("LEI: 529900T8BM49AURSDO55") == "529900T8BM49AURSDO55"
    state_aid = load_profile("flowworkshop.state_aid", "2026.09.1")
    sanctions = load_profile("flowworkshop.sanctions", "2026.09.1")
    assert normalize("Müller GmbH", state_aid) == "mueller"
    assert normalize("Müller GmbH", sanctions) == "muller"
    umschrift = load_profile("audit_designer.sanctions", "2026.09.2")
    assert normalize("Mu\u0308ller-Søren GmbH", umschrift) == "mueller soren"
    assert legacy.flowworkshop_normalize_name_umschrift("Müller") == "mueller"
    payee = load_profile("riskanalysis.payee", "2026.09.1")
    assert normalize("Müller GmbH", payee) == "mu ller"
    assert normalize("Mu\u0308ller GmbH", recommended_profile("payee")) == "mueller"
    if find_spec("rapidfuzz") is None:
        try:
            legacy.flowworkshop_fuzzy_best("siemens", [(1, "siemens")])
        except DependencyError:
            pass
        else:
            raise AssertionError("Fuzzy matching must require the optional extra")
    else:
        assert legacy.flowworkshop_fuzzy_best("siemens", [(1, "siemens")]) == (1, 100.0)
        assert pair_score("stadtwerke nord", "nordstadtwerke", "token_set_ratio") > 96
    print("PASS: installed auditcore_entity_matching normalisation, LEI and extra boundary")


if __name__ == "__main__":
    main()
