from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from auditcore_runner import codemods
from auditcore_runner.cli import main
from auditcore_runner.werkzeuge import aufgaben, bericht, einstellungen, parser
from auditcore_runner.werkzeuge.ausfuehren import Runner, content_key, run_profile
from auditcore_runner.werkzeuge.befunde import (
    Finding,
    deduplicate,
    from_sarif,
    load_baseline,
    only_new,
    save_baseline,
    to_sarif,
)
from auditcore_runner.werkzeuge.katalog import MINIMUM_TOOLS, Registry, external_orchestrator
from auditcore_runner.werkzeuge.modell import (
    DEFAULT_PROFILES,
    CheckProfile,
    RepoConfigError,
    Tool,
    ToolSetting,
    apply_machine_settings,
    load_repo_profiles,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_minimum_catalog() -> None:
    names = {t.name for t in MINIMUM_TOOLS}
    assert {"ruff", "mypy", "pytest", "gitleaks", "eslint", "zizmor", "actionlint", "codegate"} <= names
    assert all(t.parser in parser.PARSERS for t in MINIMUM_TOOLS)
    assert Registry().get("ruff").can_fix and Registry().get("eslint").can_fix
    registry = Registry()
    registry.register(external_orchestrator("megalinter", ("mega-linter",), "report.sarif"))
    assert registry.get("megalinter").parser == "sarif"


@pytest.mark.parametrize(
    ("name", "fixture", "expected"),
    [
        ("ruff-json", "ruff.json", [("ruff", "S608", "src/a.py", 12, True), ("ruff", "D103", "src/a.py", 3, False)]),
        ("mypy-text", "mypy.txt", [("mypy", "arg-type", "src/a.py", 7, False)]),
        ("junit-xml", "junit.xml", [("pytest", "failure", "tests/test_a.py", 0, False)]),
        ("gitleaks-json", "gitleaks.json", [("gitleaks", "generic-api-key", "config.py", 4, False)]),
        ("eslint-json", "eslint.json", [("eslint", "no-unused-vars", "/w/app.ts", 2, False)]),
        ("actionlint-json", "actionlint.json", [("actionlint", "expression", ".github/workflows/ci.yml", 9, False)]),
        ("sarif", "zizmor.sarif", [("zizmor", "template-injection", ".github/workflows/ci.yml", 21, False)]),
        ("codegate-json", "codegate.json", [("codegate", "complexity_over_10", "packages/x/src/x/a.py", 40, False)]),
    ],
)
def test_parsers(name: str, fixture: str, expected: list[tuple[str, str, str, int, bool]]) -> None:
    findings = parser.PARSERS[name]((FIXTURES / fixture).read_text(encoding="utf-8"))
    assert [(f.tool, f.rule, f.path, f.line, f.fixable) for f in findings] == expected


def test_gitleaks_never_copies_the_secret() -> None:
    finding = parser.gitleaks((FIXTURES / "gitleaks.json").read_text(encoding="utf-8"))[0]
    assert "sk-live" not in finding.message


def test_fingerprint_ignores_line_moves_and_baseline(tmp_path: Path) -> None:
    old = Finding("ruff", "E501", "a.py", 10, "Line too long (130 > 120)")
    moved = Finding("ruff", "E501", "a.py", 55, "Line too long (131 > 120)")
    other = Finding("ruff", "F401", "a.py", 3, "unused import")
    assert old.with_fingerprint().fingerprint == moved.with_fingerprint().fingerprint
    save_baseline(tmp_path / "baseline.json", [old])
    assert only_new([moved, other], load_baseline(tmp_path / "baseline.json")) == [other.with_fingerprint()]
    assert len(deduplicate([old, old, other])) == 2


def test_sarif_roundtrip() -> None:
    findings = [Finding("ruff", "S608", "src/a.py", 12, "SQL", "fehler", 5)]
    back = from_sarif(to_sarif(findings))
    assert [(f.tool, f.rule, f.path, f.line, f.column, f.severity) for f in back] == [
        ("ruff", "S608", "src/a.py", 12, 5, "fehler")
    ]


def test_repo_profiles_and_machine_overrides(tmp_path: Path) -> None:
    (tmp_path / ".auditcore-runner.toml").write_text(
        '[pruefprofile.pr]\nwerkzeuge = ["ruff", "mypy"]\nmax_befunde = 50\n'
        "[pruefprofile.pr.werkzeug.mypy]\nzeitlimit_s = 900\nprioritaet = 1\n"
        '[pruefprofile.eigen]\nwerkzeuge = ["gitleaks"]\nausloeser = ["nacht"]\n',
        encoding="utf-8",
    )
    profiles = load_repo_profiles(tmp_path)
    assert profiles["pr"].tools == ("ruff", "mypy") and profiles["pr"].max_findings == 50
    assert profiles["pr"].ordered_tools() == ["mypy", "ruff"]
    assert profiles["eigen"].triggers == ("nacht",) and "schnell" in profiles
    switched = apply_machine_settings(profiles["pr"], {"ruff": ToolSetting(enabled=False)})
    assert switched.ordered_tools() == ["mypy"]
    (tmp_path / ".auditcore-runner.toml").write_text('[pruefprofile.x]\nausloeser = ["irgendwann"]\n', encoding="utf-8")
    with pytest.raises(RepoConfigError):
        load_repo_profiles(tmp_path)


def test_machine_settings_file_roundtrip() -> None:
    settings = {"pr": {"mypy": ToolSetting(True, 900, 1)}}
    einstellungen.save(settings)
    assert einstellungen.load() == settings
    with pytest.raises(einstellungen.ToolSettingsError):
        einstellungen.parse({"schema": einstellungen.SCHEMA, "profile": {"pr": {"mypy": {"zeitlimit_s": 1}}}})


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    (path / "a.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], check=True
    )


def test_host_run_with_cache(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_repo(repo)
    counter = tmp_path / "zaehler"
    script = (
        "import json,pathlib,sys;p=pathlib.Path(sys.argv[1]);p.write_text(p.read_text()+'x' if p.exists() else 'x');"
        "print(json.dumps([{'code':'F401','filename':'a.py','location':{'row':1,'column':1},'message':'unused'}]))"
    )
    fake = Tool("fake", "python", (sys.executable, "-c", script, str(counter)), "ruff-json")
    registry = Registry({"fake": fake})
    profile = CheckProfile("t", ("fake",))
    first = run_profile(Runner(repo), registry, profile)
    second = run_profile(Runner(repo), registry, profile)
    assert len(first["befunde"]) == 1 and counter.read_text() == "x"  # type: ignore[arg-type]
    assert second["werkzeuge"][0]["aus_cache"] is True  # type: ignore[index]
    before = content_key(repo)
    (repo / "a.py").write_text("x = 2\n", encoding="utf-8")
    assert content_key(repo) != before
    run_profile(Runner(repo), registry, profile)
    assert counter.read_text() == "xx"


def test_missing_tool_is_reported(tmp_path: Path) -> None:
    registry = Registry({"weg": Tool("weg", "python", ("gibt-es-nicht-xyz",), "ruff-json")})
    document = run_profile(Runner(tmp_path), registry, CheckProfile("t", ("weg",)), use_cache=False)
    assert document["werkzeuge"][0]["status"] == "fehlt"  # type: ignore[index]


def _custom_profile(tmp_path: Path, tools: dict[str, str]) -> CheckProfile:
    """Profile ``pr`` with one script per tool; ``{ausgabe}`` is passed when the script name says so."""
    lines = ["[pruefprofile.pr]", f"werkzeuge = {json.dumps(list(tools))}"]
    for name, source in tools.items():
        script = tmp_path / f"{name}.py"
        script.write_text(source, encoding="utf-8")
        command = [sys.executable, str(script), *(["{ausgabe}"] if "sys.argv[1]" in source else [])]
        lines += [f"[pruefprofile.pr.werkzeug.{name}]", f"befehl = {json.dumps(command)}"]
    (tmp_path / ".auditcore-runner.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return load_repo_profiles(tmp_path)["pr"]


def _rows(document: dict[str, object], key: str) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], document[key])


def test_custom_tool_with_command_runs_by_exit_code(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    profile = _custom_profile(tmp_path, {"gut": "pass\n", "schlecht": "import sys\nsys.exit('kaputt')\n"})
    tool = profile.configured_tool(Registry().get("gut"))
    assert (tool.area, tool.parser, tool.output_file) == ("eigen", "exitcode", "")
    document = run_profile(Runner(tmp_path), Registry(), profile)
    statuses = {t["werkzeug"]: (t["status"], t["befunde"], t["aus_cache"]) for t in _rows(document, "werkzeuge")}
    assert statuses == {"gut": ("ok", 0, False), "schlecht": ("ok", 1, False)}
    (finding,) = _rows(document, "befunde")
    assert finding["werkzeug"] == "schlecht" and finding["regel"] == "exitcode"
    assert "Exitcode 1" in str(finding["meldung"]) and "kaputt" in str(finding["meldung"])
    again = run_profile(Runner(tmp_path), Registry(), profile)
    assert all(t["aus_cache"] is False for t in _rows(again, "werkzeuge"))


def test_custom_tool_with_output_placeholder_reads_junit(tmp_path: Path) -> None:
    _git_repo(tmp_path)
    report = '<testsuite><testcase classname="t" name="a"><failure message="rot"/></testcase></testsuite>'
    source = f"import pathlib, sys\npathlib.Path(sys.argv[1]).write_text({report!r})\nsys.exit(1)\n"
    profile = _custom_profile(tmp_path, {"tests": source})
    tool = profile.configured_tool(Registry().get("tests"))
    assert (tool.parser, tool.output_file) == ("junit-xml", "tests.xml")
    document = run_profile(Runner(tmp_path), Registry(), profile)
    assert _rows(document, "werkzeuge")[0]["status"] == "ok"
    assert len(_rows(document, "befunde")) == 1


def test_unknown_tool_without_command_is_reported(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _git_repo(tmp_path)
    (tmp_path / ".auditcore-runner.toml").write_text(
        '[pruefprofile.pr]\nwerkzeuge = ["gibtsnicht"]\n', encoding="utf-8"
    )
    document = run_profile(Runner(tmp_path), Registry(), load_repo_profiles(tmp_path)["pr"])
    (result,) = _rows(document, "werkzeuge")
    assert result["status"] == "unbekannt" and "befehl" in str(result["meldung"])
    assert main(["lokal", "pr", "--host", "--pfad", str(tmp_path)]) == 2
    assert "gibtsnicht" in capsys.readouterr().err


def test_report_and_task_package(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import os\n\n\ndef f():\n    return 1\n", encoding="utf-8")
    findings = [
        Finding("ruff", "D103", "a.py", 4, "Missing docstring"),
        Finding("ruff", "F401", "a.py", 1, "unused", fixable=True),
    ]
    text = bericht.render(findings, token_budget=500)
    assert "1 zu bearbeiten, 1 automatisch behebbar" in text and "a.py" in text and "geschätzte Tokens" in text
    package = aufgaben.build("p1", "docstrings", tmp_path, findings, {"ruff/D103": "Einzeiligen Docstring ergänzen"})
    assert len(package.items) == 1 and "def f()" in package.items[0].excerpt
    rendered = aufgaben.render(package)
    assert "a.py:4" in rendered and "Hinweis: Einzeiligen Docstring" in rendered
    command = aufgaben.command(package, tmp_path / "paket.md")
    assert "OTEL_RESOURCE_ATTRIBUTES=task_type=docstrings,paket_id=p1" in command and "--max-budget-usd 1" in command
    assert "codex exec --json" in aufgaben.command(package, tmp_path / "paket.md", "codex")
    documents = [{"befunde": [f.as_dict() for f in findings]}]
    assert [f.rule for f in bericht.findings_from_documents(documents)] == ["D103", "F401"]


def test_default_profiles_reference_known_tools() -> None:
    names = Registry().names()
    assert all(tool in names for profile in DEFAULT_PROFILES.values() for tool in profile.tools)
    assert json.dumps(sorted(DEFAULT_PROFILES))


def _executable(path: Path, source: str) -> None:
    path.write_text("#!/usr/bin/env python3\n" + source, encoding="utf-8")
    path.chmod(0o755)


def test_ast_grep_codemod_is_published_only_after_refactor_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, binaries = tmp_path / "repo", tmp_path / "bin"
    repo.mkdir()
    binaries.mkdir()
    _git_repo(repo)
    (repo / "regel.yml").write_text("id: modernisieren\n", encoding="utf-8")
    (repo / "auditcore-verification.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "config"],
        check=True,
    )
    _executable(
        binaries / "ast-grep",
        "from pathlib import Path\nPath('a.py').write_text('x = 2\\n')\n",
    )
    _executable(
        binaries / "auditcore-refactor",
        "import json\nfrom pathlib import Path\n"
        "ok = Path('a.py').read_text() == 'x = 2\\n'\n"
        "print(json.dumps({'status': 'PASS' if ok else 'MIGRATION_BLOCKED'}))\nraise SystemExit(0 if ok else 1)\n",
    )
    monkeypatch.setenv("PATH", f"{binaries}:{os.environ['PATH']}")

    result = codemods.run("ast-grep", "regel.yml", repo)

    assert result.changed_files == ("a.py",)
    assert (repo / "a.py").read_text(encoding="utf-8") == "x = 2\n"
    assert result.verification["status"] == "PASS"


def test_codemod_failure_leaves_repository_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, binaries = tmp_path / "repo", tmp_path / "bin"
    repo.mkdir()
    binaries.mkdir()
    _git_repo(repo)
    (repo / "regel.yml").write_text("id: kaputt\n", encoding="utf-8")
    (repo / "auditcore-verification.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "config"],
        check=True,
    )
    _executable(binaries / "ast-grep", "from pathlib import Path\nPath('a.py').write_text('x = 9\\n')\n")
    _executable(
        binaries / "auditcore-refactor",
        "import json\nprint(json.dumps({'status': 'MIGRATION_BLOCKED'}))\nraise SystemExit(1)\n",
    )
    monkeypatch.setenv("PATH", f"{binaries}:{os.environ['PATH']}")

    with pytest.raises(codemods.CodemodError, match="verify"):
        codemods.run("ast-grep", "regel.yml", repo)

    assert (repo / "a.py").read_text(encoding="utf-8") == "x = 1\n"


def test_codemod_requires_clean_tree_and_verification_config(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_repo(repo)
    with pytest.raises(codemods.CodemodError, match="verification"):
        codemods.run("libcst", "package.Rename", repo)
    (repo / "auditcore-verification.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(codemods.CodemodError, match="nicht sauber"):
        codemods.run("libcst", "package.Rename", repo)
