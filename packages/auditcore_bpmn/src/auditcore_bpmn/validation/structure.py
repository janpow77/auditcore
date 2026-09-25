"""Strukturregeln (``BPMN-S…``): Aufbau, Flüsse, Gateways, Ereignisse."""

from __future__ import annotations

from collections.abc import Iterator

from ..model import BpmnElement
from .context import ValidationContext
from .issues import ValidationIssue, issue
from .registry import rule

Issues = Iterator[ValidationIssue]


@rule("structure", "BPMN-S001")
def check_root(ctx: ValidationContext) -> Issues:
    """BPMN-S001: Wurzel ist ``bpmn:definitions``."""
    if not ctx.document.is_bpmn:
        yield issue("BPMN-S001")


@rule("structure", "BPMN-S002")
def check_has_process(ctx: ValidationContext) -> Issues:
    """BPMN-S002: mindestens ein Prozess oder eine Kollaboration."""
    if not ctx.document.processes and not ctx.document.by_type("collaboration"):
        yield issue("BPMN-S002")


@rule("structure", "BPMN-S003")
def check_duplicate_ids(ctx: ValidationContext) -> Issues:
    """BPMN-S003: IDs eindeutig."""
    for duplicate in dict.fromkeys(ctx.document.duplicate_ids):
        yield issue("BPMN-S003", duplicate, id=duplicate)


@rule("structure", "BPMN-S010", "BPMN-S011")
def check_start_and_end_events(ctx: ValidationContext) -> Issues:
    """BPMN-S010/S011: Prozesse mit Start- und Endereignis."""
    for process in ctx.document.processes:
        types = {e.type for e in ctx.document.flow_nodes if e.parent_id == process.id}
        if not types:
            continue
        if "startEvent" not in types:
            yield issue("BPMN-S010", process.id, name=process.label)
        if "endEvent" not in types:
            yield issue("BPMN-S011", process.id, name=process.label)


@rule("structure", "BPMN-S020", "BPMN-S021", "BPMN-S022")
def check_sequence_flow_ends(ctx: ValidationContext) -> Issues:
    """BPMN-S020/S021/S022: Sequenzflüsse verbunden, bekannt, innerhalb einer Ebene."""
    elements = ctx.document.elements
    for flow in ctx.document.sequence_flows:
        if not flow.source or not flow.target:
            yield issue("BPMN-S020", flow.id, id=flow.id)
        for ref in (flow.source, flow.target):
            if ref and ref not in elements:
                yield issue("BPMN-S021", flow.id, id=flow.id, ref=ref)
        source, target = elements.get(flow.source or ""), elements.get(flow.target or "")
        if source and target and source.parent_id != target.parent_id:
            yield issue("BPMN-S022", flow.id, id=flow.id)


@rule("structure", "BPMN-S023", "BPMN-S024")
def check_message_flows(ctx: ValidationContext) -> Issues:
    """BPMN-S023/S024: Nachrichtenflüsse zwischen verschiedenen Pools."""
    document = ctx.document
    for flow in document.message_flows:
        source, target = document.elements.get(flow.source or ""), document.elements.get(flow.target or "")
        if source is None or target is None:
            yield issue("BPMN-S024", flow.id, id=flow.id)
            continue
        pool = document.participant_of(source)
        if pool is not None and pool is document.participant_of(target):
            yield issue("BPMN-S023", flow.id, id=flow.id)


@rule("structure", "BPMN-S070", "BPMN-S071")
def check_associations(ctx: ValidationContext) -> Issues:
    """BPMN-S070/S071: Daten- und Assoziationen verweisen auf bekannte Elemente."""
    document = ctx.document
    for connection in document.by_type("dataInputAssociation", "dataOutputAssociation", "association"):
        rule_id = "BPMN-S071" if connection.type == "association" else "BPMN-S070"
        for ref in (connection.source, connection.target):
            if ref and ref not in document.elements:
                yield issue(rule_id, connection.id, id=connection.id, ref=ref)


def _exempt(ctx: ValidationContext, node: BpmnElement) -> bool:
    """Knoten, für die fehlende Sequenzflüsse zulässig sind."""
    parent = ctx.document.elements.get(node.parent_id or "")
    in_ad_hoc = parent is not None and parent.type == "adHocSubProcess"
    return node.type == "boundaryEvent" or node.is_compensation or in_ad_hoc


def _needs_incoming(ctx: ValidationContext, node: BpmnElement) -> bool:
    link_catch = node.type == "intermediateCatchEvent" and node.link_name is not None
    return node.type != "startEvent" and not link_catch


def _needs_outgoing(node: BpmnElement) -> bool:
    link_throw = node.type == "intermediateThrowEvent" and node.link_name is not None
    return node.type != "endEvent" and not link_throw


def _orphan_allowed(ctx: ValidationContext, node: BpmnElement, messages: set[str]) -> bool:
    parent = ctx.document.elements.get(node.parent_id or "")
    event_start = node.type == "startEvent" and parent is not None and parent.is_event_subprocess
    return node.id in messages or event_start


