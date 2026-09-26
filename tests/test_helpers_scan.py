"""Scanner: extraction (Python, TS, Vue), duplicate groups and library classification."""

from __future__ import annotations

from pathlib import Path

from helper_contracts_support import FIXTURES, node_or_skip

from auditcore.tools.helpers.catalog import library_index, load_topics, normalised_name, topic_of
from auditcore.tools.helpers.model import PYTHON, TYPESCRIPT, SourceFile
from auditcore.tools.helpers.pyscan import scan_python
from auditcore.tools.helpers.scan import EXACT, classify, collect, duplicate_groups, run_scan
from auditcore.tools.helpers.sources import is_skipped, language_of

HASHER = (
    "import hashlib\n\n\ndef {name}(path):\n    digest = hashlib.sha256()\n"
    "    with open(path, 'rb') as handle:\n"
    "        for chunk in iter(lambda: handle.read(65536), b''):\n"
    "            digest.update(chunk)\n    return digest.hexdigest()\n"
)


def test_sources_skip_tests_dependencies_and_builds() -> None:
    assert language_of("a/b.vue") == TYPESCRIPT and language_of("x.py") == PYTHON
    assert language_of("README.md") is None
    for path in (
        "frontend/node_modules/x/y.js",
        "tests/test_a.py",
        "src/a.spec.ts",
        "src/a.d.ts",
        "backend/alembic/versions/1.py",
        "dist/app.js",
        "app-wt/src/a.ts",
    ):
        assert is_skipped(path), path
    assert not is_skipped("frontend/src/lib/format.ts")
    assert is_skipped("frontend/src/legacy/x.ts", ["frontend/src/legacy/*"])


def test_python_normalisation_ignores_names_types_and_docstrings() -> None:
    first = SourceFile(
        "a.py",
        PYTHON,
        'def total(values: list[int]) -> int:\n    """Doc."""\n'
        "    result = 0\n    for value in values:\n        result += value\n    return result\n",
    )
    second = SourceFile(
        "b.py",
        PYTHON,
        "def summe(items):\n    acc = 0\n    for item in items:\n"
        "        acc += item\n    return acc\n",
    )
    [a], [b] = scan_python(first), scan_python(second)
    assert a.body_hash == b.body_hash and a.name == "total" and a.exported


def test_python_methods_are_qualified_and_nested_functions_skipped() -> None:
    file = SourceFile(
        "m.py",
        PYTHON,
        "class A:\n    def run(self):\n        def inner():\n"
        "            return 1\n        return inner()\n",
    )
    assert [(f.name, f.kind) for f in scan_python(file)] == [("A.run", "method")]


def test_python_probe_prelude_contains_stdlib_imports_and_helpers() -> None:
    file = SourceFile(
        "p.py",
        PYTHON,
        "import re\nimport requests\nPATTERN = re.compile('x')\n"
        "def _clean(t):\n    return t.strip()\n\ndef parse(t):\n"
        "    return PATTERN.sub('', _clean(t))\n",
    )
    parse = next(f for f in scan_python(file) if f.name == "parse")
    assert parse.prelude == (
        "import re",
        "PATTERN = re.compile('x')",
        "def _clean(t):\n    return t.strip()",
    )


def test_duplicate_groups_in_fixture() -> None:
    inventory = collect(FIXTURES / "buggy", [], with_ts=False)
    groups = duplicate_groups(inventory.functions)
    names = {tuple(sorted(m.name for m in g.members)) for g in groups}
    assert ("positive_total", "sum_positive") in names


def test_topics_classify_by_normalised_name() -> None:
    topics = load_topics()
    assert normalised_name("Grid._format_Date") == "formatdate"
    file = SourceFile("h.py", PYTHON, HASHER.format(name="_sha256_file"))
    [function] = scan_python(file)
    topic = topic_of(function, topics)
    assert topic is not None and topic.available is not None
    assert topic.available.library == "auditcore_common"


def test_exact_copy_of_library_function_is_found(tmp_path: Path) -> None:
    source = tmp_path / "lib/packages/auditcore_fake/src/auditcore_fake"
    source.mkdir(parents=True)
    (source / "files.py").write_text(HASHER.format(name="digest_of"))
    index = library_index(tmp_path / "lib", with_js=False)
    app = SourceFile("app.py", PYTHON, HASHER.format(name="checksum"))
    [match] = classify(scan_python(app), load_topics(), index)
    assert (
        match.match == EXACT and match.library == "auditcore_fake" and match.status == "vorhanden"
    )
    assert match.key == "library|app.py|checksum|auditcore_fake"


def test_ts_and_vue_scan_with_line_numbers() -> None:
    node_or_skip()
    inventory = collect(FIXTURES / "buggy", [])
    by_name = {f.name: f for f in inventory.functions if f.language == TYPESCRIPT}
    assert by_name["formatDatum"].path == "frontend/src/views/ListView.vue"
    assert by_name["formatDatum"].line == 12
    parse = by_name["parseDecimal"]
    assert (parse.line, parse.nested, parse.kind) == (3, True, "variable")
    assert by_name["parseNumberDe"].exported
    scan = run_scan(inventory, None)
    available = {m.function.name for m in scan.ratcheted}
    assert available == {"sha256_file", "formatDate", "formatDatum", "parse_de_number"}
