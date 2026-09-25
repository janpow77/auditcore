"""Declarative lint rules for known helper error patterns (``data/rules.json``).

Rule kinds and their per-language ``spec``:

``regex``     ``patterns`` (any matches a finding), ``unless_line``
``call``      ``calls`` (``callee`` with optional ``receiver``/``when_args``),
              ``require_args`` (arguments containing it are fine)
``file``      ``when_all`` (all must occur), ``unless_any`` (none may occur)
``function``  ``name`` (normalised name), ``body_all``, ``body_none``
``probe``     executed against a contract, see :mod:`auditcore.tools.helpers.probe`
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from auditcore.tools.helpers.model import (
    FunctionInfo,
    SourceFile,
    as_dict,
    as_list,
    as_str,
    read_json,
    str_list,
)

RULES_PATH = Path(__file__).with_name("data") / "rules.json"
KINDS = ("regex", "call", "file", "function", "probe")
RECEIVER_WINDOW = 80
COMMENT = re.compile(r"^\s*(//|/\*|\*|#)")


@dataclass(frozen=True)
class Rule:
    """One declarative rule."""

    id: str
    title: str
    kind: str
    severity: str
    message: str
    remedy: str
    contract: str
    spec: dict[str, dict[str, object]]
    examples: dict[str, list[dict[str, object]]] = field(default_factory=dict)

    def applies(self, language: str) -> bool:
        """True when the rule has a specification for ``language``."""
        return language in self.spec

    def patterns(self, language: str, key: str) -> list[re.Pattern[str]]:
        """Compiled regexes of one spec entry."""
        value = self.spec.get(language, {}).get(key)
        items = [value] if isinstance(value, str) else str_list(value)
        return [re.compile(item, re.MULTILINE) for item in items]

    def option(self, language: str, key: str) -> object:
        """Raw spec value of one entry."""
        return self.spec.get(language, {}).get(key)


def _rule(entry: dict[str, object]) -> Rule:
    kind = as_str(entry.get("kind"))
    if kind not in KINDS:
        raise ValueError(f"Unbekannte Regelart: {kind}")
    spec = {language: as_dict(value) for language, value in as_dict(entry.get("spec")).items()}
    examples = {
        name: [as_dict(i) for i in as_list(v)] for name, v in as_dict(entry.get("examples")).items()
    }
    return Rule(
        id=as_str(entry.get("id")),
        title=as_str(entry.get("title")),
        kind=kind,
        severity=as_str(entry.get("severity"), "fehler"),
        message=as_str(entry.get("message")),
        remedy=as_str(entry.get("remedy")),
        contract=as_str(entry.get("contract")),
        spec=spec,
        examples=examples,
    )


def load_rules(path: Path = RULES_PATH) -> list[Rule]:
    """Load and validate the rule catalog (unique IDs, known kinds, valid regexes)."""
    rules = [_rule(as_dict(entry)) for entry in as_list(as_dict(read_json(path)).get("rules"))]
    ids = [rule.id for rule in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("Doppelte Regel-IDs im Regelkatalog")
    return rules


@dataclass(frozen=True)
class Hit:
    """A raw rule hit before suppression handling."""

    line: int
    snippet: str
    anchor: str = ""


def _is_comment(file: SourceFile, line: int) -> bool:
    return bool(COMMENT.match(file.line_text(line)))


def regex_hits(rule: Rule, file: SourceFile) -> Iterator[Hit]:
    """Line-oriented pattern matches outside comments."""
    unless = rule.patterns(file.language, "unless_line")
    seen: set[int] = set()
    for pattern in rule.patterns(file.language, "patterns"):
        for match in pattern.finditer(file.text):
            line = file.line_of(match.start())
            text = file.line_text(line)
            if line in seen or _is_comment(file, line) or any(p.search(text) for p in unless):
                continue
            seen.add(line)
            yield Hit(line, text.strip())


def balanced_args(text: str, start: int) -> str:
    """Return the argument text of a call whose opening parenthesis ends at ``start``."""
    depth = 1
    position = start
    while position < len(text) and depth:
        char = text[position]
        depth += 1 if char == "(" else -1 if char == ")" else 0
        position += 1
    return text[start : position - 1] if depth == 0 else text[start:]


def _call_matches(
    spec: dict[str, object], file: SourceFile, required: re.Pattern[str]
) -> Iterator[int]:
    callee = re.compile(as_str(spec.get("callee")))
    receiver = re.compile(as_str(spec.get("receiver"))) if spec.get("receiver") else None
    when_args = re.compile(as_str(spec.get("when_args"))) if spec.get("when_args") else None
    for match in callee.finditer(file.text):
        args = balanced_args(file.text, match.end())
        if required.search(args):
            continue
        before = file.text[max(0, match.start() - RECEIVER_WINDOW) : match.start()]
        if receiver is not None and not receiver.search(before):
            continue
        if when_args is not None and not when_args.search(args):
            continue
        yield match.start()


def call_hits(rule: Rule, file: SourceFile) -> Iterator[Hit]:
    """Calls whose arguments lack the required option (e.g. ``timeZone``)."""
    required = re.compile(as_str(rule.option(file.language, "require_args"), r"(?!x)x"))
    seen: set[int] = set()
    for spec in map(as_dict, as_list(rule.option(file.language, "calls"))):
        for offset in _call_matches(spec, file, required):
            line = file.line_of(offset)
            if line not in seen and not _is_comment(file, line):
                seen.add(line)
                yield Hit(line, file.line_text(line).strip())


def file_hits(rule: Rule, file: SourceFile) -> Iterator[Hit]:
    """One hit per file when all ``when_all`` patterns occur and no ``unless_any``."""
    required = rule.patterns(file.language, "when_all")
    if not required or any(p.search(file.text) for p in rule.patterns(file.language, "unless_any")):
        return
    matches = [p.search(file.text) for p in required]
    if all(matches):
        first = matches[0]
        line = file.line_of(first.start()) if first else 1
        yield Hit(line, file.line_text(line).strip(), anchor=f"{rule.id}:{file.path}")


def function_matches(rule: Rule, function: FunctionInfo, normalised_name: str) -> bool:
    """True when a function satisfies the name and body conditions of a rule."""
    name = rule.option(function.language, "name")
    if isinstance(name, str) and not re.search(name, normalised_name):
        return False
    body = function.source
    if not all(p.search(body) for p in rule.patterns(function.language, "body_all")):
        return False
    return not any(p.search(body) for p in rule.patterns(function.language, "body_none"))


def innermost(functions: list[FunctionInfo]) -> list[FunctionInfo]:
    """Drop functions that enclose another matching function of the same file."""

    def encloses(outer: FunctionInfo, inner: FunctionInfo) -> bool:
        """True if ``inner`` lies strictly inside ``outer``."""
        return (
            outer is not inner
            and outer.path == inner.path
            and outer.line <= inner.line
            and inner.end_line <= outer.end_line
            and (outer.line, outer.end_line) != (inner.line, inner.end_line)
        )

    return [f for f in functions if not any(encloses(f, other) for other in functions)]
