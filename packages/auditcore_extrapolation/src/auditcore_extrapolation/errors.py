"""The single exception type of the package."""

from __future__ import annotations


class ExtrapolationInputError(ValueError):
    """Input, method or profile does not satisfy the documented contract.

    The message is German and names the offending field; nothing is replaced
    by a silent default.
    """
