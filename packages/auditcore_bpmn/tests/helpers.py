"""Gemeinsame Hilfen: kleine BPMN-Dokumente aus Bausteinen (alle Daten synthetisch)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
FA = "https://flowaudit.de/bpmn/schema/1.0"
FIXTURES = Path(__file__).parent / "fixtures"
STICHTAG = date(2026, 9, 25)


def ext(*children: str) -> str:
    """``bpmn:extensionElements`` mit FlowAudit-Kindern."""
    return "<bpmn:extensionElements>" + "".join(children) + "</bpmn:extensionElements>"


def doc(body: str, *, collaboration: str = "", process: str = 'id="P1"', extra_ns: str = "") -> str:
    """Vollständiges Dokument; ``collaboration`` ist der Inhalt von ``bpmn:collaboration``."""
    collab = f'<bpmn:collaboration id="C1">{collaboration}</bpmn:collaboration>' if collaboration else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<bpmn:definitions xmlns:bpmn="{BPMN}" xmlns:flowaudit="{FA}"{extra_ns} id="D1" targetNamespace="urn:test">'
        f"{collab}<bpmn:process {process}>{body}</bpmn:process></bpmn:definitions>"
    )


def flow(fid: str, source: str, target: str, condition: str | None = None) -> str:
    inner = f"<bpmn:conditionExpression>{condition}</bpmn:conditionExpression>" if condition else ""
    return f'<bpmn:sequenceFlow id="{fid}" sourceRef="{source}" targetRef="{target}">{inner}</bpmn:sequenceFlow>'


def linear(*nodes: str, start: str = "S", end: str = "E") -> str:
    """Start → Aufgaben ``nodes`` (IDs) → Ende, jeweils als ``bpmn:task``."""
    ids = [start, *nodes, end]
    parts = [f'<bpmn:startEvent id="{start}"/>', f'<bpmn:endEvent id="{end}"/>']
    parts += [f'<bpmn:task id="{node}" name="Aufgabe {node}"/>' for node in nodes]
    parts += [flow(f"F{index}", a, b) for index, (a, b) in enumerate(zip(ids, ids[1:], strict=False), start=1)]
    return "".join(parts)


INFO_OK = (
    '<flowaudit:diagrammInfo schemaVersion="1.1" profil="foerderperiode-2021-2027" titel="Beispielprozess" '
    'status="entwurf" foerderperiode="2021-2027"/>'
)


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def task(task_id: str, *children: str, name: str = "A") -> str:
    """``bpmn:task`` mit FlowAudit-Kindern in ``extensionElements``."""
    inner = ext(*children) if children else ""
    return f'<bpmn:task id="{task_id}" name="{name}">{inner}</bpmn:task>'


def linear_with(*children: str) -> str:
    """Start → T1 (mit ``children``) → Ende als Prozessinhalt."""
    return linear("T1").replace('<bpmn:task id="T1" name="Aufgabe T1"/>', task("T1", *children))
