"""Optional PDF output via WeasyPrint (``pip install 'auditcore_dataprotection[pdf]'``)."""

from __future__ import annotations

from collections.abc import Mapping
from types import ModuleType
from typing import Any

from .excel import ExportDependencyError
from .legacy import legacy_report_html

ALLOWED_PROTOCOLS = frozenset({"data"})


def _require_data_url(url: str) -> None:
    """Raise for every URL that is not an inline ``data:`` URL."""
    scheme = url.split(":", 1)[0].strip().lower() if ":" in url else ""
    if scheme not in ALLOWED_PROTOCOLS:
        raise ValueError(f"Externe Ressource im Bericht nicht zulässig: {url}")


def _refusing_url_fetcher(weasyprint: ModuleType) -> object:
    """URL fetcher that only resolves ``data:`` URLs and never follows redirects.

    WeasyPrint ≥ 68 expects a ``URLFetcher`` instance; older versions accept a
    callable returning a dict. Refused resources are left out of the document.
    WeasyPrint 68.0 refuses ``data:`` as well (scheme parsed up to ``://``) and
    is therefore excluded in the ``pdf`` extra.
    """
    fetcher_class = getattr(weasyprint, "URLFetcher", None)
    if fetcher_class is not None:
        fetcher: object = fetcher_class(
            allowed_protocols=set(ALLOWED_PROTOCOLS), allow_redirects=False
        )
        return fetcher
    default_fetcher = weasyprint.default_url_fetcher

    def fetch_data_only(url: str) -> object:
        """Fallback for WeasyPrint < 68: resolve ``data:`` URLs only."""
        _require_data_url(url)
        result: object = default_fetcher(url)
        return result

    return fetch_data_only


def render_pdf(html: str) -> bytes:
    """Render self-contained HTML to PDF without file or network access.

    No base URL is set and only inline ``data:`` resources are resolved; every
    other reference (http, https, file, …) is skipped without being fetched.
    """
    try:
        import weasyprint
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise ExportDependencyError(
            "PDF-Ausgabe benötigt WeasyPrint: pip install 'auditcore_dataprotection[pdf]'"
        ) from exc

    document = weasyprint.HTML(string=html, url_fetcher=_refusing_url_fetcher(weasyprint))
    result: bytes = document.write_pdf()
    return result


def legacy_report_pdf(record: Mapping[str, Any], tenant_label: str = "") -> bytes:
    """PDF of the source-application report layout (``baue_bericht_pdf``)."""
    return render_pdf(legacy_report_html(record, tenant_label))