@rule("structure", "BPMN-S012", "BPMN-S013", "BPMN-S014")
def check_node_connections(ctx: ValidationContext) -> Issues:
    """BPMN-S012/S013/S014: keine verwaisten Knoten, Ein- und Ausgänge vorhanden."""
    messages = {ref for f in ctx.document.message_flows for ref in (f.source, f.target) if ref}
    for node in ctx.document.flow_nodes:
        if _exempt(ctx, node):
            continue
        has_in, has_out = bool(ctx.incoming(node.id)), bool(ctx.outgoing(node.id))
        if not has_in and not has_out:
            if not _orphan_allowed(ctx, node, messages):
                yield issue("BPMN-S012", node.id, name=node.label)
            continue
        if not has_in and _needs_incoming(ctx, node):
            yield issue("BPMN-S013", node.id, name=node.label)
        if not has_out and _needs_outgoing(node):
            yield issue("BPMN-S014", node.id, name=node.label)


@rule("structure", "BPMN-S015", "BPMN-S016")
def check_start_end_flows(ctx: ValidationContext) -> Issues:
    """BPMN-S015/S016: Start ohne Eingang, Ende ohne Ausgang."""
    for node in ctx.document.by_type("startEvent"):
        if ctx.incoming(node.id):
            yield issue("BPMN-S015", node.id, name=node.label)
    for node in ctx.document.by_type("endEvent"):
        if ctx.outgoing(node.id):
            yield issue("BPMN-S016", node.id, name=node.label)


@rule("structure", "BPMN-S050")
def check_task_names(ctx: ValidationContext) -> Issues:
    """BPMN-S050: Aufgaben beschriftet."""
    for node in ctx.document.flow_nodes:
        if node.is_task and not (node.name or "").strip():
            yield issue("BPMN-S050", node.id, id=node.id)


@rule("structure", "BPMN-S031")
def check_default_flows(ctx: ValidationContext) -> Issues:
    """BPMN-S031: Default-Fluss ist ausgehender Fluss."""
    for node in ctx.document.flow_nodes:
        if node.default and node.default not in {f.id for f in ctx.outgoing(node.id)}:
            yield issue("BPMN-S031", node.id, flow=node.default, name=node.label)


@rule("structure", "BPMN-S030", "BPMN-S032", "BPMN-S051")
def check_branching_gateways(ctx: ValidationContext) -> Issues:
    """BPMN-S030/S032/S051: verzweigende Gateways mit Default und Frage."""
    for node in ctx.document.by_type("exclusiveGateway", "inclusiveGateway"):
        outgoing = ctx.outgoing(node.id)
        if len(outgoing) < 2:
            continue
        conditional = any(f.condition is not None for f in outgoing)
        if not node.default:
            yield issue("BPMN-S030" if conditional else "BPMN-S032", node.id, name=node.label)
        if not (node.name or "").strip():
            yield issue("BPMN-S051", node.id, id=node.id)


@rule("structure", "BPMN-S035")
def check_parallel_conditions(ctx: ValidationContext) -> Issues:
    """BPMN-S035: parallele Gateways ohne Bedingungen."""
    for node in ctx.document.by_type("parallelGateway"):
        if any(f.condition is not None for f in ctx.outgoing(node.id)):
            yield issue("BPMN-S035", node.id, name=node.label)


@rule("structure", "BPMN-S033")
def check_redundant_gateways(ctx: ValidationContext) -> Issues:
    """BPMN-S033: Gateways mit genau einem Ein- und Ausgang."""
    for node in ctx.document.flow_nodes:
        if node.category == "gateway" and len(ctx.incoming(node.id)) == 1 and len(ctx.outgoing(node.id)) == 1:
            yield issue("BPMN-S033", node.id, name=node.label)


@rule("structure", "BPMN-S034")
def check_event_based_targets(ctx: ValidationContext) -> Issues:
    """BPMN-S034: ereignisbasierte Gateways führen zu Ereignissen/Empfangsaufgaben."""
    allowed = ("intermediateCatchEvent", "receiveTask")
    for node in ctx.document.by_type("eventBasedGateway"):
        for flow in ctx.outgoing(node.id):
            target = ctx.document.elements.get(flow.target or "")
            if target is not None and target.type not in allowed:
                yield issue("BPMN-S034", node.id, name=node.label, ziel=target.label)


@rule("structure", "BPMN-S040", "BPMN-S041", "BPMN-S042")
def check_boundary_events(ctx: ValidationContext) -> Issues:
    """BPMN-S040/S041/S042: Randereignisse angeheftet, mit Ausgang, ohne Eingang."""
    for event in ctx.document.by_type("boundaryEvent"):
        host = ctx.document.elements.get(event.attached_to or "")
        if host is None or not host.is_activity:
            yield issue("BPMN-S042", event.id, name=event.label)
        compensation = "compensateEventDefinition" in event.event_definitions
        if not ctx.outgoing(event.id) and not compensation:
            yield issue("BPMN-S040", event.id, name=event.label)
        if ctx.incoming(event.id):
            yield issue("BPMN-S041", event.id, name=event.label)


@rule("structure", "BPMN-S060")
def check_links(ctx: ValidationContext) -> Issues:
    """BPMN-S060: Link-Wurf hat ein Link-Fangereignis."""
    document = ctx.document
    catches = {(e.process_id, e.link_name) for e in document.by_type("intermediateCatchEvent") if e.link_name}
    for event in document.by_type("intermediateThrowEvent"):
        if event.link_name is not None and (event.process_id, event.link_name) not in catches:
            yield issue("BPMN-S060", event.id, name=event.label, link=event.link_name)


@rule("structure", "BPMN-S061")
def check_call_activities(ctx: ValidationContext) -> Issues:
    """BPMN-S061: Aufrufaktivität nennt ein Ziel."""
    for call in ctx.document.by_type("callActivity"):
        if not call.called_element:
            yield issue("BPMN-S061", call.id, name=call.label)
