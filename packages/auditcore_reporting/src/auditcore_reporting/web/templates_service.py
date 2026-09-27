"""Report templates in contract ``reporting_ui/1``: list, data schema, preview, render.

Framework-free; the application passes its :class:`TemplateCatalogue`
(registry plus design profiles). Without one the built-in templates and the
neutral design are served.
"""

from __future__ import annotations

import importlib.util
import re
from collections.abc import Mapping, Sequence
from functools import lru_cache
from html import escape

from auditcore_common import rest

from ..templates import (
    NEUTRAL_DESIGN,
    DesignProfile,
    RenderDependencyError,
    RenderLimitError,
    ReportTemplate,
    TemplateDataError,
    TemplateError,
    TemplateNotFoundError,
    TemplateRegistry,
    builtin_registry,
    render,
    resolve,
)
from ..templates.render_html import render_html
from ..templates.values import plain
from .contract import CONTRACT, ContractError

_FILENAME = re.compile(r"[^\w .()-]", re.UNICODE)


class DataContractError(ContractError):
    """Data do not satisfy the template's data contract; the body lists every issue."""

    def __init__(self, error: TemplateDataError) -> None:
        super().__init__(str(error), code="invalid_data")
        self.issues = [issue.to_dict() for issue in error.issues]

    def to_dict(self) -> dict[str, object]:
        """Error body with ``issues`` (path and message)."""
        body = super().to_dict()
        error = body["error"]
        assert isinstance(error, dict)
        error["issues"] = self.issues
        return body


class TemplateCatalogue:
    """Templates and design profiles offered by one application."""

    def __init__(
        self,
        registry: TemplateRegistry | None = None,
        designs: Sequence[DesignProfile] = (NEUTRAL_DESIGN,),
    ) -> None:
        self.registry = registry if registry is not None else builtin_registry()
        if not designs:
            raise ValueError("Mindestens ein Gestaltungsprofil.")
        self.designs = {design.id: design for design in designs}

    def template(self, template_id: str, version: object = None) -> ReportTemplate:
        """Template or ``404 unknown_template``."""
        if version is not None and not isinstance(version, str):
            raise ContractError("'version' muss ein Text sein.")
        try:
            return self.registry.get(template_id, version)
        except TemplateNotFoundError as exc:
            raise ContractError(str(exc), status=404, code="unknown_template") from exc

    def design(self, value: object) -> DesignProfile:
        """Design profile by id; the first profile when none is given."""
        if value is None:
            return next(iter(self.designs.values()))
        if not isinstance(value, str) or value not in self.designs:
            raise ContractError(
                f"'design' muss einer der Werte {', '.join(self.designs)} sein.",
                code="unknown_design",
            )
        return self.designs[value]


@lru_cache(maxsize=1)
def default_catalogue() -> TemplateCatalogue:
    """Built-in templates with the neutral design (created once)."""
    return TemplateCatalogue()


def available_formats() -> dict[str, bool]:
    """Which formats this installation can render (``pdf`` needs reportlab)."""
    return {"docx": True, "pdf": importlib.util.find_spec("reportlab") is not None, "html": True}


def _summary(template: ReportTemplate, registry: TemplateRegistry) -> dict[str, object]:
    return {
        "id": template.id,
        "version": template.version,
        "title": template.title,
        "description": template.description,
        "status": template.status,
        "kind": "docx" if template.docx is not None else "structured",
        "formats": list(template.formats),
        "fingerprint": template.fingerprint,
        "versions": list(registry.versions(template.id)),
    }


def template_list(catalogue: TemplateCatalogue) -> dict[str, object]:
    """``GET /templates``."""
    return {
        "contract": CONTRACT,
        "templates": [_summary(t, catalogue.registry) for t in catalogue.registry.latest()],
        "designs": [design.to_dict() for design in catalogue.designs.values()],
        "formats": available_formats(),
    }


def template_detail(
    catalogue: TemplateCatalogue, template_id: str, version: object = None
) -> dict[str, object]:
    """``GET /templates/{id}``: data contract, sample data, text blocks and conditions."""
    template = catalogue.template(template_id, version)
    blocks = [
        {
            "id": block.id,
            "title": block.title,
            "text": block.text,
            "required": block.required,
            "legal_basis": block.legal_basis,
            "condition": plain(block.condition),
        }
        for block in template.text_blocks
    ]
    return {
        "contract": CONTRACT,
        **_summary(template, catalogue.registry),
        "schema": plain(template.schema),
        "sample": plain(template.sample),
        "conditions": plain(template.conditions),
        "text_blocks": blocks,
    }


