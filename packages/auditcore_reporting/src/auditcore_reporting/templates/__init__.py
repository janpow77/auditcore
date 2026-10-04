"""Versioned report templates: data contract, text blocks, DOCX/PDF/HTML rendering.

A template is a JSON definition (``define_template``) with a JSON-Schema data
contract, named conditions, text blocks (Textbausteine) and either a block
list (renders to DOCX, PDF and HTML) or a Word file with placeholders and
control tags (renders to DOCX). Rendering is deterministic: identical
template, data and design profile give identical bytes. DOCX output and
HTML need only the standard library; filling Word templates needs the
extra ``docx`` (defusedxml), PDF the extra ``pdf`` (reportlab).
"""

from __future__ import annotations

from .definition import define_template
from .design import NEUTRAL_DESIGN, DesignProfile, design_from_dict
from .errors import (
    Issue,
    RenderDependencyError,
    RenderLimitError,
    TemplateDataError,
    TemplateError,
    TemplateNotFoundError,
    UnsafeDocumentError,
)
from .model import FORMATS, ReportTemplate, TextBlock
from .options import RenderOptions
from .registry import TemplateRegistry, builtin_registry
from .render import MEDIA_TYPES, RenderResult, render
from .resolve import ResolvedDocument, ResolveLimits, resolve

__all__ = [
    "FORMATS",
    "MEDIA_TYPES",
    "NEUTRAL_DESIGN",
    "DesignProfile",
    "Issue",
    "RenderDependencyError",
    "RenderLimitError",
    "RenderOptions",
    "RenderResult",
    "ReportTemplate",
    "ResolveLimits",
    "ResolvedDocument",
    "TemplateDataError",
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateRegistry",
    "TextBlock",
    "UnsafeDocumentError",
    "builtin_registry",
    "define_template",
    "design_from_dict",
    "render",
    "resolve",
]
