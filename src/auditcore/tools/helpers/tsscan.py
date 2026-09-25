"""Extract TS/JS/Vue functions through the shipped Node script ``node/scan.mjs``."""

from __future__ import annotations

import re
from pathlib import Path

from auditcore.tools.helpers.model import (
    TYPESCRIPT,
    FunctionInfo,
    as_dict,
    as_int,
    as_list,
    as_str,
)
from auditcore.tools.helpers.nodetools import run_node

BATCH = 400


def _references(text: str, name: str) -> bool:
    return bool(name) and re.search(rf"(?<![\w$.]){re.escape(name)}(?![\w$])", text) is not None


def _prelude(source: str, definitions: list[dict[str, object]]) -> tuple[str, ...]:
    """Top-level definitions the source references, transitively, in file order."""
    texts = {as_str(d.get("name")): as_str(d.get("text")) for d in definitions}
    selected: set[str] = set()
    pending = [name for name in texts if _references(source, name)]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        selected.add(name)
        pending.extend(
            other for other in texts if other not in selected and _references(texts[name], other)
        )
    return tuple(texts[name] for name in texts if name in selected and texts[name] != source)


def _function(item: dict[str, object], constants: dict[str, object]) -> FunctionInfo:
    path = as_str(item.get("path"))
    source = as_str(item.get("source"))
    file_constants = [as_dict(entry) for entry in as_list(constants.get(path))]
    return FunctionInfo(
        language=TYPESCRIPT,
        path=path,
        name=as_str(item.get("name")),
        kind=as_str(item.get("kind")),
        line=as_int(item.get("line")),
        end_line=as_int(item.get("end_line")),
        tokens=as_int(item.get("tokens")),
        body_hash=as_str(item.get("body_hash")),
        source=source,
        exported=item.get("exported") is True,
        nested=item.get("nested") is True,
        params=as_int(item.get("params")),
        prelude=_prelude(source, file_constants),
    )


def scan_typescript(root: Path, files: list[str]) -> tuple[list[FunctionInfo], list[str]]:
    """Return the functions of the given files and the per-file extraction errors."""
    functions: list[FunctionInfo] = []
    errors: list[str] = []
    for start in range(0, len(files), BATCH):
        payload = {"root": str(root), "files": files[start : start + BATCH]}
        result = as_dict(run_node("scan.mjs", payload))
        constants = as_dict(result.get("constants"))
        functions.extend(
            _function(as_dict(item), constants) for item in as_list(result.get("functions"))
        )
        for error in as_list(result.get("errors")):
            entry = as_dict(error)
            errors.append(f"{as_str(entry.get('path'))}: {as_str(entry.get('error'))}")
    return functions, errors
