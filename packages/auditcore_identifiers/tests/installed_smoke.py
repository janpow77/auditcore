"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

import auditcore_identifiers as ai
from auditcore_identifiers.web import check_one


def main() -> None:
    package = distribution("auditcore_identifiers")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None
    assert ai.check_iban("DE89 3704 0044 0532 0130 00").normalized == "DE89370400440532013000"
    assert ai.check_iban("DE89370400440532013001").reason is ai.Reason.INVALID_CHECKSUM
    assert ai.check_iban("DE89370400440532013001", profile="flowinvoice.legacy").valid
    assert ai.check_vat_id("DE136695976").valid and ai.check_tax_id("36574261809").valid
    assert ai.check_lei("7LTWFZYICNSX8D621K86").valid and ai.check_bic("DEUTDEFF500").valid
    assert ai.check_tax_number("2893081508152").details["land"] == "Baden-Württemberg"
    assert ai.check_register_number("HRB 12345").valid
    assert len(ai.profile_names()) == 8
    answer = check_one({"kind": "iban", "value": "DE89370400440532013001", "profile": "strict"})
    assert answer["result"]["reason_label"] == "Prüfziffer falsch"  # type: ignore[index]
    print("auditcore_identifiers installed smoke PASS", ai.__version__)


if __name__ == "__main__":
    main()
