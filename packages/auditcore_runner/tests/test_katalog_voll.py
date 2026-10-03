from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from auditcore_runner.werkzeuge import aufgaben, parser
from auditcore_runner.werkzeuge.ausfuehren import Runner, applies, fix_order, run_fixes, run_profile
from auditcore_runner.werkzeuge.befunde import Finding, relative_to
from auditcore_runner.werkzeuge.katalog import FULL_TOOLS, Registry
from auditcore_runner.werkzeuge.modell import (
    AREAS,
    DEFAULT_PROFILES,
    STAGES,
    CheckProfile,
    RepoConfigError,
    Tool,
    load_codemods,
)

FIXTURES = Path(__file__).parent / "fixtures"
DATA = Path(__file__).parents[1] / "src" / "auditcore_runner" / "data" / "werkzeuge"
REQUIRED = {
    "pyrefly",
    "opengrep",
    "osv-scanner",
    "syft",
    "grype",
    "trivy",
    "vulture",
    "deptry",
    "import-linter",
    "codespell",
    "typos",
    "mutmut",
    "diff-cover",
    "pytest-testmon",
    "pytest-split-1v2",
    "jscpd",
    "ast-grep",
    "tsc",
    "prettier",
    "stylelint",
    "vitest",
    "knip",
    "size-limit",
    "playwright",
    "axe",
    "lighthouse",
    "markdownlint",
    "lychee",
    "betterleaks",
    "gitleaks",
    "prek",
}


def test_full_catalog_is_consistent() -> None:
    names = [t.name for t in FULL_TOOLS]
    assert len(names) == len(set(names)) and set(names) >= REQUIRED
    for tool in FULL_TOOLS:
        assert tool.parser in parser.PARSERS, tool.name
        assert tool.area in AREAS and tool.stage in STAGES, tool.name
        assert tool.command or tool.can_fix, tool.name
        uses_output = any("{ausgabe}" in part for part in tool.command)
        assert uses_output == bool(tool.output_file), tool.name
    assert Registry().get("pytest-gpu").cost.gpu
    assert {t.name for t in FULL_TOOLS if t.network} == {"osv-scanner", "grype", "trivy", "lychee-online", "prek"}


def test_every_profile_is_known_and_neutral() -> None:
    names = set(Registry().names())
    assert set(DEFAULT_PROFILES) == {"schnell", "pr", "voll", "gui", "sicherheit", "gpu", "fuell"}
    for profile in DEFAULT_PROFILES.values():
        assert set(profile.tools) <= names, profile.name
        gpu = [t for t in profile.tools if Registry().get(t).cost.gpu]
        assert not gpu or profile.name == "gpu"
    assert not any(Registry().get(t).network for t in DEFAULT_PROFILES["pr"].tools)


