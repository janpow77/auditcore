"""Name normalisation for comparison only; the displayed name is never changed.

Two algorithms exist in the sources and are kept apart:

* ``translate_then_casefold`` (flowworkshop state aid): a fixed character
  table (``ä → ae``, ``é → e`` …) *before* case folding, ``&`` → ``und``,
  punctuation → space, legal-form tokens and optionally filler words removed.
  Characters outside the table, including upper-case accented letters such as
  ``É``, are kept.
* ``casefold_fold_nfkd`` (flowworkshop and audit_designer sanctions): case
  folding, a small fold map (``ß → ss``, ``ø → o`` …), NFKD decomposition
  without combining marks (``ä → a``), punctuation → space, legal-form tokens
  removed.
* ``casefold_nfc_fold_nfkd`` (audit_designer sanctions from 2026.09.2): as
  above, but the case-folded text is first composed to NFC so that a
  decomposed umlaut (``u`` + combining diaeresis) meets the fold map
  (``ü → ue``) instead of losing only its diaeresis.
* ``lower_nfkd_ascii`` (flowinvoice PEP bulk screening): ``str.lower``,
  NFKD without combining marks, then every character outside ``a-z``,
  ``0-9`` and whitespace becomes a separator. ``ß``, ``ø``, ``ł`` and all
  non-Latin scripts are therefore lost (``Straße → stra e``).
* ``nfkd_lower_regex`` (riskanalysis payee normaliser): NFKD decomposition,
  ``lower()``, every character matched by ``nonword_pattern`` → space (this
  also turns the combining diaeresis of ``ü`` into a space: ``Müller → mu
  ller``), legal-form/generic words matched by ``removal_pattern`` → space,
  whitespace collapsed. Reproduced as characterized, not corrected.

Optional ``compose = "NFC"`` and a fold map on ``nfkd_lower_regex`` and
``lower_nfkd_ascii`` exist only in the user-decided profiles (23.09.2026):
decomposed umlauts are composed first and ``ä/ö/ü/ß`` transliterated.
"""

from __future__ import annotations

import re
import unicodedata

from .errors import ProfileError
from .profiles import Profile

_WORD = re.compile(r"[^\w\s]", re.UNICODE)
_ASCII_WORD = re.compile(r"[^a-z0-9\s]")
_SPACE = re.compile(r"\s+")


def normalize(text: str | None, profile: Profile, *, drop_filler: bool = False) -> str:
    """Comparison form of ``text`` under the given normalisation profile.

    ``None`` and empty input yield ``""``. ``drop_filler`` is only meaningful
    for profiles with filler words (state aid identifier bucket).
    """
    rules = profile.normalization
    if rules is None:
        raise ProfileError(f"Profil {profile.id} enthält keine Normalisierung.")
    if not text:
        return ""
    if not isinstance(text, str):
        raise TypeError("Namen sind als Text zu übergeben.")
    if rules.compose == "NFC":
        text = unicodedata.normalize("NFC", text)
    if rules.algorithm == "nfkd_lower_regex":
        if rules.compose is None and not rules.fold_map:
            value = unicodedata.normalize("NFKD", text).lower()
        else:
            # Decided variant: transliterate before decomposition, then drop the
            # remaining combining marks instead of turning them into separators.
            value = text.lower()
            for source, target in rules.fold_map.items():
                value = value.replace(source, target)
            decomposed = unicodedata.normalize("NFKD", value)
            value = "".join(c for c in decomposed if not unicodedata.combining(c))
        value = re.sub(str(rules.nonword_pattern), " ", value)
        value = re.sub(str(rules.removal_pattern), " ", value)
        return _SPACE.sub(" ", value).strip()
    if rules.algorithm == "lower_nfkd_ascii":
        lowered = text.lower().strip()
        for source, target in rules.fold_map.items():
            lowered = lowered.replace(source, target)
        decomposed = unicodedata.normalize("NFKD", lowered)
        value = "".join(c for c in decomposed if not unicodedata.combining(c))
        value = _ASCII_WORD.sub(" ", value)
    elif rules.algorithm == "translate_then_casefold":
        table: dict[str, str | int | None] = dict(rules.translation)
        value = text.translate(str.maketrans(table)).casefold()
        if rules.ampersand is not None:
            value = value.replace("&", rules.ampersand)
        value = _SPACE.sub(" ", _WORD.sub(" ", value)).strip()
    else:
        value = text.casefold()
        if rules.algorithm == "casefold_nfc_fold_nfkd":
            value = unicodedata.normalize("NFC", value)
        for source, target in rules.fold_map.items():
            if source in value:
                value = value.replace(source, target)
        decomposed = unicodedata.normalize("NFKD", value)
        value = "".join(c for c in decomposed if not unicodedata.combining(c))
        value = _WORD.sub(" ", value)
    tokens = []
    for token in value.split():
        compact = token.replace(".", "").replace("-", "") if rules.compact_tokens else token
        if compact in rules.legal_suffixes:
            continue
        if drop_filler and compact in rules.filler_words:
            continue
        tokens.append(token)
    return " ".join(tokens)
