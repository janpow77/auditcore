"""Run with python -I after installing ``auditcore_funding_sources[xlsx]``."""

import io
from importlib.metadata import distribution


def main() -> None:
    """Read an XLSX transparency list through the optional extra; defusedxml is active."""
    import openpyxl
    import openpyxl.xml

    assert openpyxl.xml.DEFUSEDXML, "defusedxml must be used for untrusted workbooks"
    extras = [r for r in distribution("auditcore_funding_sources").requires or [] if "xlsx" in r]
    assert any(r.startswith("openpyxl") for r in extras) and any("defusedxml" in r for r in extras)
    from auditcore_funding_sources import workshop

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Liste der Vorhaben"])
    ws.append(["Name des Begünstigten", "Gesamtkosten", "PLZ", "Ort"])
    ws.append(["Beispiel GmbH", 125000.5, 1067, "Dresden"])
    buffer = io.BytesIO()
    wb.save(buffer)
    rows = workshop.parse_file(buffer.getvalue(), "liste.xlsx")
    assert rows[0]["beneficiary_name"] == "Beispiel GmbH"
    assert rows[0]["cost_total_raw"] == "125000.5"
    print("PASS: installed auditcore_funding_sources[xlsx] with openpyxl and defusedxml")


if __name__ == "__main__":
    main()