def test_image_pins_every_binary() -> None:
    pins = json.loads((DATA / "binaer.json").read_text(encoding="utf-8"))
    for entry in pins["werkzeuge"]:
        assert len(entry["sha256"]) == 64 and entry["version"] and entry["lizenz"], entry["name"]
    names = {e["name"] for e in pins["werkzeuge"]}
    assert {"opengrep", "osv-scanner", "grype", "syft", "trivy", "lychee", "betterleaks", "reviewdog", "prek"} <= names
    trivy = next(e for e in pins["werkzeuge"] if e["name"] == "trivy")
    assert "GHSA-69fq-xp46-6x23" in trivy["warnung"]
    requirements = (DATA / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert all("==" in line for line in requirements if line and not line.startswith("#"))
    node = json.loads((DATA / "package.json").read_text(encoding="utf-8"))
    assert all(v[0].isdigit() for v in node["dependencies"].values())
    assert (DATA / "package-lock.json").is_file()


@pytest.mark.parametrize(
    ("name", "fixture", "count", "first"),
    [
        ("pyrefly-json", "pyrefly.json", 2, ("pyrefly", "bad-assignment", "m.py", 2, False)),
        ("vulture-text", "vulture.txt", 12, ("vulture", "unused-import", "src/probe/domain.py", 1, False)),
        ("deptry-json", "deptry.json", 5, ("deptry", "DEP002", "pyproject.toml", 0, False)),
        (
            "import-linter-text",
            "import-linter.txt",
            1,
            ("import-linter", "vertrag-verletzt", "probe/domain.py", 4, False),
        ),
        ("codespell-text", "codespell.txt", 3, ("codespell", "schreibfehler", "docs/lies.md", 1, True)),
        ("typos-json", "typos.jsonl", 4, ("typos", "schreibfehler", "src/probe/rechnen.py", 5, True)),
        ("mutmut-text", "mutmut.txt", 2, ("mutmut", "survived", "probe/rechnen.py", 0, False)),
        (
            "diff-cover-json",
            "diff-cover.json",
            1,
            ("diff-cover", "ungetestete-aenderung", "src/probe/rechnen.py", 10, False),
        ),
        ("ast-grep-json", "ast-grep.jsonl", 2, ("ast-grep", "kein-os-import", "src/probe/domain.py", 1, True)),
        ("betterleaks-json", "betterleaks.json", 1, ("betterleaks", "aws-access-token", "config.py", 1, False)),
        ("lychee-json", "lychee.json", 1, ("lychee", "defekter-link", "docs/lies.md", 3, False)),
        ("prettier-text", "prettier.txt", 3, ("prettier", "format", "web/app.ts", 0, True)),
        ("stylelint-json", "stylelint.json", 2, ("stylelint", "color-hex-case", "/work/web/stil.css", 1, False)),
        ("markdownlint-json", "markdownlint.json", 3, ("markdownlint", "MD022", "docs/lies.md", 1, True)),
        ("jscpd-json", "jscpd.json", 1, ("jscpd", "duplikat-python", "probe/domain.py", 11, False)),
        ("knip-json", "knip.json", 3, ("knip", "unbenutzte-datei", "src/verwaist.ts", 0, False)),
        ("tsc-text", "tsc.txt", 1, ("tsc", "TS2322", "web/app.ts", 1, False)),
        ("size-limit-json", "size-limit.json", 1, ("size-limit", "groessengrenze", "package.json", 0, False)),
        (
            "lighthouse-json",
            "lighthouse.json",
            8,
            ("lighthouse", "meta-description", "http://127.0.0.1:5198/?fw=vue&fall=eingabefeld-1", 0, False),
        ),
        ("sarif", "opengrep.sarif", 1, ("Opengrep OSS", "kein-eval", "src/probe/gefahr.py", 2, False)),
        ("sarif", "osv-scanner.sarif", 3, ("osv-scanner", "CVE-2019-10906", "file:///work/requirements.txt", 0, False)),
    ],
)
def test_parsers_on_real_outputs(name: str, fixture: str, count: int, first: tuple[str, str, str, int, bool]) -> None:
    findings = parser.PARSERS[name]((FIXTURES / fixture).read_text(encoding="utf-8"))
    assert len(findings) == count
    assert (findings[0].tool, findings[0].rule, findings[0].path, findings[0].line, findings[0].fixable) == first
    assert all(f.with_fingerprint().fingerprint for f in findings)


def test_secret_values_never_reach_findings() -> None:
    raw = (FIXTURES / "betterleaks.json").read_text(encoding="utf-8")
    secret = json.loads(raw)[0]["Secret"]
    finding = parser.PARSERS["betterleaks-json"](raw)[0]
    assert secret not in finding.message


def test_junit_parsers_name_their_tool() -> None:
    xml = '<testsuite><testcase name="knopf" file="e2e/a.spec.ts"><failure message="Screenshot weicht ab"/></testcase></testsuite>'
    assert parser.PARSERS["playwright-junit"](xml)[0].tool == "playwright"
    assert parser.PARSERS["vitest-junit"](xml)[0].message == "knopf: Screenshot weicht ab"
    assert (
        parser.PARSERS["lighthouse-json"](
            '[{"name":"minScore","auditId":"color-contrast","url":"http://localhost/","passed":false,'
            '"level":"error","actual":0.8,"expected":0.9,"operator":">="}]'
        )[0].rule
        == "color-contrast"
    )


def test_relative_paths_for_host_and_container() -> None:
    findings = [
        Finding("osv-scanner", "CVE-1", "file:///work/requirements.txt", 0, "x"),
        Finding("stylelint", "r", "/repo/web/stil.css", 1, "x"),
        Finding("ruff", "F401", "src/a.py", 1, "x"),
    ]
    assert [f.path for f in relative_to(findings, ("/repo", "/work"))] == [
        "requirements.txt",
        "web/stil.css",
        "src/a.py",
    ]


def test_tools_apply_only_to_matching_files() -> None:
    tool = Registry().get("opengrep")
    assert not applies(tool, ["src/a.py"]) and applies(tool, ["src/a.py", ".opengrep/regeln.yml"])
    assert applies(Registry().get("deptry"), ["pakete/x/pyproject.toml"])
    assert applies(Registry().get("gitleaks"), ["irgendwas"]) and applies(tool, [])


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    (path / "a.py").write_text("x = 1\n", encoding="utf-8")


def test_profile_skips_unmatched_and_fix_only_tools(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    registry = Registry(
        {
            "nur-md": Tool("nur-md", "doku", ("gibt-es-nicht-xyz",), "keine", applies_to=("*.md",)),
            "hook": Tool("hook", "struktur", (), "keine", fix_command=("true",), stage="autofix"),
        }
    )
    document = run_profile(Runner(tmp_path), registry, CheckProfile("t", ("nur-md", "hook")), use_cache=False)
    assert [(r["werkzeug"], r["status"]) for r in document["werkzeuge"]] == [("nur-md", "entfaellt")]  # type: ignore[index, union-attr]


def test_container_network_only_where_needed(tmp_path: Path) -> None:
    runner = Runner(tmp_path, "bild:1")
    assert "none" in runner.command(["ruff"]) and "none" not in runner.command(["osv-scanner"], network=True)


def test_codemods_run_after_autofix(tmp_path: Path) -> None:
    (tmp_path / ".auditcore-runner.toml").write_text(
        '[codemods]\nlibcst = ["projekt.codemods.Umbenennen"]\nbefehle = [["sh", "-c", "echo ok >> spur"]]\n',
        encoding="utf-8",
    )
    codemods = load_codemods(tmp_path)
    assert [t.name for t in codemods] == ["libcst:projekt.codemods.Umbenennen", "codemod:1"]
    profile = CheckProfile("t", ("ast-grep", "ruff", "typos"))
    order = [t.name for t in fix_order(Registry(), profile, codemods)]
    assert order == ["ruff", "typos", "ast-grep", "libcst:projekt.codemods.Umbenennen", "codemod:1"]
    registry = Registry({"leer": Tool("leer", "python", ("true",), "keine")})
    assert run_fixes(Runner(tmp_path), registry, CheckProfile("t", ("leer",)), codemods[1:]) == ["codemod:1"]
    assert (tmp_path / "spur").read_text(encoding="utf-8") == "ok\n"


def test_codemod_config_is_validated(tmp_path: Path) -> None:
    (tmp_path / ".auditcore-runner.toml").write_text('[codemods]\nbefehle = ["kein-array"]\n', encoding="utf-8")
    with pytest.raises(RepoConfigError):
        load_codemods(tmp_path)
    assert load_codemods(tmp_path / "fehlt") == ()


def test_task_package_matches_fix_template(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n" * 5, encoding="utf-8")
    findings = [Finding("vulture", "unused-variable", "a.py", n, "unused variable 'x'") for n in range(1, 2001)]
    package = aufgaben.build("runner-42", "befunde-beheben", tmp_path, findings)
    rendered = aufgaben.render(package)
    assert rendered.startswith("# Aufgabenpaket runner-42 (befunde-beheben)\n")
    assert len(rendered) <= aufgaben.MAX_ZEICHEN and "im nächsten Paket" in rendered
    assert "Toten Code entfernen" in rendered
    with pytest.raises(ValueError):
        aufgaben.build("mit leerzeichen", "befunde-beheben", tmp_path, findings)


def test_catalog_module_runs_without_optional_imports() -> None:
    code = "import auditcore_runner.werkzeuge as w; print(len(w.FULL_TOOLS))"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert int(result.stdout) >= 40


BEISPIEL = """
[pruefprofile.pr]
werkzeuge = ["ruff", "pyrefly", "pytest", "gitleaks", "playwright"]
ausloeser = ["lokal", "pr"]
zeitlimit_s = 1800
autofix = true

[pruefprofile.pr.werkzeug.playwright]
zeitlimit_s = 900
prioritaet = 90
leer_erlaubt = true
befehl = ["playwright", "test", "e2e", "--reporter=junit"]
autofix_befehl = ["prettier", "--write", "e2e"]

[codemods]
libcst = ["projekt.codemods.AlteApiErsetzen"]
befehle = [["ast-grep", "scan", "--update-all"]]
"""


def test_repo_file_schema_matches_loader(tmp_path: Path) -> None:
    import tomllib

    import jsonschema

    schema = json.loads((DATA.parent / "schemas" / "repo-konfiguration.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(tomllib.loads(BEISPIEL), schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"pruefprofile": {"pr": {"ausloeser": ["immer"]}}}, schema)
    (tmp_path / ".auditcore-runner.toml").write_text(BEISPIEL, encoding="utf-8")
    from auditcore_runner.werkzeuge.modell import load_repo_profiles

    profile = load_repo_profiles(tmp_path)["pr"]
    assert profile.autofix and profile.ordered_tools()[-1] == "playwright"
    configured = profile.configured_tool(Registry().get("playwright"))
    assert configured.command == ("playwright", "test", "e2e", "--reporter=junit")
    assert configured.fix_command == ("prettier", "--write", "e2e")
    assert configured.allow_empty and not profile.configured_tool(Registry().get("pytest")).allow_empty
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"pruefprofile": {"pr": {"werkzeug": {"pytest": {"leer_erlaubt": "ja"}}}}}, schema)
    assert len(load_codemods(tmp_path)) == 2


def test_repo_command_override_runs_without_shell(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    (tmp_path / ".auditcore-runner.toml").write_text(
        '[pruefprofile.test]\nwerkzeuge = ["probe"]\n'
        '[pruefprofile.test.werkzeug.probe]\nbefehl = ["sh", "-c", "printf override"]\n',
        encoding="utf-8",
    )
    from auditcore_runner.werkzeuge.modell import load_repo_profiles

    registry = Registry({"probe": Tool("probe", "extern", ("printf", "catalog"), "keine")})
    document = run_profile(Runner(tmp_path), registry, load_repo_profiles(tmp_path)["test"], use_cache=False)
    assert document["werkzeuge"][0]["status"] == "ok"  # type: ignore[index]


def test_scan_root_paths_and_missing_programs(tmp_path: Path) -> None:
    from auditcore_runner.werkzeuge.ausfuehren import _scan_root_relative

    (tmp_path / "requirements.txt").write_text("jinja2==2.10\n", encoding="utf-8")
    finding = Finding("grype", "GHSA-x", "/requirements.txt", 1, "x")
    assert _scan_root_relative(finding, tmp_path).path == "requirements.txt"
    assert _scan_root_relative(Finding("x", "r", "/etc/hosts", 1, "x"), tmp_path).path == "/etc/hosts"
    registry = Registry({"weg": Tool("weg", "python", ("sh", "-c", "exit 127"), "keine")})
    document = run_profile(Runner(tmp_path), registry, CheckProfile("t", ("weg",)), use_cache=False)
    assert document["werkzeuge"][0]["status"] == "fehlt"  # type: ignore[index]
    assert (tmp_path / ".auditcore-runner" / ".gitignore").read_text(encoding="utf-8") == "*\n"
