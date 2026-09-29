"""Registry of tools: the minimum set plus the full catalog of the runner image."""

from __future__ import annotations

from dataclasses import dataclass, field

from .katalog_voll import DOC_TOOLS, PYTHON_TOOLS, SECURITY_TOOLS
from .katalog_web import GUI_TOOLS, HOOK_TOOLS, JS_TOOLS, STRUCTURE_TOOLS
from .modell import Cost, Tool

MINIMUM_TOOLS: tuple[Tool, ...] = (
    Tool(
        name="ruff",
        area="python",
        # S- (Sicherheit, ersetzt bandit) und D-Regeln (Docstrings) zusätzlich zur Projektkonfiguration.
        command=("ruff", "check", ".", "--output-format=json", "--exit-zero", "--extend-select", "S,D"),
        parser="ruff-json",
        fix_command=("ruff", "check", ".", "--fix", "--exit-zero"),
        install="pip: ruff (gepinnt im Runner-Image)",
        version_command=("ruff", "--version"),
        applies_to=("*.py",),
    ),
    Tool(
        name="mypy",
        area="python",
        command=("mypy", ".", "--no-color-output", "--no-error-summary"),
        parser="mypy-text",
        cost=Cost(cpus=2, minutes=3),
        install="pip: mypy",
        version_command=("mypy", "--version"),
        applies_to=("*.py",),
    ),
    Tool(
        name="pytest",
        area="python",
        command=("python", "-m", "pytest", "-q", "--junitxml={ausgabe}"),
        parser="junit-xml",
        cost=Cost(cpus=4, minutes=10),
        install="pip: pytest",
        version_command=("python", "-m", "pytest", "--version"),
        applies_to=("*.py",),
        output_file="pytest.xml",
        success_codes=(0, 1, 5),
    ),
    Tool(
        name="gitleaks",
        area="sicherheit",
        command=(
            "gitleaks",
            "detect",
            "--no-banner",
            "--redact",
            "--report-format",
            "json",
            "--report-path",
            "{ausgabe}",
            "--exit-code",
            "0",
        ),
        parser="gitleaks-json",
        install="Binärdatei: gitleaks (gepinnte Version im Runner-Image)",
        version_command=("gitleaks", "version"),
        output_file="gitleaks.json",
    ),
    Tool(
        name="eslint",
        area="js",
        command=("npx", "--no-install", "eslint", ".", "-f", "json"),
        parser="eslint-json",
        fix_command=("npx", "--no-install", "eslint", ".", "--fix"),
        cost=Cost(cpus=2, minutes=3),
        install="npm: eslint (aus dem Projekt, kein globaler Download)",
        version_command=("npx", "--no-install", "eslint", "--version"),
        applies_to=("*.js", "*.ts", "*.vue", "*.tsx"),
    ),
    Tool(
        name="zizmor",
        area="sicherheit",
        command=("zizmor", "--format", "sarif", "--no-progress", ".github/workflows"),
        parser="sarif",
        install="pip: zizmor (MIT)",
        version_command=("zizmor", "--version"),
        applies_to=(".github/workflows/*",),
        success_codes=(0, 1, 10, 11, 12, 13, 14),
    ),
    Tool(
        name="actionlint",
        area="sicherheit",
        command=("actionlint", "-format", "{{json .}}"),
        parser="actionlint-json",
        install="Binärdatei: actionlint (MIT)",
        version_command=("actionlint", "-version"),
        applies_to=(".github/workflows/*",),
    ),
    Tool(
        name="codegate",
        area="struktur",
        command=("auditcore-codegate", "check", "--output", "{ausgabe}"),
        parser="codegate-json",
        cost=Cost(cpus=2, minutes=3),
        install="auditcore (Plattform) – nur in auditcore-Repositories",
        version_command=("auditcore-codegate", "--help"),
        output_file="codegate.json",
    ),
)


FULL_TOOLS: tuple[Tool, ...] = (
    *MINIMUM_TOOLS,
    *PYTHON_TOOLS,
    *SECURITY_TOOLS,
    *DOC_TOOLS,
    *STRUCTURE_TOOLS,
    *JS_TOOLS,
    *GUI_TOOLS,
    *HOOK_TOOLS,
)


@dataclass
class Registry:
    tools: dict[str, Tool] = field(default_factory=lambda: {t.name: t for t in FULL_TOOLS})

    def register(self, tool: Tool) -> None:
        """Add or replace a tool, e.g. an external orchestrator with parser ``sarif``."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self.tools:
            return Tool(name=name, area="custom", command=(), parser="keine", success_codes=(0,))
        return self.tools[name]

    def names(self) -> list[str]:
        return sorted(self.tools)


def external_orchestrator(name: str, command: tuple[str, ...], output_file: str) -> Tool:
    """An aggregating linter (MegaLinter, Trunk, …) that writes one SARIF file."""
    return Tool(
        name=name,
        area="extern",
        command=command,
        parser="sarif",
        output_file=output_file,
        cost=Cost(cpus=4, minutes=15),
        install="extern",
    )
