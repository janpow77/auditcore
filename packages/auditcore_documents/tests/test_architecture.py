"""F-09/T-38: Laufzeitmodule nutzen nur die Standardbibliothek; Extras nur lazy."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_documents

STDLIB = {
    "__future__",
    "abc",
    "argparse",
    "asyncio",
    "collections",
    "contextlib",
    "copy",
    "dataclasses",
    "datetime",
    "decimal",
    "difflib",
    "enum",
    "functools",
    "getpass",
    "hashlib",
    "io",
    "json",
    "math",
    "os",
    "pathlib",
    "re",
    "subprocess",
    "sys",
    "tempfile",
    "time",
    "types",
    "typing",
    "urllib",
    "uuid",
    "warnings",  # only for DeprecationWarning aliases (docs/quality/code-quality.md)
    "xml",
    "zipfile",
    "zoneinfo",
}
#: Optionale Extras dürfen nur innerhalb von Funktionen importiert werden.
LAZY = {
    "lxml": {"docx", "docx-render"},
    "rapidfuzz": {"fuzzy"},
    "pypdf": {"pdf-text"},
    "docx": {"docx-render"},
    "reportlab": {"pdf-render"},
    "magic": {"mime"},
    "pypdfium2": {"ocr-raster"},
    # Extra ``donut`` (0.2.0): nur verzögert und nur im Donut-Adapter (siehe unten).
    "torch": {"donut"},
    "transformers": {"donut"},
    "PIL": {"donut", "ocr-raster"},
}
DONUT_ONLY = {"torch", "transformers", "PIL"}
#: Extras ``web``/``fastapi`` (0.3.0): Frameworks nur in ihrem Adaptermodul unter ``web/``.
WEB_ADAPTERS = {
    "asgi.py": {"starlette"},
    "fastapi_router.py": {"fastapi"},
    "extraction_asgi.py": {"starlette"},
    "extraction_fastapi.py": {"fastapi"},
}
FORBIDDEN = {
    "fastapi",
    "sqlalchemy",
    "celery",
    "redis",
    "requests",
    "httpx",
    "app",
    "auditcore",
}


def _imports(tree: ast.AST) -> list[tuple[ast.AST, set[str], bool]]:
    found = []
    function_nodes = {
        id(n)
        for f in ast.walk(tree)
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
        for n in ast.walk(f)
        if n is not f
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if getattr(node, "level", 0):
                continue
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            found.append((node, {n.split(".")[0] for n in names}, id(node) in function_nodes))
    return found


def test_runtime_imports() -> None:
    package = Path(auditcore_documents.__file__).parent
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        adapter = WEB_ADAPTERS.get(path.name, set()) if path.parent.name == "web" else set()
        for _node, roots, in_function in _imports(tree):
            assert not roots & (FORBIDDEN - adapter), (path.name, roots)
            optional = roots & set(LAZY)
            if optional:
                assert in_function, (path.name, optional)
                if optional & DONUT_ONLY:
                    assert path.name == "donut.py", (path.name, optional)
                continue
            own = {"auditcore_documents", "auditcore_common", "importlib"}
            assert roots <= STDLIB | own | adapter, (
                path.name,
                roots,
            )
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__", "print", "open"}, (
                    path.name
                )


def test_subprocess_only_in_pdftotext_adapter() -> None:
    package = Path(auditcore_documents.__file__).parent
    users = sorted(
        p.name for p in package.glob("*.py") if "subprocess" in p.read_text(encoding="utf-8")
    )
    assert users == ["pdftext.py"]
    source = (package / "pdftext.py").read_text(encoding="utf-8")
    assert "shell=True" not in source


def test_import_loads_no_optional_dependency() -> None:
    code = (
        "import sys, auditcore_documents, auditcore_documents.legacy, auditcore_documents.cli;"
        "import auditcore_documents.pipeline, auditcore_documents.web;"
        "bad = {'lxml', 'rapidfuzz', 'pypdf', 'docx', 'reportlab', 'auditcore_reporting',"
        " 'magic', 'pypdfium2', 'PIL', 'httpx', 'pydantic', 'sqlalchemy',"
        " 'starlette', 'fastapi', 'multipart'}"
        " & set(sys.modules);"
        "assert not bad, bad"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
