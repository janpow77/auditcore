"""Versioned package templates loaded from installed package resources."""

from importlib.resources import files

from auditcore.tools.common import digest

TEMPLATE_VERSION = "1.0"


def render_template(template_name: str, **values: str) -> str:
    """Render a known template with validated deployment-profile values."""
    if template_name not in {"control", "systemd", "postinst", "prerm", "postrm"}:
        raise ValueError("Unknown deployment template")
    template = (
        files("auditcore.tools.deployer").joinpath(f"templates/{template_name}.tmpl").read_text()
    )
    return template.format_map(values)


def template_manifest() -> dict[str, str]:
    """Record exact template versions and hashes in build manifests."""
    result = {"version": TEMPLATE_VERSION}
    for name in ("control", "systemd", "postinst", "prerm", "postrm"):
        content = files("auditcore.tools.deployer").joinpath(f"templates/{name}.tmpl").read_text()
        result[name] = digest(content)
    return result
