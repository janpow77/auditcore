"""Registry der Prüfregeln: kleine, einzeln testbare Funktionen je Gruppe."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass

from .context import ValidationContext
from .issues import ValidationIssue

RuleFunction = Callable[[ValidationContext], Iterable[ValidationIssue]]


@dataclass(frozen=True)
class RegisteredRule:
    """Registrierte Regelfunktion mit Gruppe und IDs."""

    group: str
    rule_ids: tuple[str, ...]
    function: RuleFunction

    @property
    def name(self) -> str:
        """Name der Regelfunktion."""
        return self.function.__name__


RULES: list[RegisteredRule] = []


def rule(group: str, *rule_ids: str) -> Callable[[RuleFunction], RuleFunction]:
    """Registriert eine Regelfunktion mit den IDs, die sie melden kann."""

    def register(function: RuleFunction) -> RuleFunction:
        RULES.append(RegisteredRule(group, rule_ids, function))
        return function

    return register


def rules_for(group: str) -> list[RegisteredRule]:
    """Registrierte Regeln einer Gruppe."""
    return [r for r in RULES if r.group == group]


def run(context: ValidationContext) -> Iterator[ValidationIssue]:
    """Alle Regeln der konfigurierten Gruppen; deaktivierte IDs werden verworfen."""
    disabled = context.config.disabled
    for group in context.config.groups:
        for registered in rules_for(group):
            for found in registered.function(context):
                if found.rule_id not in disabled:
                    yield found
