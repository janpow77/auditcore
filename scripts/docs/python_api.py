"""Collect the public API of a Python package statically (AST, no import).

Public names are the entries of ``__all__`` in the package ``__init__``; each
name is followed through relative (and sibling-package) imports to its
definition, whose kind and first docstring line form the overview row. Nothing
of the package is executed.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

MAX_SUMMARY = 180
MAX_DEPTH = 6
# ``type X = ...`` exists from Python 3.12; on 3.11 no node has this type.
_TYPE_ALIAS: tuple[type, ...] = tuple(filter(None, [getattr(ast, "TypeAlias", None)]))


@dataclass(frozen=True)
class ApiEntry:
    name: str
    kind: str
    summary: str
    module: str


@dataclass(frozen=True)
class Definition:
    module: str
    node: ast.stmt | None
    attribute_doc: str | None


@dataclass(frozen=True)
class ModuleEntry:
    name: str
    summary: str


def summary_line(docstring: str | None) -> str:
    """First paragraph of a docstring as one line, cut at a sentence end."""
    if not docstring:
        return ""
    paragraph = docstring.strip().split("\n\n", 1)[0]
    text = " ".join(line.strip() for line in paragraph.splitlines())
    if len(text) <= MAX_SUMMARY:
        return text
    cut = text[:MAX_SUMMARY]
    end = cut.rfind(". ")
    return cut[: end + 1] if end > 40 else cut.rstrip() + " …"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _module_file(package_dir: Path, dotted: str) -> Path | None:
    base = package_dir.joinpath(*dotted.split(".")) if dotted else package_dir
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def declared_all(tree: ast.Module) -> list[str] | None:
    for node in tree.body:
        if not isinstance(node, ast.Assign | ast.AnnAssign) or not _defines(node, "__all__"):
            continue
        if node.value is not None:
            return [str(item) for item in ast.literal_eval(node.value)]
    return None


class _Resolver:
    """Follow a public name from ``__init__`` to its defining statement."""

    def __init__(self, src_root: Path, package: str) -> None:
        self.src_roots = [src_root, *sorted(src_root.parents[1].glob("*/src"))]
        self.package = package

    def locate(self, dotted: str) -> Path | None:
        top, _, rest = dotted.partition(".")
        for root in self.src_roots:
            if (root / top).is_dir():
                return _module_file(root / top, rest)
        return None

    def resolve(self, dotted: str, name: str, depth: int = 0) -> Definition:
        path = self.locate(dotted)
        if path is None or depth > MAX_DEPTH:
            return Definition(dotted, None, None)
        source_lines = path.read_text(encoding="utf-8").splitlines()
        body = _parse(path).body
        for index, node in enumerate(body):
            if _defines(node, name):
                doc = _attribute_doc(node, body, index) or _comment_doc(node, source_lines)
                return Definition(dotted, node, doc)
            source = _import_source(node, name, dotted, path.name == "__init__.py")
            if source is not None:
                return self.resolve(source[0], source[1], depth + 1)
        return Definition(dotted, None, None)


def _defines(node: ast.stmt, name: str) -> bool:
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node.name == name
    if isinstance(node, ast.Assign):
        return any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    if isinstance(node, (ast.AnnAssign, *_TYPE_ALIAS)):
        target = node.target if isinstance(node, ast.AnnAssign) else getattr(node, "name", None)
        return isinstance(target, ast.Name) and target.id == name
    return False


def _attribute_doc(node: ast.stmt, body: list[ast.stmt], index: int) -> str | None:
    """String literal directly after an assignment (attribute docstring)."""
    if isinstance(node, (ast.Assign, ast.AnnAssign, *_TYPE_ALIAS)) and index + 1 < len(body):
        following = body[index + 1]
        if isinstance(following, ast.Expr) and isinstance(following.value, ast.Constant):
            value = following.value.value
            return value if isinstance(value, str) else None
    return None


def _comment_doc(node: ast.stmt, lines: list[str]) -> str | None:
    """Comment block directly above an assignment (``# …`` or ``#: …``)."""
    if not isinstance(node, (ast.Assign, ast.AnnAssign, *_TYPE_ALIAS)):
        return None
    comments: list[str] = []
    row = node.lineno - 2
    while row >= 0 and lines[row].lstrip().startswith("#"):
        comments.insert(0, lines[row].lstrip().lstrip("#:").strip())
        row -= 1
    return " ".join(comments) or None


def _import_source(
    node: ast.stmt, name: str, current: str, is_package: bool
) -> tuple[str, str] | None:
    if not isinstance(node, ast.ImportFrom):
        return None
    for alias in node.names:
        if (alias.asname or alias.name) != name:
            continue
        if node.level == 0:
            return node.module or "", alias.name
        parts = current.split(".")
        keep = len(parts) - node.level + (1 if is_package else 0)
        base = ".".join(parts[:keep])
        module = f"{base}.{node.module}" if node.module else base
        return module, alias.name
    return None


def _class_kind(node: ast.ClassDef) -> str:
    bases = {ast.unparse(base).rsplit(".", 1)[-1] for base in node.bases}
    decorators = {ast.unparse(d).split("(")[0].rsplit(".", 1)[-1] for d in node.decorator_list}
    if any(b.endswith(("Error", "Exception", "Fehler", "Warning")) for b in bases):
        return "Ausnahme"
    if "Protocol" in bases:
        return "Protokoll"
    if bases & {"Enum", "StrEnum", "IntEnum"}:
        return "Aufzählung"
    if bases & {"TypedDict"}:
        return "TypedDict"
    if "dataclass" in decorators or bases & {"NamedTuple"}:
        return "Datenklasse"
    return "Klasse"


def _assignment_kind(name: str, node: ast.stmt) -> str:
    value = getattr(node, "value", None)
    if isinstance(node, _TYPE_ALIAS):
        return "Typalias"
    annotation = getattr(node, "annotation", None)
    if annotation is not None and "TypeAlias" in ast.unparse(annotation):
        return "Typalias"
    if isinstance(value, ast.Subscript | ast.BinOp) and name[:1].isupper() and not name.isupper():
        return "Typalias"
    return "Konstante" if name.isupper() else "Wert"


def describe(name: str, definition: Definition) -> tuple[str, str]:
    """Kind and summary of a definition (unknown definitions stay unknown)."""
    node = definition.node
    if node is None:
        return "Re-Export", ""
    if isinstance(node, ast.ClassDef):
        return _class_kind(node), summary_line(ast.get_docstring(node))
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return "Funktion", summary_line(ast.get_docstring(node))
    return _assignment_kind(name, node), summary_line(definition.attribute_doc)


def public_modules(package_dir: Path) -> list[ModuleEntry]:
    entries = []
    for path in sorted(package_dir.iterdir()):
        if path.name.startswith("_") or path.name == "tests":
            continue
        target = path / "__init__.py" if path.is_dir() else path
        if target.suffix != ".py" or not target.is_file():
            continue
        doc = ast.get_docstring(_parse(target))
        entries.append(ModuleEntry(path.stem, summary_line(doc)))
    return entries


def collect(src_root: Path, package: str) -> tuple[list[str] | None, list[ApiEntry]]:
    """Return ``__all__`` (None when absent) and one entry per public name."""
    init = src_root / package / "__init__.py"
    names = declared_all(_parse(init))
    if names is None:
        return None, []
    resolver = _Resolver(src_root, package)
    entries = []
    for name in names:
        definition = resolver.resolve(package, name)
        module = definition.module
        kind, summary = describe(name, definition)
        short = module.removeprefix(package).lstrip(".") or "(Paketstamm)"
        if not module.startswith(package):
            short = module
        entries.append(ApiEntry(name, kind, summary, short))
    return names, entries
