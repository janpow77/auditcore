"""File names for downloads and exports; each function is one characterized variant.

The variants differ on purpose (character set, length, fallback name); none of
them is a general default:

=============================  ==============================================
Function                       Behaviour
=============================  ==============================================
:func:`path_component`         last path segment, control characters removed
:func:`unicode_filename`       Unicode word characters and umlauts kept
:func:`replace_reserved`       Windows-reserved characters → ``_``
:func:`underscore_slug`        alphanumerics, runs of others → one ``_``
:func:`dashed_slug`            alphanumerics, space/``-``/``_`` → ``-``
:func:`export_filename`        ASCII stem plus extension
=============================  ==============================================
"""

from __future__ import annotations

import os
import re

_RESERVED = '<>:"/\\|?*'
_UNICODE_UNSAFE = re.compile(r"[^\w.()\- äöüÄÖÜß]")
_ASCII_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def path_component(filename: str | None, fallback: str = "download", max_length: int = 255) -> str:
    """Last segment of a browser-supplied path without control characters.

    ``""``, ``"."`` and ``".."`` become ``fallback``; the result is cut to
    ``max_length`` characters.
    """
    candidate = (filename or fallback).replace("\\", "/").split("/")[-1]
    candidate = "".join(char for char in candidate if ord(char) >= 32).strip()
    if candidate in ("", ".", ".."):
        candidate = fallback
    return candidate[:max_length]


def unicode_filename(filename: str | None, fallback: str = "datei", max_length: int = 255) -> str:
    """Base name with word characters, ``.()-``, space and umlauts; others → ``_``."""
    value = os.path.basename(filename or fallback)
    value = _UNICODE_UNSAFE.sub("_", value).strip(" .")
    return value[:max_length] or fallback


def replace_reserved(filename: str, replacement: str = "_") -> str:
    """Replace the characters ``<>:"/\\|?*`` and strip surrounding whitespace."""
    for char in _RESERVED:
        filename = filename.replace(char, replacement)
    return filename.strip()


def underscore_slug(value: str, fallback: str, max_length: int = 80) -> str:
    """Lower-case alphanumerics (Unicode) joined by single ``_``."""
    safe = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    safe = "_".join(part for part in safe.split("_") if part)
    return safe[:max_length] or fallback


def dashed_slug(value: str, fallback: str, max_length: int = 48) -> str:
    """Lower-case alphanumerics; space, ``-`` and ``_`` → ``-``; others dropped."""
    allowed = []
    for char in value.lower():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "-", "_"}:
            allowed.append("-")
    return "".join(allowed).strip("-")[:max_length] or fallback


def export_filename(slug: str, ext: str, fallback: str = "export") -> str:
    """ASCII stem (runs of other characters → ``_``) plus ``.ext``."""
    base = _ASCII_UNSAFE.sub("_", slug).strip("_") or fallback
    return f"{base}.{ext}"
