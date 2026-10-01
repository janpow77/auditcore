"""Hierarchische Baumstrukturen für Checklisten mit Validierung und Navigation."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime

from .errors import (
    CycleDetectedError,
    InvalidBranchError,
    JsonObject,
    NodeNotFoundError,
    TreeStructureError,
)
from .models import (
    AnswerType,
    ChecklistNode,
    NodeContent,
    NodeInternal,
    NodeType,
    TreeValidationFinding,
)
from .tree_serialization import (
    content_to_dict,
    node_to_dict,
    parse_node_dict,
)
from .tree_validation import validate_tree_structure


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


class ChecklistTree:
    """Verwaltet einen vollständigen, hierarchischen Prüfbaum."""

    def __init__(self, root_id: str, nodes: Mapping[str, ChecklistNode]) -> None:
        self._root_id = root_id
        self._nodes: dict[str, ChecklistNode] = dict(nodes)

    @property
    def root_id(self) -> str:
        """ID des Wurzelknotens."""
        return self._root_id

    @property
    def nodes(self) -> Mapping[str, ChecklistNode]:
        """Alle Knoten des Baums als Zuordnung."""
        return self._nodes

    def get_node(self, node_id: str) -> ChecklistNode:
        """Knoten anhand seiner ID abrufen."""
        node = self._nodes.get(node_id)
        if node is None:
            raise NodeNotFoundError(node_id)
        return node

    def get_root(self) -> ChecklistNode:
        """Wurzelknoten abrufen."""
        return self.get_node(self._root_id)

    @classmethod
    def create_empty(
        cls, title: str = "Neue Checkliste", user_id: int | str | None = None
    ) -> ChecklistTree:
        """Erzeugt einen leeren Prüfbaum mit Wurzelüberschrift."""
        root_id = str(uuid.uuid4())
        now = _iso_now()
        content = NodeContent(title=title)
        internal = NodeInternal(
            status="pending",
            created_at=now,
            updated_at=now,
            created_by=user_id,
        )
        root = ChecklistNode(
            id=root_id,
            node_type=NodeType.HEADING,
            parent_id=None,
            content=content,
            internal=internal,
        )
        return cls(root_id=root_id, nodes={root_id: root})

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ChecklistTree:
        """Baum aus serialisierter Wörterbuchstruktur laden."""
        root_id = str(data.get("root_id", ""))
        raw_nodes = data.get("nodes")
        if not isinstance(raw_nodes, Mapping):
            raise TreeStructureError("Baumdaten enthalten kein gültiges 'nodes'-Objekt.")
        nodes: dict[str, ChecklistNode] = {}
        for nid_str, raw_node in raw_nodes.items():
            if isinstance(raw_node, Mapping):
                nodes[str(nid_str)] = parse_node_dict(str(nid_str), raw_node)
        if root_id not in nodes:
            raise TreeStructureError(f"Wurzelknoten '{root_id}' ist nicht in den Knoten vorhanden.")
        return cls(root_id=root_id, nodes=nodes)

    def to_dict(self) -> JsonObject:
        """Baum als serialisierbares Wörterbuch ausgeben."""
        nodes_dict: JsonObject = {nid: node_to_dict(n) for nid, n in self._nodes.items()}
        return {"root_id": self._root_id, "nodes": nodes_dict}

    def canonical_data(self) -> JsonObject:
        """Kanonische Struktur (ohne volatiles 'internal') für Prüfsummen."""
        canonical_nodes: JsonObject = {}
        for nid, n in self._nodes.items():
            canonical_nodes[nid] = {
                "node_type": n.node_type.value,
                "parent_id": n.parent_id,
                "branch": n.branch,
                "sort_order": n.sort_order,
                "content": content_to_dict(n.content),
                "children": list(n.children),
            }
        return {"root_id": self._root_id, "nodes": canonical_nodes}

    def add_node(
        self,
        node_type: NodeType,
        parent_id: str,
        title: str,
        branch: str | None = None,
        answer_type: AnswerType | None = None,
        category_id: int | str | None = None,
        hints: Sequence[str] | None = None,
        public_remark: str | None = None,
        remark_snippets: Mapping[str, str] | None = None,
        user_id: int | str | None = None,
        node_id: str | None = None,
    ) -> tuple[ChecklistTree, ChecklistNode]:
        """Neuen Knoten an einen Elternknoten anhängen."""
        parent = self.get_node(parent_id)
        if parent.node_type in (NodeType.QUESTION, NodeType.HINT):
            raise TreeStructureError("Fragen und Hinweise können keine Unterknoten besitzen.")

        eff_branch = self._validate_branch(parent, branch)
        eff_atype = self._resolve_answer_type(node_type, answer_type)

        nid = node_id or str(uuid.uuid4())
        branch_siblings = [
            self._nodes[cid]
            for cid in parent.children
            if cid in self._nodes and self._nodes[cid].branch == eff_branch
        ]
        sort_order = len(branch_siblings)

        content = NodeContent(
            title=title.strip(),
            answer_type=eff_atype,
            category_id=category_id,
            hints=tuple(hints or ()),
            public_remark=public_remark,
            remark_snippets=dict(remark_snippets or {}),
        )
        now = _iso_now()
        internal = NodeInternal(
            status="pending",
            created_at=now,
            updated_at=now,
            created_by=user_id,
        )
        new_node = ChecklistNode(
            id=nid,
            node_type=node_type,
            parent_id=parent_id,
            content=content,
            branch=eff_branch,
            sort_order=sort_order,
            internal=internal,
            children=(),
        )
        updated_parent = replace(parent, children=(*parent.children, nid))
        new_nodes = dict(self._nodes)
        new_nodes[parent_id] = updated_parent
        new_nodes[nid] = new_node
        return ChecklistTree(root_id=self._root_id, nodes=new_nodes), new_node

    def _validate_branch(self, parent: ChecklistNode, branch: str | None) -> str | None:
        if parent.node_type == NodeType.DECISION:
            if branch not in ("JA", "NEIN"):
                raise InvalidBranchError(
                    "Unterknoten einer Entscheidung erfordern 'JA' oder 'NEIN'."
                )
            return branch
        if branch is not None:
            raise InvalidBranchError(
                "Unterknoten unter Nicht-Entscheidungen dürfen keinen Zweig haben."
            )
        return None

    def _resolve_answer_type(self, ntype: NodeType, atype: AnswerType | None) -> AnswerType | None:
        if ntype == NodeType.DECISION:
            return AnswerType.BOOLEAN_JN
        if ntype in (NodeType.HEADING, NodeType.HINT):
            return None
        return atype

    def update_node(
        self,
        node_id: str,
        title: str | None = None,
        answer_type: AnswerType | None = None,
        category_id: int | str | None = None,
        hints: Sequence[str] | None = None,
        public_remark: str | None = None,
        remark_snippets: Mapping[str, str] | None = None,
        status: str | None = None,
    ) -> tuple[ChecklistTree, ChecklistNode]:
        """Inhalte oder Status eines bestehenden Knotens anpassen."""
        node = self.get_node(node_id)
        cur_c = node.content
        new_atype = (
            cur_c.answer_type
            if node.node_type == NodeType.DECISION
            else (answer_type if answer_type is not None else cur_c.answer_type)
        )
        new_content = NodeContent(
            title=title.strip() if title is not None else cur_c.title,
            answer_type=new_atype,
            answer_options=cur_c.answer_options,
            category_id=category_id if category_id is not None else cur_c.category_id,
            hints=tuple(hints) if hints is not None else cur_c.hints,
            public_remark=public_remark if public_remark is not None else cur_c.public_remark,
            remark_snippets=dict(remark_snippets)
            if remark_snippets is not None
            else cur_c.remark_snippets,
            qchess_eingabetyp=cur_c.qchess_eingabetyp,
            qchess_antwortset_id=cur_c.qchess_antwortset_id,
            qchess_ja_label=cur_c.qchess_ja_label,
            qchess_nein_label=cur_c.qchess_nein_label,
        )
        new_internal = replace(
            node.internal,
            status=status if status is not None else node.internal.status,
            updated_at=_iso_now(),
        )
        updated_node = replace(node, content=new_content, internal=new_internal)
        new_nodes = dict(self._nodes)
        new_nodes[node_id] = updated_node
        return ChecklistTree(root_id=self._root_id, nodes=new_nodes), updated_node

    def delete_node(self, node_id: str) -> ChecklistTree:
        """Knoten und alle Nachkommen rekursiv entfernen."""
        if node_id == self._root_id:
            raise TreeStructureError(
                "Wurzelknoten darf nicht gelöscht werden.", code="ROOT_DELETION_FORBIDDEN"
            )
        node = self.get_node(node_id)
        to_delete = set(self.get_subtree_ids(node_id))

        new_nodes = {nid: n for nid, n in self._nodes.items() if nid not in to_delete}
        if node.parent_id and node.parent_id in new_nodes:
            parent = new_nodes[node.parent_id]
            remaining_children = [cid for cid in parent.children if cid != node_id]
            updated_parent = replace(parent, children=tuple(remaining_children))
            new_nodes[node.parent_id] = updated_parent
            self._reindex_parent_children(new_nodes, node.parent_id)

        return ChecklistTree(root_id=self._root_id, nodes=new_nodes)

    def move_node(
        self,
        node_id: str,
        new_parent_id: str,
        new_branch: str | None = None,
        new_sort_order: int | None = None,
    ) -> ChecklistTree:
        """Knoten unter einen neuen Elternknoten verschieben."""
        if node_id == self._root_id:
            raise TreeStructureError("Wurzelknoten kann nicht verschoben werden.")
        if new_parent_id in self.get_subtree_ids(node_id):
            raise CycleDetectedError(node_id, new_parent_id)

        node = self.get_node(node_id)
        new_parent = self.get_node(new_parent_id)
        if new_parent.node_type in (NodeType.QUESTION, NodeType.HINT):
            raise TreeStructureError("Fragen und Hinweise können keine Unterknoten aufnehmen.")

        eff_branch = self._validate_branch(new_parent, new_branch)
        new_nodes = dict(self._nodes)

        # Aus altem Elternknoten entfernen
        if node.parent_id and node.parent_id in new_nodes:
            old_p = new_nodes[node.parent_id]
            new_nodes[node.parent_id] = replace(
                old_p, children=tuple(cid for cid in old_p.children if cid != node_id)
            )
            self._reindex_parent_children(new_nodes, node.parent_id)

        # In neuen Elternknoten einhängen
        curr_p = new_nodes[new_parent_id]
        new_children = list(curr_p.children)
        if new_sort_order is not None and 0 <= new_sort_order < len(new_children):
            new_children.insert(new_sort_order, node_id)
        else:
            new_children.append(node_id)

        new_nodes[new_parent_id] = replace(curr_p, children=tuple(new_children))
        new_nodes[node_id] = replace(
            node,
            parent_id=new_parent_id,
            branch=eff_branch,
            internal=replace(node.internal, updated_at=_iso_now()),
        )
        self._reindex_parent_children(new_nodes, new_parent_id)
        return ChecklistTree(root_id=self._root_id, nodes=new_nodes)

    def _reindex_parent_children(
        self, nodes_dict: dict[str, ChecklistNode], parent_id: str
    ) -> None:
        parent = nodes_dict.get(parent_id)
        if not parent:
            return
        if parent.node_type == NodeType.DECISION:
            counters: dict[str | None, int] = {}
            for cid in parent.children:
                child = nodes_dict.get(cid)
                if child:
                    idx = counters.get(child.branch, 0)
                    nodes_dict[cid] = replace(child, sort_order=idx)
                    counters[child.branch] = idx + 1
        else:
            for idx, cid in enumerate(parent.children):
                child = nodes_dict.get(cid)
                if child:
                    nodes_dict[cid] = replace(child, sort_order=idx)

    def get_children(self, node_id: str, branch: str | None = None) -> list[ChecklistNode]:
        """Gibt geordnete Kindknoten zurück, optional gefiltert nach Zweig."""
        node = self.get_node(node_id)
        result: list[ChecklistNode] = []
        for cid in node.children:
            child = self._nodes.get(cid)
            if child and (branch is None or child.branch == branch):
                result.append(child)
        result.sort(key=lambda n: n.sort_order)
        return result

    def get_subtree_ids(self, node_id: str) -> list[str]:
        """Sammelt rekursiv alle Knoten-IDs des Teilbaums."""
        result: list[str] = [node_id]
        node = self._nodes.get(node_id)
        if not node:
            return result
        for cid in node.children:
            result.extend(self.get_subtree_ids(cid))
        return result

    def validate(self) -> list[TreeValidationFinding]:
        """Vollständige Konsistenzprüfung der Baumstruktur."""
        reachable = self.get_subtree_ids(self._root_id)
        return validate_tree_structure(self._root_id, self._nodes, reachable)
