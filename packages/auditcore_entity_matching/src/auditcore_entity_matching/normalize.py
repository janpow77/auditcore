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
"""

from __future__ import annotations

import re
import unicodedata

from .errors import ProfileError
from .profiles import Profile

_WORD = re.compile(r"[^\w\s]", re.UNICODE)
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
    if rules.algorithm == "translate_then_casefold":
        table: dict[str, str | int | None] = dict(rules.translation)
        value = text.translate(str.maketrans(table)).casefold()
        if rules.ampersand is not None:
            value = value.replace("&", rules.ampersand)
        value = _SPACE.sub(" ", _WORD.sub(" ", value)).strip()
    else:
        value = text.casefold()
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
