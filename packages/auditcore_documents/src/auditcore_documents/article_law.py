"""Gesetzessynopse: gängige Änderungsbefehle eines Artikelgesetzes anwenden.

Befehlsmuster, Anwendung und Ergebnisaufbau entsprechen ``article_law.py``
des Originals. Die Anwendung ist eine Arbeitshilfe ohne amtlichen Charakter:
erkannt werden nur Befehle auf Absatzebene; Satz-, Nummern- und
Buchstabenangaben werden nicht aufgelöst (dokumentiert in DC-L03).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from auditcore_documents.model import CompareItem, CompareRow, ComparisonResult

OPEN_QUOTE = r"[„\"»]"
CLOSE_QUOTE = r"[“\"«]"
WORK_AID_NOTICE = "Arbeitshilfe ohne amtlichen Charakter; jede Zuordnung ist fachlich zu prüfen."


@dataclass
class LawParagraph:
    section: str
    paragraph: int
    text: str
    new_text: str | None = None
    command: str = ""
    repealed: bool = False
    inserted: bool = False

    @property
    def location(self) -> str:
        if self.inserted:
            return f"{self.section}, neuer Absatz {self.paragraph}"
        return f"{self.section} Absatz {self.paragraph}"


COMMAND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "replace",
        re.compile(
            rf"^In\s+(?P<section>§+\s*\d+[a-z]?)\s+"
            rf"(?:Absatz|Abs\.)\s*(?P<paragraph>\d+).*?"
            rf"(?:werden|wird)\s+die\s+(?:Wörter|Wort|Angaben|Angabe|Zahl)\s*"
            rf"{OPEN_QUOTE}(?P<old>.+?){CLOSE_QUOTE}\s+durch\s+die\s+"
            rf"(?:Wörter|Wort|Angaben|Angabe|Zahl)\s*"
            rf"{OPEN_QUOTE}(?P<new>.+?){CLOSE_QUOTE}\s+ersetzt",
            re.IGNORECASE,
        ),
    ),
    (
        "repeal",
        re.compile(
            r"^(?P<section>§+\s*\d+[a-z]?)"
            r"(?:\s+(?:Absatz|Abs\.)\s*(?P<paragraph>\d+))?\s+wird\s+aufgehoben",
            re.IGNORECASE,
        ),
    ),
    (
        "recast",
        re.compile(
            r"^(?P<section>§+\s*\d+[a-z]?)\s+"
            r"(?:Absatz|Abs\.)\s*(?P<paragraph>\d+)\s+wird\s+wie\s+folgt\s+gefasst",
            re.IGNORECASE,
        ),
    ),
    (
        "insert",
        re.compile(
            r"^Nach\s+(?P<section>§+\s*\d+[a-z]?)\s+"
            r"(?:Absatz|Abs\.)\s*(?P<paragraph>\d+)\s+wird\s+folgender\s+"
            r"Absatz(?:\s+(?P<new_number>\d+))?.*?eingefügt",
            re.IGNORECASE,
        ),
    ),
)
_UNSUPPORTED_START = re.compile(r"^(?:In|Nach|Vor|§|Art)", re.IGNORECASE)
_UNSUPPORTED_VERB = re.compile(r"\bwird|\bwerden", re.IGNORECASE)


def _normalise_section(value: str) -> str:
    return re.sub(r"\s+", "", value or "").casefold()


def _quoted_text(value: str) -> str:
    match = re.search(rf"{OPEN_QUOTE}(.+?){CLOSE_QUOTE}", value, re.DOTALL)
    return match.group(1).strip() if match else value.strip()


def base_paragraphs(items: list[CompareItem]) -> list[LawParagraph]:
    """Absätze des Stammgesetzes aus Fließtext-Einheiten unter „§ …“-Überschriften."""
    counts: dict[str, int] = {}
    paragraphs: list[LawParagraph] = []
    for item in items:
        match = re.match(r"^(§+\s*\d+[a-z]?)", item.section, re.IGNORECASE)
        if not match:
            continue
        section = re.sub(r"\s+", " ", match.group(1)).strip()
        counts[section] = counts.get(section, 0) + 1
        paragraphs.append(LawParagraph(section, counts[section], item.text))
    if not paragraphs:
        raise ValueError("Im Stammgesetz wurden keine Paragrafen mit Absätzen gefunden.")
    return paragraphs


def _find(
    paragraphs: list[LawParagraph], section: str, paragraph: str | int
) -> LawParagraph | None:
    wanted_section = _normalise_section(section)
    wanted_paragraph = int(paragraph)
    return next(
        (
            item
            for item in paragraphs
            if _normalise_section(item.section) == wanted_section
            and item.paragraph == wanted_paragraph
        ),
        None,
    )


def _append_command(target: LawParagraph, command: str) -> None:
    target.command = "\n".join(filter(None, [target.command, command]))


#: Benannte Gruppen eines erkannten Befehls (``None`` = nicht angegeben).
CommandData = dict[str, str | None]
#: Handler: (Absätze, Befehl, Gruppen, Folgezeile, Umnummerierung) → (Problem, verbrauchte Zeilen).
CommandHandler = Callable[
    [list[LawParagraph], str, CommandData, str | None, bool], tuple[str | None, int]
]


def _apply_replace(
    paragraphs: list[LawParagraph],
    command: str,
    data: CommandData,
    next_line: str | None,
    renumber: bool,
) -> tuple[str | None, int]:
    target = _find(paragraphs, data["section"] or "", data.get("paragraph") or 0)
    if target is None:
        return "Zielstelle nicht gefunden", 0
    basis = target.new_text if target.new_text is not None else target.text
    old_value = data.get("old") or ""
    if old_value not in basis:
        return "zu ersetzender Wortlaut nicht gefunden", 0
    # Jedes Vorkommen im Absatz wird ersetzt (DC-L02, entschieden D2).
    target.new_text = basis.replace(old_value, data.get("new") or "")
    _append_command(target, command)
    return None, 0


def _apply_repeal(
    paragraphs: list[LawParagraph],
    command: str,
    data: CommandData,
    next_line: str | None,
    renumber: bool,
) -> tuple[str | None, int]:
    section = data["section"] or ""
    paragraph = data.get("paragraph")
    if paragraph:
        found = _find(paragraphs, section, paragraph)
        targets = [found] if found else []
    else:
        wanted = _normalise_section(section)
        targets = [item for item in paragraphs if _normalise_section(item.section) == wanted]
    if not targets:
        return "Zielstelle nicht gefunden", 0
    for target in targets:
        target.repealed = True
        target.new_text = ""
        _append_command(target, command)
    return None, 0


def _apply_recast(
    paragraphs: list[LawParagraph],
    command: str,
    data: CommandData,
    next_line: str | None,
    renumber: bool,
) -> tuple[str | None, int]:
    target = _find(paragraphs, data["section"] or "", data.get("paragraph") or 0)
    if target is None or next_line is None:
        return "Neufassung nicht eindeutig gefunden", 0
    target.new_text = _quoted_text(next_line)
    _append_command(target, command)
    return None, 1


def _apply_insert(
    paragraphs: list[LawParagraph],
    command: str,
    data: CommandData,
    next_line: str | None,
    renumber: bool,
) -> tuple[str | None, int]:
    target = _find(paragraphs, data["section"] or "", data.get("paragraph") or 0)
    if target is None or next_line is None:
        return "Einfügung nicht eindeutig gefunden", 0
    new_number = int(data.get("new_number") or target.paragraph + 1)
    inserted = LawParagraph(
        section=target.section,
        paragraph=new_number,
        text="",
        new_text=_quoted_text(next_line),
        command=command,
        inserted=True,
    )
    position = paragraphs.index(target) + 1
    if renumber:
        section_key = _normalise_section(target.section)
        for item in paragraphs[position:]:
            if _normalise_section(item.section) == section_key and item.paragraph >= new_number:
                item.paragraph += 1
    # Legacy: nachfolgende Absätze werden nicht umnummeriert (DC-L01).
    paragraphs.insert(position, inserted)
    return None, 1


COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "replace": _apply_replace,
    "repeal": _apply_repeal,
    "recast": _apply_recast,
    "insert": _apply_insert,
}


def _match_command(command: str) -> tuple[str, CommandData] | None:
    """Erstes passendes Befehlsmuster (Reihenfolge von ``COMMAND_PATTERNS``)."""
    for command_type, pattern in COMMAND_PATTERNS:
        match = pattern.match(command)
        if match is not None:
            return command_type, match.groupdict()
    return None


def _looks_like_unsupported_command(command: str) -> bool:
    return bool(_UNSUPPORTED_START.match(command) and _UNSUPPORTED_VERB.search(command))


def apply_commands(
    paragraphs: list[LawParagraph], commands: list[str], *, renumber_after_insert: bool = False
) -> tuple[list[LawParagraph], list[str], int]:
    """Befehle der Reihe nach anwenden; nicht anwendbare bleiben offen.

    ``renumber_after_insert`` (Entscheidung D2): Nach einer Einfügung rücken die
    folgenden Absätze desselben Paragrafen ab der neuen Nummer um eins auf;
    spätere Befehle beziehen sich auf die neue Zählung.
    """
    open_commands: list[str] = []
    recognised = 0
    index = 0
    while index < len(commands):
        command = commands[index]
        next_line = commands[index + 1] if index + 1 < len(commands) else None
        matched = _match_command(command)
        consumed = 0
        if matched is not None:
            command_type, data = matched
            handler = COMMAND_HANDLERS[command_type]
            problem, consumed = handler(paragraphs, command, data, next_line, renumber_after_insert)
            if problem is None:
                recognised += 1
            else:
                open_commands.append(f"{command} [{problem}]")
        elif _looks_like_unsupported_command(command):
            open_commands.append(f"{command} [Befehlsart nicht unterstützt]")
        index += 1 + consumed
    return paragraphs, open_commands, recognised


def article_law_result(
    paragraphs: list[LawParagraph],
    open_commands: list[str],
    recognised: int,
    *,
    old_filename: str,
    new_filename: str,
    old_sha256: str,
    new_sha256: str,
    version: str,
    now: Callable[[], datetime],
) -> ComparisonResult:
    """Ergebnis mit Synopsezeilen und konsolidierter Arbeitsfassung."""
    rows: list[CompareRow] = []
    for item in paragraphs:
        if item.inserted:
            status = "added"
        elif item.repealed:
            status = "removed"
        elif item.new_text is not None:
            status = "changed"
        else:
            continue
        rows.append(
            CompareRow(
                row_id=f"law-{len(rows)}",
                status=status,
                location=item.location,
                old_text=item.text,
                new_text=item.new_text or "",
                reason=item.command,
                reason_source="article_law",
            )
        )
    consolidated: list[dict[str, Any]] = [
        {
            "section": item.section,
            "paragraph": item.paragraph,
            "text": item.text if item.new_text is None else item.new_text,
            "repealed": item.repealed,
            "inserted": item.inserted,
        }
        for item in paragraphs
    ]
    return ComparisonResult(
        version=version,
        mode="text",
        old_filename=old_filename,
        new_filename=new_filename,
        old_sha256=old_sha256,
        new_sha256=new_sha256,
        old_count=len([item for item in paragraphs if not item.inserted]),
        new_count=len([item for item in paragraphs if not item.repealed]),
        matched_count=len(rows),
        changed_count=sum(row.status == "changed" for row in rows),
        removed_count=sum(row.status == "removed" for row in rows),
        added_count=sum(row.status == "added" for row in rows),
        rows=rows,
        created_at=now().isoformat(),
        metadata={
            "comparison_type": "article_law",
            "old_label": "Geltende Fassung",
            "new_label": "Fassung nach dem Entwurf",
            "reason_label": "Änderungsbefehl",
            "recognised_commands": recognised,
            "open_commands": open_commands,
            "open_command_count": len(open_commands),
            "consolidated_text": consolidated,
            "work_aid_notice": WORK_AID_NOTICE,
        },
    )
