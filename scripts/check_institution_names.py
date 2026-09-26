"""Forbid names of concrete institutions in the shared packages.

The auditcore packages serve every audit authority and every ESI fund, so
names such as those of a particular intermediate body or ministry must not be
wired into code, profiles, tests or package documentation. The names are kept
in ``quality/institutsnamen-denylist.txt`` (never in source code); justified
exceptions, each limited to a file pattern and an allowed expression, live in
``quality/institutsnamen-ausnahmen.txt``.

    python scripts/check_institution_names.py            # check, exit 1 on findings
    python scripts/check_institution_names.py --json out.json

Exit code 0: no finding outside the exceptions and every exception is still
needed. Exit code 1: findings or stale exceptions (listed on stdout).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENYLIST = ROOT / "quality" / "institutsnamen-denylist.txt"
EXCEPTIONS = ROOT / "quality" / "institutsnamen-ausnahmen.txt"
#: Tracked paths that are checked; analysis and history reports are excluded.
SCOPE = (
    "packages/",
    "packages-js/",
    "docs/ui/",
    "examples/",
    "scripts/",
    "src/",
    "contracts/",
    "contexts/",
    "tests/",
)
_LETTER = "A-Za-zÄÖÜäöüß"


@dataclass(frozen=True)
class Term:
    """One forbidden name and its optional neutral replacement."""

    name: str
    replacement: str | None


@dataclass(frozen=True)
class Allowance:
    """A justified exception: file pattern, allowed expression, reason."""

    pattern: str
    allowed: re.Pattern[str]
    reason: str


@dataclass(frozen=True)
class Finding:
    """A forbidden name at a file position."""

    path: str
    line: int
    text: str


def _lines(path: Path) -> Iterable[str]:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            yield line


def load_denylist(path: Path = DENYLIST) -> list[Term]:
    """Terms of the denylist, longest first (so replacements do not overlap)."""
    terms = []
    for line in _lines(path):
        name, _, replacement = (part.strip() for part in line.partition("=>"))
        terms.append(Term(name, replacement or None))
    return sorted(terms, key=lambda term: -len(term.name))


def load_exceptions(path: Path = EXCEPTIONS) -> list[Allowance]:
    """Exceptions ``<glob> | <regex> | <reason>``; a reason is mandatory."""
    result = []
    for line in _lines(path):
        parts = [part.strip() for part in line.split(" | ")]
        if len(parts) != 3 or not all(parts):
            raise ValueError(f"Ausnahme braucht Muster, Ausdruck und Begründung: {line}")
        result.append(Allowance(parts[0], re.compile(parts[1], re.IGNORECASE), parts[2]))
    return result


def name_pattern(terms: Sequence[Term]) -> re.Pattern[str]:
    """Case-insensitive pattern matching any term as a word of its own."""
    alternatives = "|".join(re.escape(term.name) for term in terms)
    # a regex word boundary written as ``\\b`` counts as a separator, too
    before, after = rf"(?:(?<![{_LETTER}])|(?<=\\b))", rf"(?:(?![{_LETTER}])|(?=\\b))"
    return re.compile(f"{before}(?:{alternatives}){after}", re.IGNORECASE)


def neutralize(text: str, terms: Sequence[Term] | None = None) -> str:
    """Replace every term that has a replacement (used by capture tools)."""
    for term in load_denylist() if terms is None else terms:
        if term.replacement is not None:
            text = name_pattern([term]).sub(term.replacement, text)
    return text


def _covered(line: str, start: int, end: int, allowed: Iterable[re.Pattern[str]]) -> bool:
    return any(m.start() <= start and end <= m.end() for rx in allowed for m in rx.finditer(line))


def scan_text(
    path: str, text: str, pattern: re.Pattern[str], exceptions: Sequence[Allowance]
) -> tuple[list[Finding], set[int]]:
    """Findings not covered by an exception, and the indices of the used exceptions."""
    applicable = [(i, e) for i, e in enumerate(exceptions) if fnmatch.fnmatch(path, e.pattern)]
    findings: list[Finding] = []
    used: set[int] = set()
    for number, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            hits = [i for i, e in applicable if _covered(line, *match.span(), [e.allowed])]
            used.update(hits)
            if not hits:
                findings.append(Finding(path, number, line.strip()[:160]))
    return findings, used


def tracked_files(root: Path = ROOT) -> list[str]:
    """Tracked files within :data:`SCOPE`."""
    output = subprocess.run(
        ["git", "ls-files", "-z", "--", *SCOPE], cwd=root, capture_output=True, check=True
    ).stdout.decode("utf-8")
    return sorted(name for name in output.split("\0") if name)


def check(root: Path = ROOT) -> tuple[list[Finding], list[Allowance]]:
    """All findings and the exceptions that no longer match anything."""
    terms, exceptions = load_denylist(), load_exceptions()
    pattern = name_pattern(terms)
    findings: list[Finding] = []
    used: set[int] = set()
    for name in tracked_files(root):
        try:
            text = (root / name).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        found, hits = scan_text(name, text, pattern, exceptions)
        findings.extend(found)
        used |= hits
    stale = [e for i, e in enumerate(exceptions) if i not in used]
    return findings, stale


def _label(allowance: Allowance) -> str:
    return f"{allowance.pattern} | {allowance.allowed.pattern}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path, help="Ergebnis zusätzlich als JSON schreiben")
    args = parser.parse_args(argv)
    findings, stale = check()
    for finding in findings:
        print(f"{finding.path}:{finding.line}: Institutsname: {finding.text}")
    for allowance in stale:
        print(f"Ausnahme ohne Treffer (entfernen): {_label(allowance)}")
    if args.json:
        payload = {
            "findings": [vars(f) for f in findings],
            "stale_exceptions": [_label(allowance) for allowance in stale],
        }
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    if findings or stale:
        print(f"{len(findings)} Fundstelle(n), {len(stale)} veraltete Ausnahme(n).")
        return 1
    print("Keine Institutsnamen außerhalb der begründeten Ausnahmen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
