"""Run with an isolated Python after pip/APT installation; stdlib assertions only."""

from datetime import date
from importlib.metadata import version
from pathlib import Path

import auditcore_dummygenerator
from auditcore_dummygenerator import TestDataGenerator, list_profiles, profile_reference

assert version("auditcore_dummygenerator") == "0.1.2"
location = Path(auditcore_dummygenerator.__file__).resolve()
assert "site-packages" in location.parts or "dist-packages" in location.parts, location
request = {
    "rows": 3,
    "countries": "DE",
    "fields": [
        {"name": "id", "type": "auto_increment", "params": {"start": 10, "step": 3}},
        {"name": "date", "type": "date_after", "params": {"minDays": 1, "maxDays": 1}},
        {"name": "name", "type": "first_name"},
    ],
}
a = TestDataGenerator(42, base_date=date(2024, 1, 1)).generate_rows(request)
b = TestDataGenerator(42, base_date=date(2024, 1, 1)).generate_rows(request)
assert a == b
assert [row["id"] for row in a] == [10, 13, 16]
assert {row["date"] for row in a} == {"2024-01-02"}
assert TestDataGenerator(42).generate_first_name("DE") == "Anna"
assert len(list_profiles()) == 27
reference = profile_reference("auditcore.dummygenerator.field.number")
assert reference["version"] == "0.1.0" and reference["content_hash"]
print(f"Installed dummy generator smoke PASS: {location}")
