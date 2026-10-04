"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_tyfindings import (
    STANDARDPROFIL,
    formal_zuordnen,
    katalog,
    kennziffer_aus_kuerzungsgrund,
    load_profile,
    zuordnen,
)


def main() -> None:
    """Catalogue, error-code mapping, keyword rules and profile fingerprint."""
    package = distribution("auditcore_tyfindings")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == ["auditcore_common==0.2.1"]
    assert find_spec("auditcore") is None
    assert len(katalog()) == 86
    profil = load_profile(*STANDARDPROFIL)
    assert profil.fingerprint == "149acf962219ec306a83615e56e42500691dd56aa08557f147688862a0adcdc5"
    assert zuordnen("8.9", "Skonto").tof_unterkategorie == "4.2"
    assert zuordnen("16", "unter 50 EUR").gold_plating
    assert zuordnen("1.10").zuordnungsweg == "nicht zugeordnet"
    assert formal_zuordnen("Logo fehlt").tof_unterkategorie == "8.1"
    assert kennziffer_aus_kuerzungsgrund("0") is None
    print("PASS: installed auditcore_tyfindings")


if __name__ == "__main__":
    main()
