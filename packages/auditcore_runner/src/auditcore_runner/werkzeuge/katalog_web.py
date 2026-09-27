"""Full catalog, part two: structure, JavaScript/TypeScript, GUI and pre-commit hooks.

GUI checks (Playwright screenshots, axe, Lighthouse CI) run the project's own
scenarios and configuration; the package ships no scenarios of its own.
"""

from __future__ import annotations

from .katalog_voll import IMAGE, JS
from .modell import Cost, Tool

NPX = ("npx", "--no-install")
STYLES = ("*.css", "*.scss", "*.vue")
PLAYWRIGHT = "npx playwright test --reporter=junit"

STRUCTURE_TOOLS: tuple[Tool, ...] = (
    Tool(
        name="jscpd",
        area="struktur",
        command=(
            "sh",
            "-c",
            "jscpd . --silent --reporters json --gitignore --output {ausgabe}.d"
            " && mv {ausgabe}.d/jscpd-report.json {ausgabe}",
        ),
        parser="jscpd-json",
        cost=Cost(cpus=2, minutes=3),
        install=f"npm: jscpd – {IMAGE}",
        version_command=("jscpd", "--version"),
        output_file="jscpd.json",
    ),
    Tool(
        name="ast-grep",
        area="struktur",
        command=("ast-grep", "scan", "--json=stream"),
        parser="ast-grep-json",
        fix_command=("ast-grep", "scan", "--update-all"),
        install=f"pip: ast-grep-cli; Regeln aus sgconfig.yml im Projekt – {IMAGE}",
        version_command=("ast-grep", "--version"),
        applies_to=("sgconfig.yml",),
        stage="codemod",
    ),
    Tool(
        name="knip",
        area="js",
        command=("knip", "--reporter", "json", "--no-progress"),
        parser="knip-json",
        cost=Cost(cpus=2, minutes=3),
        install=f"npm: knip (ISC) – {IMAGE}",
        version_command=("knip", "--version"),
        applies_to=("package.json",),
    ),
)

JS_TOOLS: tuple[Tool, ...] = (
    Tool(
        name="tsc",
        area="js",
        command=(*NPX, "tsc", "--noEmit", "--pretty", "false"),
        parser="tsc-text",
        cost=Cost(cpus=2, minutes=3),
        install=f"npm: typescript (Projekt, sonst {IMAGE})",
        version_command=(*NPX, "tsc", "--version"),
        applies_to=("tsconfig.json",),
        success_codes=(0, 1, 2),
    ),
    Tool(
        name="prettier",
        area="js",
        command=("sh", "-c", "prettier --check --ignore-unknown . 2>&1"),
        parser="prettier-text",
        fix_command=("prettier", "--write", "--ignore-unknown", "."),
        install=f"npm: prettier – {IMAGE}",
        version_command=("prettier", "--version"),
        applies_to=(*JS, "*.css", "*.json", "*.md"),
        stage="autofix",
    ),
    Tool(
        name="stylelint",
        area="js",
        command=("stylelint", "**/*.{css,scss,vue}", "--allow-empty-input", "-f", "json", "-o", "{ausgabe}"),
        parser="stylelint-json",
        fix_command=("stylelint", "**/*.{css,scss,vue}", "--allow-empty-input", "--fix"),
        install=f"npm: stylelint; Konfiguration im Projekt – {IMAGE}",
        version_command=("stylelint", "--version"),
        applies_to=STYLES,
        output_file="stylelint.json",
        success_codes=(0, 2),
        stage="autofix",
    ),
    Tool(
        name="vitest",
        area="js",
        command=(*NPX, "vitest", "run", "--reporter=junit", "--outputFile={ausgabe}"),
        parser="vitest-junit",
        cost=Cost(cpus=4, minutes=5),
        install=f"npm: vitest (Projekt, sonst {IMAGE})",
        version_command=(*NPX, "vitest", "--version"),
        applies_to=JS,
        output_file="vitest.xml",
    ),
    Tool(
        name="size-limit",
        area="js",
        command=(*NPX, "size-limit", "--json"),
        parser="size-limit-json",
        install="npm: size-limit und Plugin im Projekt",
        version_command=(*NPX, "size-limit", "--version"),
        applies_to=(".size-limit.json", ".size-limit.js", ".size-limit.cjs"),
    ),
)


def _playwright(name: str, extra: tuple[str, ...], cost: Cost) -> Tool:
    return Tool(
        name=name,
        area="gui",
        command=("sh", "-c", f"PLAYWRIGHT_JUNIT_OUTPUT_FILE={{ausgabe}} {PLAYWRIGHT} {' '.join(extra)}".rstrip()),
        parser=f"{name}-junit",
        cost=cost,
        install=f"npm: @playwright/test mit Chromium und Noto-Schriften – {IMAGE}",
        version_command=("playwright", "--version"),
        applies_to=("playwright.config.ts", "playwright.config.js", "playwright.config.mjs"),
        output_file=f"{name}.xml",
    )


GUI_TOOLS: tuple[Tool, ...] = (
    # Screenshot-Vergleiche (toHaveScreenshot) mit Baselines im Projekt.
    _playwright("playwright", (), Cost(cpus=4, minutes=10)),
    # Barrierefreiheit: Szenarien mit @axe-core/playwright, markiert mit @axe.
    _playwright("axe", ("--grep", "@axe"), Cost(cpus=2, minutes=5)),
    Tool(
        name="lighthouse",
        area="gui",
        command=("sh", "-c", "lhci autorun >&2; cp .lighthouseci/assertion-results.json {ausgabe}"),
        parser="lighthouse-json",
        cost=Cost(cpus=2, minutes=10),
        install=f"npm: @lhci/cli (Apache-2.0), Chromium über CHROME_PATH – {IMAGE}",
        version_command=("lhci", "--version"),
        applies_to=("lighthouserc.json", ".lighthouserc.json", "lighthouserc.js"),
        output_file="lighthouse.json",
    ),
)

HOOK_TOOLS: tuple[Tool, ...] = (
    # Nur Autofix: die pre-commit-Hooks des Projekts (prek liest .pre-commit-config.yaml).
    Tool(
        name="prek",
        area="struktur",
        command=(),
        parser="keine",
        fix_command=("prek", "run", "--all-files"),
        install=f"Binärdatei: prek – {IMAGE}",
        version_command=("prek", "--version"),
        applies_to=(".pre-commit-config.yaml",),
        stage="autofix",
        network=True,
    ),
)
