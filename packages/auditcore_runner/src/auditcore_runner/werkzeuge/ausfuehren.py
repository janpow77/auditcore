"""Run a check profile locally – in the runner image or on the host – with a per-tool cache.

Cache key per tool: ``(tool, version, config hash, Git content of the checked
path)``. The content hash covers the committed tree of that path plus
uncommitted changes and untracked files below it, so unchanged packages are
never checked twice and nothing is sent to GitHub for them. The tools' own
caches (ruff, mypy, pytest) live in a shared Docker volume.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field, replace
from fnmatch import fnmatch
from pathlib import Path

from ..profile import state_dir
from .befunde import Finding, deduplicate, relative_to
from .katalog import Registry
from .modell import CUSTOM_AREA, EXIT_CODE_PARSER, REPO_FILE, CheckProfile, Tool
from .parser import NOTHING_CHECKED, PARSERS

CONFIG_FILES = (
    "pyproject.toml",
    "setup.cfg",
    "ruff.toml",
    ".ruff.toml",
    "mypy.ini",
    "pytest.ini",
    "eslint.config.js",
    "eslint.config.mjs",
    ".eslintrc.json",
    "package.json",
    ".gitleaks.toml",
    ".auditcore-runner.toml",
    "tsconfig.json",
    ".importlinter",
    "sgconfig.yml",
    "_typos.toml",
    ".markdownlint.json",
    ".stylelintrc.json",
    "knip.json",
    ".jscpd.json",
    ".size-limit.json",
    "lighthouserc.json",
    "playwright.config.ts",
    ".pre-commit-config.yaml",
)
TOOL_CACHE_VOLUME = "auditcore-runner-werkzeug-cache"
NOTHING_CHECKED_STATUS = "nichts_geprueft"
# Statuses that mean the tool did not check the code: the overall result is red.
RED_STATUSES = ("fehler", "fehlt", "zeitlimit", "unlesbar", "unbekannt", NOTHING_CHECKED_STATUS)
COMMAND_NOT_FOUND = 127  # shell and ``docker run`` when the program is missing


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60, check=False)
    return result.stdout if result.returncode == 0 else ""


def content_key(path: Path) -> str:
    """Committed tree of ``path`` + uncommitted diff + untracked files below it."""
    digest = hashlib.sha256(_git(path, "rev-parse", "HEAD:./").encode())
    digest.update(_git(path, "diff", "HEAD", "--binary", "--", ".").encode())
    for name in sorted(_git(path, "ls-files", "--others", "--exclude-standard", "--", ".").splitlines()):
        file = path / name
        digest.update(name.encode())
        if file.is_file():
            digest.update(hashlib.sha256(file.read_bytes()).digest())
    return digest.hexdigest()[:32]


def config_hash(path: Path, tool: Tool) -> str:
    """Hash of the tool definition and the configuration files that influence it."""
    digest = hashlib.sha256(json.dumps([tool.command, tool.parser, tool.allow_empty]).encode())
    for directory in (path, *path.parents):
        for name in CONFIG_FILES:
            file = directory / name
            if file.is_file():
                digest.update(name.encode() + hashlib.sha256(file.read_bytes()).digest())
        if (directory / ".git").exists():
            break
    return digest.hexdigest()[:16]


@dataclass
class ToolResult:
    tool: str
    status: str
    seconds: float
    findings: list[Finding] = field(default_factory=list)
    message: str = ""
    cached: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "werkzeug": self.tool,
            "status": self.status,
            "sekunden": round(self.seconds, 1),
            "befunde": len(self.findings),
            "meldung": self.message,
            "aus_cache": self.cached,
        }


@dataclass
class Runner:
    """Executes tools inside ``image`` (Docker, no network) or directly on the host."""

    root: Path
    image: str = ""

    def command(self, argv: list[str], network: bool = False) -> list[str]:
        """Container call; without ``network`` the tool runs fully offline."""
        if not self.image:
            return argv
        return [
            "docker",
            "run",
            "--rm",
            *(() if network else ("--network", "none")),
            "--cap-drop",
            "ALL",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{self.root}:/work",
            "-w",
            "/work",
            "-v",
            f"{TOOL_CACHE_VOLUME}:/cache",
            "-e",
            "XDG_CACHE_HOME=/cache",
            "-e",
            "RUFF_CACHE_DIR=/cache/ruff",
            "-e",
            "MYPY_CACHE_DIR=/cache/mypy",
            "--entrypoint",
            "",
            self.image,
            *argv,
        ]

    def output_prefix(self) -> str:
        return "/work/.auditcore-runner" if self.image else str(self.root / ".auditcore-runner")

    def version(self, tool: Tool) -> str:
        if not tool.version_command:
            return ""
        try:
            result = subprocess.run(
                self.command(list(tool.version_command), tool.network),
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        lines = result.stdout.strip().splitlines()
        return lines[0] if result.returncode == 0 and lines else ""


def _execute(runner: Runner, tool: Tool, timeout: int) -> ToolResult:
    work = runner.root / ".auditcore-runner"
    work.mkdir(exist_ok=True)
    (work / ".gitignore").write_text("*\n", encoding="utf-8")
    output = work / tool.output_file if tool.output_file else None
    if output is not None:
        # A report left over from an earlier run must never stand in for this one.
        output.unlink(missing_ok=True)
    target = f"{runner.output_prefix()}/{tool.output_file}"
    argv = [part.replace("{ausgabe}", target) for part in tool.command]
    started = time.monotonic()
    try:
        result = subprocess.run(
            runner.command(argv, tool.network),
            cwd=runner.root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return ToolResult(tool.name, "fehlt", 0.0, message=f"{argv[0]} nicht installiert")
    except subprocess.TimeoutExpired:
        return ToolResult(tool.name, "zeitlimit", float(timeout), message=f"nach {timeout} s abgebrochen")
    seconds = time.monotonic() - started
    if result.returncode == COMMAND_NOT_FOUND and COMMAND_NOT_FOUND not in tool.success_codes:
        return ToolResult(
            tool.name, "fehlt", seconds, message=f"{argv[0]} im Image bzw. auf dem Rechner nicht gefunden"
        )
    if tool.parser == EXIT_CODE_PARSER:
        return ToolResult(tool.name, "ok", seconds, _exit_code_findings(tool, result))
    if result.returncode not in tool.success_codes:
        return ToolResult(tool.name, "fehler", seconds, message=result.stderr.strip()[-400:])
    raw = output.read_text(encoding="utf-8") if output and output.exists() else result.stdout
    try:
        findings = PARSERS[tool.parser](raw)
    except (ValueError, KeyError) as error:
        return ToolResult(tool.name, "unlesbar", seconds, message=str(error)[:300])
    local = relative_to(_named(tool, findings), (str(runner.root), "/work"))
    checked = [_scan_root_relative(f, runner.root) for f in local]
    try:
        reason = None if tool.allow_empty or tool.parser not in NOTHING_CHECKED else NOTHING_CHECKED[tool.parser](raw)
    except ValueError as error:
        return ToolResult(tool.name, "unlesbar", seconds, message=str(error)[:300])
    if reason is not None:
        message = f"nichts geprüft – {reason}"[:400]
        empty = Finding(tool=tool.name, rule=NOTHING_CHECKED_STATUS, path=REPO_FILE, line=0, message=message)
        return ToolResult(tool.name, NOTHING_CHECKED_STATUS, seconds, [*checked, empty], message)
    return ToolResult(tool.name, "ok", seconds, checked)


def _exit_code_findings(tool: Tool, result: subprocess.CompletedProcess[str]) -> list[Finding]:
    """Generic tools without report: a failing exit code is one finding with the tail of the output."""
    if result.returncode in tool.success_codes:
        return []
    output = (result.stderr.strip() or result.stdout.strip())[-400:]
    message = f"{' '.join(tool.command)} endete mit Exitcode {result.returncode}" + (f": {output}" if output else "")
    return [Finding(tool=tool.name, rule="exitcode", path=REPO_FILE, line=0, message=message)]


def _named(tool: Tool, findings: list[Finding]) -> list[Finding]:
    """SARIF names its producer freely ("Opengrep OSS"); catalog tools report under their catalog name."""
    if tool.parser != "sarif" or tool.area == "extern":
        return findings
    return [replace(f, tool=tool.name) for f in findings]


def _scan_root_relative(finding: Finding, root: Path) -> Finding:
    """Scanners such as grype report ``/datei`` relative to the scan root."""
    path = finding.path
    if path.startswith("/") and (root / path.lstrip("/")).exists():
        return replace(finding, path=path.lstrip("/"))
    return finding


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "auditcore-runner" / "ergebnisse"


def cache_key(tool: Tool, version: str, runner: Runner, content: str) -> str:
    identity = json.dumps([tool.name, version, config_hash(runner.root, tool), content, runner.image])
    return hashlib.sha256(identity.encode()).hexdigest()[:40]


def _read_cache(key: str) -> ToolResult | None:
    path = cache_dir() / f"{key}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    items = [Finding(**item) for item in data.get("findings", []) if isinstance(item, dict)]
    return ToolResult(str(data.get("tool")), "ok", 0.0, items, "", True)


def _write_cache(key: str, result: ToolResult) -> None:
    directory = cache_dir()
    directory.mkdir(parents=True, exist_ok=True)
    document = {"tool": result.tool, "findings": [f.__dict__ for f in result.findings]}
    handle, temporary = tempfile.mkstemp(dir=directory)
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        json.dump(document, stream)
    os.replace(temporary, directory / f"{key}.json")


def run_tool(runner: Runner, tool: Tool, timeout: int, content: str, use_cache: bool = True) -> ToolResult:
    """One tool, from cache when its inputs are unchanged.

    Tools running a repository ``befehl`` are never cached: such commands may
    depend on state outside Git (``.env``, running containers), which the key
    does not cover.
    """
    use_cache = use_cache and tool.cacheable
    key = cache_key(tool, runner.version(tool), runner, content)
    cached = _read_cache(key) if use_cache else None
    if cached is not None:
        return cached
    result = _execute(runner, tool, timeout)
    if result.status == "ok":
        _write_cache(key, result)
    return result


def fix_order(registry: Registry, profile: CheckProfile, extra: tuple[Tool, ...] = ()) -> list[Tool]:
    """Stufen ohne LLM: erst Autofixer der Werkzeuge, dann Codemods (Repo-Regeln), dann wird geprüft."""
    tools = [profile.configured_tool(registry.get(name)) for name in profile.ordered_tools()] + list(extra)
    fixers = [t for t in tools if t.can_fix]
    return [t for t in fixers if t.stage != "codemod"] + [t for t in fixers if t.stage == "codemod"]


def run_fixes(runner: Runner, registry: Registry, profile: CheckProfile, extra: tuple[Tool, ...] = ()) -> list[str]:
    """Autofix first, then codemods – no LLM involved; returns the tools that ran a fixer."""
    fixed = []
    for tool in fix_order(registry, profile, extra):
        subprocess.run(
            runner.command(list(tool.fix_command), tool.network),
            cwd=runner.root,
            capture_output=True,
            timeout=profile.setting(tool.name).timeout_seconds,
            check=False,
        )
        fixed.append(tool.name)
    return fixed


def applies(tool: Tool, files: list[str]) -> bool:
    """A tool with ``applies_to`` runs only if a tracked file matches (path or file name)."""
    if not tool.applies_to or not files:
        return True
    return any(fnmatch(f, p) or fnmatch(f.rsplit("/", 1)[-1], p) for f in files for p in tool.applies_to)


def _check(runner: Runner, tool: Tool, timeout: int, content: str, files: list[str], use_cache: bool) -> ToolResult:
    if tool.area == CUSTOM_AREA and not tool.command:
        return ToolResult(
            tool.name,
            "unbekannt",
            0.0,
            message=f"nicht im Katalog; eigenes Werkzeug braucht befehl in {REPO_FILE}",
        )
    if not applies(tool, files):
        return ToolResult(tool.name, "entfaellt", 0.0, message="keine passenden Dateien")
    return run_tool(runner, tool, timeout, content, use_cache)


def run_profile(runner: Runner, registry: Registry, profile: CheckProfile, use_cache: bool = True) -> dict[str, object]:
    """Run all enabled checking tools of a profile; returns the result document."""
    content = content_key(runner.root)
    files = _git(runner.root, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    configured = (profile.configured_tool(registry.get(n)) for n in profile.ordered_tools())
    # Catalog tools without command only fix (prek); unknown tools without command are reported.
    tools = [t for t in configured if t.command or t.area == CUSTOM_AREA]
    results = [
        _check(runner, tool, profile.setting(tool.name).timeout_seconds, content, files, use_cache) for tool in tools
    ]
    findings = deduplicate(f for r in results for f in r.findings)
    problems = [f"{r.tool}: {r.message or r.status}" for r in results if r.status in RED_STATUSES]
    return {
        "schema": "auditcore-runner/ergebnis/1",
        "profil": profile.name,
        "pfad": str(runner.root),
        "inhalt": content,
        "gesamt": "rot" if problems or findings else "gruen",
        "probleme": problems,
        "werkzeuge": [r.as_dict() for r in results],
        "befunde": [f.as_dict() for f in findings],
    }


def last_result_path() -> Path:
    return state_dir() / "letztes-ergebnis.json"
