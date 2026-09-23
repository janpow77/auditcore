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


def apply_commands(
    paragraphs: list[LawParagraph], commands: list[str]
) -> tuple[list[LawParagraph], list[str], int]:
    """Befehle der Reihe nach anwenden; nicht anwendbare bleiben offen."""
    open_commands: list[str] = []
    recognised = 0
    index = 0
    while index < len(commands):
        command = commands[index]
        recognised_here = False
        for command_type, pattern in COMMAND_PATTERNS:
            match = pattern.match(command)
            if match is None:
                continue
            recognised_here = True
            data = match.groupdict()
            section = data["section"]
            paragraph = data.get("paragraph")
            if command_type == "replace":
                target = _find(paragraphs, section, paragraph or 0)
                if target is None:
                    open_commands.append(f"{command} [Zielstelle nicht gefunden]")
                    break
                basis = target.new_text if target.new_text is not None else target.text
                old_value = data.get("old") or ""
                if old_value not in basis:
                    open_commands.append(f"{command} [zu ersetzender Wortlaut nicht gefunden]")
                    break
                # Legacy: jedes Vorkommen im Absatz wird ersetzt (DC-L02).
                target.new_text = basis.replace(old_value, data.get("new") or "")
                _append_command(target, command)
                recognised += 1
            elif command_type == "repeal":
                if paragraph:
                    found = _find(paragraphs, section, paragraph)
                    targets = [found] if found else []
                else:
                    targets = [
                        item
                        for item in paragraphs
                        if _normalise_section(item.section) == _normalise_section(section)
                    ]
                if not targets:
                    open_commands.append(f"{command} [Zielstelle nicht gefunden]")
                    break
                for target in targets:
                    target.repealed = True
                    target.new_text = ""
                    _append_command(target, command)
                recognised += 1
            elif command_type == "recast":
                target = _find(paragraphs, section, paragraph or 0)
                if target is None or index + 1 >= len(commands):
                    open_commands.append(f"{command} [Neufassung nicht eindeutig gefunden]")
                    break
                target.new_text = _quoted_text(commands[index + 1])
                _append_command(target, command)
                index += 1
                recognised += 1
            elif command_type == "insert":
                target = _find(paragraphs, section, paragraph or 0)
                if target is None or index + 1 >= len(commands):
                    open_commands.append(f"{command} [Einfügung nicht eindeutig gefunden]")
                    break
                new_number = int(data.get("new_number") or target.paragraph + 1)
                inserted = LawParagraph(
                    section=target.section,
                    paragraph=new_number,
                    text="",
                    new_text=_quoted_text(commands[index + 1]),
                    command=command,
                    inserted=True,
                )
                # Legacy: nachfolgende Absätze werden nicht umnummeriert (DC-L01).
                paragraphs.insert(paragraphs.index(target) + 1, inserted)
                index += 1
                recognised += 1
            break
        if (
            not recognised_here
            and _UNSUPPORTED_START.match(command)
            and _UNSUPPORTED_VERB.search(command)
        ):
            open_commands.append(f"{command} [Befehlsart nicht unterstützt]")
        index += 1
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
