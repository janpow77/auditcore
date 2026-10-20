"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_tyfindings import (
    DEFAULT_RULE_SET,
    STANDARDPROFIL,
    formal_zuordnen,
    katalog,
    kennziffer_aus_kuerzungsgrund,
    load_overview_rules,
    load_profile,
    match_rule,
    zuordnen,
)


def main() -> None:
    """Catalogue, error-code mapping, keyword rules and profile fingerprint."""
    package = distribution("auditcore_tyfindings")
    assert package.version == "0.3.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == ["auditcore_common==0.2.1"]
    assert find_spec("auditcore") is None
    assert len(katalog()) == 86
    profil = load_profile(*STANDARDPROFIL)
    assert profil.fingerprint == "f83a36f21f57605f85a117cd7b004ae9ce04c42fcb73b749c34e189970ad7ebf"
    assert profil.kategorie_de("4") == "Nicht förderfähige Ausgaben"
    assert zuordnen("8.9", "Skonto").tof_unterkategorie == "4.2"
    assert zuordnen("16", "unter 50 EUR").gold_plating
    assert zuordnen("1.10").zuordnungsweg == "nicht zugeordnet"
    assert formal_zuordnen("Logo fehlt").tof_unterkategorie == "8.1"
    assert kennziffer_aus_kuerzungsgrund("0") is None
    regeln = load_overview_rules(*DEFAULT_RULE_SET)
    assert regeln.fingerprint == "6398d3ebfa8edf6de9887aedda7077f7c48102d2416c6cb25a1a23f40c9754b5"
    assert match_rule("UR", "Kürzung, UR", regelwerk=regeln) is not None
    print("PASS: installed auditcore_tyfindings")


if __name__ == "__main__":
    main()
