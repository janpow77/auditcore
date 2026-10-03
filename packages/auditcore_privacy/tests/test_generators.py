"""Tests für formattreue und natürlich wirkende Generatoren."""

from __future__ import annotations

import re

from auditcore_privacy.generators import (
    clean_ascii_slug,
    generate_company_pseudonym,
    generate_email_pseudonym,
    generate_iban_pseudonym,
    generate_person_pseudonym,
    generate_phone_pseudonym,
    is_valid_iban,
)


def test_clean_ascii_slug() -> None:
    """Umlaute und Sonderzeichen werden sauber und deterministisch umgewandelt."""
    assert clean_ascii_slug("Müller-Lüdenscheidt") == "mueller-luedenscheidt"
    assert clean_ascii_slug("Groß & Partner") == "grosspartner"
    assert clean_ascii_slug("Österreichische Börse") == "oesterreichischeboerse"
    assert clean_ascii_slug("???") == "kontakt"


def test_person_pseudonym_word_count(sample_salt: str) -> None:
    """Wortzahl des Originalnamens wird beibehalten."""
    single_word = generate_person_pseudonym(sample_salt, "Meier", attempt=0)
    assert len(single_word.split()) == 1

    two_words = generate_person_pseudonym(sample_salt, "Sabine Meier", attempt=0)
    assert len(two_words.split()) == 2

    multi_words = generate_person_pseudonym(sample_salt, "Dr. Sabine von Meier", attempt=0)
    assert len(multi_words.split()) == 2


def test_company_pseudonym_legal_forms(sample_salt: str) -> None:
    """Rechtsformen von Unternehmen bleiben im Pseudonym erhalten."""
    cases = [
        ("Musterbau GmbH", "GmbH"),
        ("Nordinvest AG", "AG"),
        ("Logistik Express GmbH & Co. KG", "GmbH & Co. KG"),
        ("Startup UG (haftungsbeschränkt)", "UG (haftungsbeschränkt)"),
        ("Kanzlei Müller & Partner GbR", "GbR"),
    ]
    for orig, expected_form in cases:
        pseudo = generate_company_pseudonym(sample_salt, orig, attempt=0)
        assert pseudo.endswith(expected_form), f"Erwartete Endung {expected_form} bei {pseudo}"

    # Ohne Rechtsform
    no_form = generate_company_pseudonym(sample_salt, "Freie Werkstatt", attempt=0)
    assert not any(no_form.endswith(f) for f in ("GmbH", "AG", "KG", "GbR"))


def test_iban_pseudonym_generation(sample_salt: str) -> None:
    """Erzeugte IBANs sind prüfzifferngültig und nutzen das Null-Institut 00000000."""
    de_iban = generate_iban_pseudonym(sample_salt, "DE89 3705 0198 0000 0123 45", attempt=0)
    assert is_valid_iban(de_iban)
    clean_de = de_iban.replace(" ", "")
    assert len(clean_de) == 22
    assert clean_de.startswith("DE")
    # Bankleitzahl DE ist ab Stelle 4 (8 Stellen) -> 00000000
    assert clean_de[4:12] == "00000000"

    # Ausländische IBAN
    at_iban = generate_iban_pseudonym(sample_salt, "AT61 1904 3002 3457 3201", attempt=0)
    assert is_valid_iban(at_iban)
    clean_at = at_iban.replace(" ", "")
    assert len(clean_at) == 20
    assert clean_at.startswith("AT")


def test_is_valid_iban_cases() -> None:
    """Prüfung der IBAN-Validierung nach ISO 13616."""
    # Gültige reale Test-IBAN
    assert is_valid_iban("DE79 0000 0000 1234 5678 90")
    # Ungültige Prüfziffer
    assert not is_valid_iban("DE99 0000 0000 1234 5678 90")
    # Falsche Länge
    assert not is_valid_iban("DE79 1234")
    # Formal plausibel, aber für das Länderkennzeichen DE (22 Stellen) zu kurz
    assert not is_valid_iban("DE79 0000 0000 1234 5678 9")
    # Ungültige Zeichen
    assert not is_valid_iban("DE79 0000 0000 XXXX 5678 90!")


def test_email_pseudonym_generation(sample_salt: str) -> None:
    """E-Mail-Pseudonyme nutzen die RFC-2606-Beispieldomäne und gültiges Format."""
    email = generate_email_pseudonym(sample_salt, "hans.mueller@alt-firma.de", attempt=0)
    assert email.endswith(".example")
    pattern = r"^[a-z0-9._-]+@[a-z0-9.-]+\.example$"
    assert re.match(pattern, email), f"Ungültiges Format: {email}"


def test_phone_pseudonym_generation(sample_salt: str) -> None:
    """Telefon-Pseudonyme nutzen die Bundesnetzagentur-Testrufnummern (+49 30 23125 xxxx)."""
    phone = generate_phone_pseudonym(sample_salt, "+49 89 12345678", attempt=0)
    assert phone.startswith("+49 30 23125 ")
    parts = phone.split()
    assert len(parts) == 4
    assert len(parts[3]) == 4
    assert parts[3].isdigit()
