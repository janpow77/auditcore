"""The full tool catalog (PR 2): every tool pinned in the runner image.

Commands run in the repository root inside the image. Tools that need the
project's own dependencies (tsc, vitest, Playwright, pytest plugins) use the
project installation first and fall back to the copy in the image. Tools with
``network=True`` fetch vulnerability databases or check links online; all
others run with ``--network none``.
"""

from __future__ import annotations

from .modell import Cost, Tool

PY = ("*.py",)
JS = ("*.js", "*.ts", "*.tsx", "*.vue", "*.mjs", "*.cjs")
TEXT = ("*.py", "*.md", "*.rst", "*.txt", "*.js", "*.ts", "*.vue", "*.toml", "*.yml", "*.yaml")
SKIP = ".git,node_modules,.venv,.auditcore-runner,*.lock,package-lock.json,*.svg,*.png"
IMAGE = "Runner-Image (gepinnt, siehe data/werkzeuge/)"


def _pytest_variant(name: str, area: str, extra: tuple[str, ...], cost: Cost, install: str) -> Tool:
    return Tool(
        name=name,
        area=area,
        command=("python", "-m", "pytest", "-q", *extra, "--junitxml={ausgabe}"),
        parser="junit-xml",
        cost=cost,
        install=install,
        version_command=("python", "-m", "pytest", "--version"),
        applies_to=PY,
        output_file=f"{name}.xml",
        success_codes=(0, 1, 5),
    )


def pytest_split(group: int, splits: int) -> Tool:
    """One group of a test suite split by recorded durations (pytest-split)."""
    return _pytest_variant(
        f"pytest-split-{group}v{splits}",
        "python",
        ("--splits", str(splits), "--group", str(group)),
        Cost(cpus=4, minutes=10),
        "pip: pytest-split (im Projekt)",
    )


PYTHON_TOOLS: tuple[Tool, ...] = (
    Tool(
        name="pyrefly",
        area="python",
        command=("pyrefly", "check", "--output-format", "json", "--summary=none"),
        parser="pyrefly-json",
        cost=Cost(cpus=2, minutes=2),
        install=f"pip: pyrefly – {IMAGE}",
        version_command=("pyrefly", "--version"),
        applies_to=PY,
    ),
    Tool(
        name="vulture",
        area="python",
        command=("vulture", ".", "--exclude", ".venv,node_modules,.auditcore-runner,build,dist"),
        parser="vulture-text",
        install=f"pip: vulture – {IMAGE}",
        version_command=("vulture", "--version"),
        applies_to=PY,
        success_codes=(0, 1, 3),
    ),
    Tool(
        name="deptry",
        area="python",
        command=("deptry", ".", "--json-output", "{ausgabe}"),
        parser="deptry-json",
        install=f"pip: deptry – {IMAGE}",
        version_command=("deptry", "--version"),
        applies_to=("pyproject.toml",),
        output_file="deptry.json",
    ),
    Tool(
        name="import-linter",
        area="struktur",
        command=("lint-imports", "--no-cache"),
        parser="import-linter-text",
        install=f"pip: import-linter – {IMAGE}",
        version_command=("uv", "tool", "list"),
        applies_to=(".importlinter", "setup.cfg", "pyproject.toml"),
    ),
    Tool(
        name="mutmut",
        area="python",
        command=("sh", "-c", "mutmut run --max-children 2 >/dev/null 2>&1; mutmut results"),
        parser="mutmut-text",
        cost=Cost(cpus=4, minutes=60),
        install=f"pip: mutmut – {IMAGE}; Quellpfade unter [tool.mutmut] im Projekt",
        applies_to=PY,
        success_codes=(0, 1, 2),
    ),
    Tool(
        name="diff-cover",
        area="python",
        command=("diff-cover", "coverage.xml", "--compare-branch", "origin/main", "--json-report", "{ausgabe}"),
        parser="diff-cover-json",
        install=f"pip: diff-cover – {IMAGE}; erwartet coverage.xml aus dem Testlauf",
        version_command=("diff-cover", "--version"),
        applies_to=("coverage.xml",),
        output_file="diff-cover.json",
    ),
    _pytest_variant(
        "pytest-testmon", "python", ("--testmon",), Cost(cpus=2, minutes=5), "pip: pytest-testmon (im Projekt)"
    ),
    pytest_split(1, 2),
    pytest_split(2, 2),
    _pytest_variant(
        "pytest-gpu", "gpu", ("-m", "gpu"), Cost(cpus=4, minutes=20, gpu=True), "pip: pytest; GPU über CDI"
    ),
)

