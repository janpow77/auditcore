"""Optional PDF output via WeasyPrint (``pip install 'auditcore_dataprotection[pdf]'``)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .excel import ExportDependencyError
from .legacy import legacy_report_html


def render_pdf(html: str) -> bytes:
    """Render self-contained HTML to PDF; no base URL, so no file or network access."""
    try:
        from weasyprint import HTML
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise ExportDependencyError(
            "PDF-Ausgabe benötigt WeasyPrint: pip install 'auditcore_dataprotection[pdf]'"
        ) from exc

    def refuse(url: str) -> dict[str, Any]:
        """Refuse every external resource."""
        raise ValueError(f"Externe Ressource im Bericht nicht zulässig: {url}")

    result: bytes = HTML(string=html, url_fetcher=refuse).write_pdf()
    return result


def legacy_report_pdf(record: Mapping[str, Any], tenant_label: str = "") -> bytes:
    """PDF of the source-application report layout (``baue_bericht_pdf``)."""
    return render_pdf(legacy_report_html(record, tenant_label))
