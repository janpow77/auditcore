"""Importprüfung ausschließlich der installierten öffentlichen API."""

from auditcore_privacy import EntityType, PseudonymEngine, mask_text

engine = PseudonymEngine(scope_key="smoke", salt="0123456789abcdef0123456789abcdef")
person = engine.get_or_create(EntityType.PERSON, "Dr. Hans Meyer")
assert person == engine.get_or_create(EntityType.PERSON, "Dr. Hans Meyer")
assert engine.get_or_create(EntityType.COMPANY, "Musterbau GmbH").endswith("GmbH")
assert mask_text("DE1234567890") == "DE12••••••90"