SECURITY_TOOLS: tuple[Tool, ...] = (
    Tool(
        name="betterleaks",
        area="sicherheit",
        command=(
            "betterleaks",
            "dir",
            ".",
            "--no-banner",
            "--redact",
            "--report-format",
            "json",
            "--report-path",
            "{ausgabe}",
            "--exit-code",
            "0",
        ),
        parser="betterleaks-json",
        install=f"Binärdatei: betterleaks (zum Vergleich neben gitleaks) – {IMAGE}",
        version_command=("betterleaks", "version"),
        output_file="betterleaks.json",
    ),
    Tool(
        name="opengrep",
        area="sicherheit",
        command=(
            "opengrep",
            "scan",
            "--config",
            ".opengrep",
            "--sarif-output={ausgabe}",
            "--disable-version-check",
            "--quiet",
            ".",
        ),
        parser="sarif",
        cost=Cost(cpus=2, minutes=5),
        install=f"Binärdatei: Opengrep (LGPL-2.1, separates Programm); Regeln aus .opengrep/ im Projekt – {IMAGE}",
        version_command=("opengrep", "--version"),
        applies_to=(".opengrep/*",),
        output_file="opengrep.sarif",
    ),
    Tool(
        name="osv-scanner",
        area="sicherheit",
        command=("osv-scanner", "scan", "source", "-r", ".", "--format", "sarif", "--output", "{ausgabe}"),
        parser="sarif",
        install=f"Binärdatei: osv-scanner v2 – {IMAGE}",
        version_command=("osv-scanner", "--version"),
        output_file="osv-scanner.sarif",
        success_codes=(0, 1, 128),
        network=True,
    ),
    Tool(
        name="grype",
        area="sicherheit",
        command=("grype", "dir:.", "-o", "sarif", "--file", "{ausgabe}"),
        parser="sarif",
        cost=Cost(cpus=2, minutes=5),
        install=f"Binärdatei: grype – {IMAGE}",
        version_command=("grype", "--version"),
        output_file="grype.sarif",
        network=True,
    ),
    Tool(
        name="syft",
        area="sicherheit",
        command=("syft", "dir:.", "-o", "spdx-json={ausgabe}"),
        parser="keine",
        install=f"Binärdatei: syft (SBOM als Artefakt, keine Befunde) – {IMAGE}",
        version_command=("syft", "--version"),
        output_file="sbom.spdx.json",
        success_codes=(0,),
    ),
    Tool(
        name="trivy",
        area="sicherheit",
        command=(
            "trivy",
            "fs",
            "--scanners",
            "vuln,misconfig",
            "--format",
            "sarif",
            "--output",
            "{ausgabe}",
            "--quiet",
            ".",
        ),
        parser="sarif",
        cost=Cost(cpus=2, minutes=5),
        install=f"Binärdatei: trivy, nur per SHA-256 gepinnt (GHSA-69fq-xp46-6x23) – {IMAGE}",
        version_command=("trivy", "--version"),
        output_file="trivy.sarif",
        network=True,
    ),
)

DOC_TOOLS: tuple[Tool, ...] = (
    Tool(
        name="codespell",
        area="doku",
        command=("codespell", "--skip", SKIP),
        parser="codespell-text",
        fix_command=("codespell", "--skip", SKIP, "--write-changes"),
        install=f"pip: codespell (GPL-2.0, separates Programm) – {IMAGE}",
        version_command=("codespell", "--version"),
        applies_to=TEXT,
        success_codes=(0, 65),
        stage="autofix",
    ),
    Tool(
        name="typos",
        area="doku",
        command=("typos", "--format", "json"),
        parser="typos-json",
        fix_command=("typos", "--write-changes"),
        install=f"pip: typos – {IMAGE}",
        version_command=("typos", "--version"),
        applies_to=TEXT,
        success_codes=(0, 2),
        stage="autofix",
    ),
    Tool(
        name="markdownlint",
        area="doku",
        command=("markdownlint", "--json", "--output", "{ausgabe}", "--ignore", "node_modules", "."),
        parser="markdownlint-json",
        fix_command=("markdownlint", "--fix", "--ignore", "node_modules", "."),
        install=f"npm: markdownlint-cli – {IMAGE}",
        version_command=("markdownlint", "--version"),
        applies_to=("*.md",),
        output_file="markdownlint.json",
        stage="autofix",
    ),
    Tool(
        name="lychee",
        area="doku",
        command=("lychee", "--offline", "--format", "json", "--no-progress", "--output", "{ausgabe}", "."),
        parser="lychee-json",
        install=f"Binärdatei: lychee (nur lokale Links) – {IMAGE}",
        version_command=("lychee", "--version"),
        applies_to=("*.md", "*.html", "*.rst"),
        output_file="lychee.json",
        success_codes=(0, 2),
    ),
    Tool(
        name="lychee-online",
        area="doku",
        command=("lychee", "--format", "json", "--no-progress", "--output", "{ausgabe}", "."),
        parser="lychee-json",
        cost=Cost(cpus=1, minutes=5),
        install=f"Binärdatei: lychee (auch externe Links) – {IMAGE}",
        version_command=("lychee", "--version"),
        applies_to=("*.md", "*.html", "*.rst"),
        output_file="lychee-online.json",
        success_codes=(0, 2),
        network=True,
    ),
)