def _request(
    catalogue: TemplateCatalogue, template_id: str, payload: object
) -> tuple[ReportTemplate, Mapping[str, object]]:
    body = rest.json_object(payload, "Anfrage", error=ContractError)
    template = catalogue.template(template_id, body.get("version"))
    if "data" not in body:
        raise ContractError("'data' fehlt (Daten gemäß Datenvertrag der Vorlage).")
    return template, body


def _paragraph_preview(content: bytes, title: str) -> str:
    from ..templates.docx_template import docx_paragraphs

    lines = "".join(f"<p>{escape(text)}</p>" for text in docx_paragraphs(content) if text.strip())
    return (
        '<!DOCTYPE html>\n<html lang="de"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy"'
        " content=\"default-src 'none'; style-src 'unsafe-inline'\">"
        f"<title>{escape(title)}</title></head><body><main>{lines}</main></body></html>\n"
    )


def template_preview(
    catalogue: TemplateCatalogue, template_id: str, payload: object
) -> dict[str, object]:
    """``POST /templates/{id}/preview``: data check, HTML preview and used text blocks.

    Invalid data are no error here: ``valid`` is false and ``issues`` lists them.
    """
    template, body = _request(catalogue, template_id, payload)
    design = catalogue.design(body.get("design"))
    result: dict[str, object] = {
        "contract": CONTRACT,
        "template": {
            "id": template.id,
            "version": template.version,
            "fingerprint": template.fingerprint,
        },
        "valid": True,
        "issues": [],
        "html": None,
        "text_blocks": [],
        "data_sha256": None,
    }
    try:
        if template.docx is None:
            document = resolve(template, body["data"])
            html = render_html(document, design)
            result.update(
                html=html, text_blocks=list(document.text_blocks), data_sha256=document.data_sha256
            )
        else:
            rendered = render(template, body["data"], "docx")
            html = _paragraph_preview(rendered.content, template.title)
            result.update(html=html, data_sha256=rendered.data_sha256)
    except TemplateDataError as exc:
        result.update(valid=False, issues=[issue.to_dict() for issue in exc.issues])
    except RenderDependencyError as exc:
        raise ContractError(str(exc), status=501, code="docx_unavailable") from exc
    except RenderLimitError as exc:
        raise ContractError(f"Grenze überschritten: {exc}", status=413, code="too_large") from exc
    except TemplateError as exc:
        raise ContractError(f"Vorlage abgelehnt: {exc}", code="template_rejected") from exc
    return result


def document_filename(value: object, fallback: str, extension: str) -> str:
    """Safe download name with the format's extension."""
    if value is None:
        value = fallback
    if not isinstance(value, str):
        raise ContractError("'filename' muss ein Text sein.")
    stem = _FILENAME.sub("_", value.strip()).strip(" .")[:100]
    if stem.lower().endswith(f".{extension}"):
        stem = stem[: -len(extension) - 1].rstrip(" .")
    return f"{stem or 'bericht'}.{extension}"


def template_render(
    catalogue: TemplateCatalogue, template_id: str, payload: object
) -> tuple[bytes, str, str, dict[str, str]]:
    """``POST /templates/{id}/render``: file, download name, media type, provenance headers."""
    template, body = _request(catalogue, template_id, payload)
    output = rest.choice(body.get("format"), "format", tuple(template.formats), error=ContractError)
    design = catalogue.design(body.get("design"))
    try:
        result = render(template, body["data"], output, design)
    except TemplateDataError as exc:
        raise DataContractError(exc) from exc
    except RenderDependencyError as exc:
        raise ContractError(str(exc), status=501, code=f"{output}_unavailable") from exc
    except RenderLimitError as exc:
        raise ContractError(f"Grenze überschritten: {exc}", status=413, code="too_large") from exc
    except TemplateError as exc:
        raise ContractError(f"Vorlage abgelehnt: {exc}", code="template_rejected") from exc
    headers = {
        "X-Template-Id": result.template_id,
        "X-Template-Version": result.template_version,
        "X-Template-Fingerprint": result.template_fingerprint,
        "X-Data-SHA256": result.data_sha256,
    }
    filename = document_filename(body.get("filename"), template.id, output)
    return result.content, filename, result.media_type, headers
