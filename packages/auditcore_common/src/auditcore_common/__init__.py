"""Shared helpers of the auditcore domain packages, proven equal before merging.

Only the standard library is required; ``defusedxml`` is the optional extra
``xml`` and is imported lazily. Each topic has its own module, there is no
catch-all ``utils``:

``json_values``
    JSON value types, :func:`~auditcore_common.json_values.jsonable` with
    explicitly named conversion variants, :func:`decode_json`.
``hashing``
    Canonical JSON and SHA-256 over JSON, text and files.
``profiles``
    Listing, loading and recommending packaged, versioned JSON profiles.
``frozen``
    Read-only copies of JSON data (``MappingProxyType``/``tuple``) and back.
``safe_xml``
    XML parsing only through ``defusedxml``.
``html_text``
    Anchor links of an HTML page and HTML marker detection.
``numeric``
    NumPy-compatible pairwise sum and rounding without NumPy, finite checks,
    percent rates, percentage shares and tolerant float coercion.
``filenames``
    Characterized file-name variants for downloads and exports.
``aio``
    Running coroutines from synchronous code (loop per thread).
``clock`` / ``ids``
    Timezone-aware time and random identifiers.
``text``
    Small text normalisations shared by several packages.
``optional``
    Lazy import of optional extras with a package-specific error.
"""

from __future__ import annotations

__version__ = "0.1.1"

__all__ = ["__version__"]
