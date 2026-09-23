"""robots.txt evaluation (RFC 9309 with the common ``*``/``$`` wildcards).

Only the group of the configured user-agent token applies, otherwise the
``*`` group. Among matching rules the longest pattern wins; on equal length
``Allow`` wins. An empty ``Disallow`` allows everything. Nothing here fetches
robots.txt; adapters obtain it through the injected transport.
"""

from __future__ import annotations

import re
import urllib.parse
from collections.abc import Sequence
from dataclasses import dataclass

from .errors import AccessNotPermitted


@dataclass(frozen=True)
class RobotsRules:
    """Rules of one group: ``(allow, pattern)`` in file order."""

    rules: tuple[tuple[bool, str], ...]
    group: str

    def to_list(self) -> list[list[object]]:
        """JSON form (used in harvest cursors)."""
        return [[allow, pattern] for allow, pattern in self.rules] + [[None, self.group]]

    @classmethod
    def from_list(cls, data: Sequence[Sequence[object]]) -> RobotsRules:
        """Inverse of :meth:`to_list`."""
        *rules, marker = data
        return cls(tuple((bool(a), str(p)) for a, p in rules), str(marker[1]))


def parse_robots(text: str, token: str = "*") -> RobotsRules:
    """Rules of the group for ``token`` (case-insensitive), else of ``*``."""
    groups: list[tuple[list[str], list[tuple[bool, str]]]] = []
    agents: list[str] = []
    rules: list[tuple[bool, str]] = []
    collecting_agents = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        field, value = (part.strip() for part in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            if not collecting_agents:
                agents, rules = [], []
                groups.append((agents, rules))
                collecting_agents = True
            agents.append(value.lower())
        elif field in ("allow", "disallow"):
            collecting_agents = False
            if not groups:
                continue
            if field == "disallow" and not value:
                continue  # empty Disallow: everything allowed
            rules.append((field == "allow", value))
        else:
            collecting_agents = False
    wanted = token.lower()
    if wanted != "*":
        for group_agents, group_rules in groups:
            if any(a != "*" and a in wanted for a in group_agents):
                return RobotsRules(tuple(group_rules), wanted)
    for group_agents, group_rules in groups:
        if "*" in group_agents:
            return RobotsRules(tuple(group_rules), "*")
    return RobotsRules((), "*")


def _pattern(rule: str) -> re.Pattern[str]:
    anchored = rule.endswith("$")
    body = rule[:-1] if anchored else rule
    regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in body)
    return re.compile(regex + ("$" if anchored else ""))


def is_allowed(rules: RobotsRules, url: str) -> bool:
    """Whether ``url`` (absolute or path) may be fetched under ``rules``."""
    parts = urllib.parse.urlsplit(url)
    target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    best: tuple[int, bool] | None = None
    for allow, rule in rules.rules:
        if not rule:
            continue
        if _pattern(rule).match(target) is None:
            continue
        length = len(rule)
        if best is None or length > best[0] or (length == best[0] and allow):
            best = (length, allow)
    return True if best is None else best[1]


def require_allowed(rules: RobotsRules, url: str) -> None:
    """Raise :class:`AccessNotPermitted` for a disallowed ``url``."""
    if not is_allowed(rules, url):
        raise AccessNotPermitted(f"robots.txt ({rules.group}) untersagt den Abruf von {url}.")


def robots_url(url: str) -> str:
    """``scheme://host/robots.txt`` of ``url``."""
    parts = urllib.parse.urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}/robots.txt"
