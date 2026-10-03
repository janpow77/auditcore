"""Importprüfung ausschließlich der installierten öffentlichen API.

Läuft ohne das optionale Extra ``[pymupdf]``: Modelle und Muster stehen bereit,
die PDF-Funktionen melden das fehlende Extra klar statt beim Import zu scheitern.
"""

from auditcore_pdf import (
    STANDARD_PATTERNS,
    SanitizationPolicy,
    is_pymupdf_available,
    merge_documents,
    open_pdf,
)

assert "iban" in STANDARD_PATTERNS
assert SanitizationPolicy(scrub_metadata=True).scrub_metadata is True
expected = ValueError if is_pymupdf_available() else RuntimeError
for call in (lambda: open_pdf(b""), lambda: merge_documents([b""])):
    try:
        call()
    except expected:
        pass
    else:
        raise AssertionError("Leeres PDF oder fehlendes PyMuPDF wurde nicht gemeldet")
