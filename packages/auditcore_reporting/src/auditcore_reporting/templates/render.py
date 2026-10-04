"""One entry point for all formats: validate, resolve and render with provenance."""

from __future__ import annotations

from dataclasses import dataclass

from auditcore_common.hashing import canonical_sha256

from .design import NEUTRAL_DESIGN, DesignProfile
from .errors import TemplateError
from .model import ReportTemplate
from .options import DEFAULT_OPTIONS, RenderOptions
from .resolve import ResolveLimits, checked_data, resolve
from .values import plain

MEDIA_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "html": "text/html; charset=utf-8",
}


@dataclass(frozen=True)
class RenderResult:
    """Rendered file plus what is needed to reproduce it exactly."""

    content: bytes
    format: str
    media_type: str
    template_id: str
    template_version: str
    template_fingerprint: str
    data_sha256: str
    design: str
    text_blocks: tuple[str, ...]


def render(
    template: ReportTemplate,
    data: object,
    output: str = "docx",
    design: DesignProfile = NEUTRAL_DESIGN,
    limits: ResolveLimits | None = None,
    *,
    options: RenderOptions = DEFAULT_OPTIONS,
) -> RenderResult:
    """Render ``data`` with ``template`` as ``docx``, ``pdf`` or ``html``.

    ``options`` sets document properties (author, title, creation time); Word
    templates keep the properties of their source file and reject them.
    Raises :class:`TemplateDataError` (data contract), :class:`RenderLimitError`,
    :class:`RenderDependencyError` (missing extra) or :class:`TemplateError`.
    """
    if output not in template.formats:
        raise TemplateError(
            f"{template.id}: Format {output!r} nicht vorgesehen ({template.formats})."
        )
    if template.docx is not None:
        if options != DEFAULT_OPTIONS:
            raise TemplateError(
                f"{template.id}: Render-Optionen gelten nur für Vorlagen mit Blöcken;"
                " Word-Vorlagen behalten die Eigenschaften der Vorlagedatei."
            )
        from .docx_template import render_docx_template

        content = render_docx_template(template, data, limits)
        values = checked_data(template, plain(data))
        return RenderResult(
            content, output, MEDIA_TYPES[output], template.id, template.version,
            template.fingerprint, canonical_sha256(values), "docx-vorlage", (),
        )  # fmt: skip
    document = resolve(template, data, limits)
    if output == "html":
        from .render_html import render_html

        content = render_html(document, design, options).encode("utf-8")
    elif output == "pdf":
        from .render_pdf import render_pdf

        content = render_pdf(document, design, options)
    else:
        from .render_docx import render_docx

        content = render_docx(document, design, options)
    return RenderResult(
        content, output, MEDIA_TYPES[output], document.template_id, document.template_version,
        document.template_fingerprint, document.data_sha256, f"{design.id}@{design.version}",
        document.text_blocks,
    )  # fmt: skip
