"""Serialisierung und Deserialisierung von Baumknoten und Inhalten."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .errors import JsonObject, to_int, to_json_value
from .models import (
    AnswerType,
    ChecklistNode,
    NodeContent,
    NodeInternal,
    NodeType,
    TeamNote,
)


def parse_content(raw: Mapping[str, object] | None) -> NodeContent:
    """Extrahiert fachliche Inhalte eines Baumknotens."""
    if not raw:
        return NodeContent(title="Unbenannt")
    title = str(raw.get("title", ""))
    atype_raw = raw.get("answer_type")
    atype = AnswerType(str(atype_raw)) if atype_raw else None
    raw_opts = raw.get("answer_options")
    opts = tuple(str(x) for x in raw_opts) if isinstance(raw_opts, (list, tuple)) else ()
    cid = raw.get("category_id")
    raw_hints = raw.get("hints")
    hints = tuple(str(x) for x in raw_hints) if isinstance(raw_hints, (list, tuple)) else ()
    pub_remark = str(raw["public_remark"]) if raw.get("public_remark") is not None else None
    snippets_raw = raw.get("remark_snippets")
    snippets: dict[str, str] = {}
    if isinstance(snippets_raw, Mapping):
        snippets = {str(k): str(v) for k, v in snippets_raw.items()}
    qtype = raw.get("qchess_eingabetyp")
    valid_qtype = qtype if isinstance(qtype, int) and not isinstance(qtype, bool) else None
    return NodeContent(
        title=title,
        answer_type=atype,
        answer_options=opts,
        category_id=cid if isinstance(cid, (int, str)) and not isinstance(cid, bool) else None,
        hints=hints,
        public_remark=pub_remark,
        remark_snippets=snippets,
        qchess_eingabetyp=valid_qtype,
        qchess_antwortset_id=str(raw["qchess_antwortset_id"])
        if raw.get("qchess_antwortset_id")
        else None,
        qchess_ja_label=str(raw["qchess_ja_label"]) if raw.get("qchess_ja_label") else None,
        qchess_nein_label=str(raw["qchess_nein_label"]) if raw.get("qchess_nein_label") else None,
    )


def parse_team_notes(raw_notes: Sequence[object]) -> tuple[TeamNote, ...]:
    """Parst Teamnotizen eines Knotens."""
    notes: list[TeamNote] = []
    for item in raw_notes:
        if isinstance(item, Mapping):
            notes.append(
                TeamNote(
                    id=str(item.get("id", "")),
                    username=str(item.get("username", "")),
                    message=str(item.get("message", "")),
                    timestamp=str(item.get("timestamp", "")),
                    user_id=item.get("user_id")
                    if isinstance(item.get("user_id"), (int, str))
                    else None,
                    parent_note_id=str(item["parent_note_id"])
                    if item.get("parent_note_id")
                    else None,
                )
            )
    return tuple(notes)


def parse_internal(raw: Mapping[str, object] | None) -> NodeInternal:
    """Parst interne Metadaten eines Baumknotens."""
    if not raw:
        return NodeInternal()
    notes_raw = raw.get("team_notes")
    notes = parse_team_notes(notes_raw) if isinstance(notes_raw, Sequence) else ()
    cby = raw.get("created_by")
    valid_cby = cby if isinstance(cby, (int, str)) and not isinstance(cby, bool) else None
    return NodeInternal(
        team_notes=notes,
        status=str(raw.get("status", "pending")),
        created_at=str(raw["created_at"]) if raw.get("created_at") else None,
        updated_at=str(raw["updated_at"]) if raw.get("updated_at") else None,
        created_by=valid_cby,
    )


def content_to_dict(c: NodeContent) -> JsonObject:
    """Wandelt NodeContent in ein JSON-kompatibles Wörterbuch."""
    return {
        "title": c.title,
        "answer_type": c.answer_type.value if c.answer_type else None,
        "answer_options": list(c.answer_options) if c.answer_options else None,
        "category_id": c.category_id,
        "hints": list(c.hints),
        "public_remark": c.public_remark,
        "remark_snippets": dict(c.remark_snippets) if c.remark_snippets else None,
        "qchess_eingabetyp": c.qchess_eingabetyp,
        "qchess_antwortset_id": c.qchess_antwortset_id,
        "qchess_ja_label": c.qchess_ja_label,
        "qchess_nein_label": c.qchess_nein_label,
    }


def node_to_dict(node: ChecklistNode) -> JsonObject:
    """Wandelt ChecklistNode in ein serialisierbares JSON-Wörterbuch."""
    internal_dict: JsonObject = {
        "team_notes": [
            {
                "id": tn.id,
                "user_id": tn.user_id,
                "username": tn.username,
                "message": tn.message,
                "timestamp": tn.timestamp,
                "parent_note_id": tn.parent_note_id,
            }
            for tn in node.internal.team_notes
        ],
        "status": node.internal.status,
        "created_at": node.internal.created_at,
        "updated_at": node.internal.updated_at,
        "created_by": node.internal.created_by,
    }
    return {
        "id": node.id,
        "node_type": node.node_type.value,
        "parent_id": node.parent_id,
        "branch": node.branch,
        "sort_order": node.sort_order,
        "content": content_to_dict(node.content),
        "internal": internal_dict,
        "children": [to_json_value(cid) for cid in node.children],
    }


def parse_node_dict(nid_str: str, raw_node: Mapping[str, object]) -> ChecklistNode:
    """Deserialisiert ein Wörterbuch in einen ChecklistNode."""
    ntype = NodeType(str(raw_node.get("node_type", NodeType.HEADING.value)))
    pid = str(raw_node["parent_id"]) if raw_node.get("parent_id") else None
    branch = str(raw_node["branch"]) if raw_node.get("branch") else None
    s_order = to_int(raw_node.get("sort_order"), 0)
    raw_children = raw_node.get("children")
    children = (
        tuple(str(c) for c in raw_children) if isinstance(raw_children, (list, tuple)) else ()
    )
    raw_content = raw_node.get("content")
    content_map = raw_content if isinstance(raw_content, Mapping) else None
    raw_internal = raw_node.get("internal")
    internal_map = raw_internal if isinstance(raw_internal, Mapping) else None
    return ChecklistNode(
        id=str(nid_str),
        node_type=ntype,
        parent_id=pid,
        branch=branch,
        sort_order=s_order,
        content=parse_content(content_map),
        internal=parse_internal(internal_map),
        children=children,
    )
