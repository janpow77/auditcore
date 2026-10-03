"""Importprüfung ausschließlich der installierten öffentlichen API."""

from auditcore_checklists import (
    AnswerType,
    ChecklistTree,
    ExecutionState,
    NodeType,
    evaluate_checklist,
)

tree = ChecklistTree.create_empty(title="Importprüfung")
tree, heading = tree.add_node(node_type=NodeType.HEADING, parent_id=tree.root_id, title="1.")
tree, question = tree.add_node(
    node_type=NodeType.QUESTION,
    parent_id=heading.id,
    title="Liegt ein Beschluss vor?",
    answer_type=AnswerType.BOOLEAN,
)
result = evaluate_checklist(tree, ExecutionState().record_answer(node_id=question.id, value=True))
assert result.is_complete is True
assert result.total_findings == 0
