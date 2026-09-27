"""Static check of placeholders, conditions and loops against the data contract.

Every data path a template reads must be declared in its JSON schema (loop
variables resolve to the item schema of their list). Unknown paths, unknown
text blocks and unreferenced Pflichtbausteine are errors at definition time –
the strict counterpart of Jinja's ``StrictUndefined``.
"""

from __future__ import annotations

from collections.abc import Mapping

from .conditions import Condition, condition_paths
from .errors import TemplateError
from .model import TextBlock
from .placeholders import placeholders
from .schema import item_schema, subschema

Bindings = Mapping[str, Mapping[str, object]]
_RESERVED = frozenset({"textbaustein"})


class Checker:
    """Walks a template once; records which text blocks are referenced."""

    def __init__(
        self,
        schema: Mapping[str, object],
        conditions: Mapping[str, Condition],
        text_blocks: tuple[TextBlock, ...],
    ) -> None:
        self.schema = schema
        self.conditions = conditions
        self.blocks = {block.id: block for block in text_blocks}
        self.used: set[str] = set()

    def path(self, path: str, bindings: Bindings, where: str) -> Mapping[str, object]:
        """Schema of ``path``; loop variables shadow top-level properties."""
        head, *rest = path.split(".")
        if head in bindings:
            found = subschema(bindings[head], rest)
        else:
            found = subschema(self.schema, [head, *rest])
        if found is None:
            raise TemplateError(
                f"{where}: Datenpfad {path!r} ist im Datenvertrag nicht deklariert."
            )
        return found

    def text(self, text: str, bindings: Bindings, where: str) -> None:
        """Check every placeholder of ``text``."""
        for placeholder in placeholders(text, where):
            if placeholder.block is not None:
                self.block_ref(placeholder.block, bindings, where)
            else:
                self.path(placeholder.path, bindings, where)

    def condition(self, spec: Condition | None, bindings: Bindings, where: str) -> None:
        """Check the data paths read by a condition."""
        if spec is None:
            return
        for path in condition_paths(spec, self.conditions, where):
            self.path(path, bindings, where)

    def loop(self, source: str, var: str, bindings: Bindings, where: str) -> Bindings:
        """Bindings inside a loop over the list at ``source``."""
        if var in _RESERVED or "." in var or not var.isidentifier():
            raise TemplateError(f"{where}: ungültiger Schleifenname {var!r}.")
        found = self.path(source, bindings, where)
        items = item_schema(found)
        if found.get("type") != "array" or items is None:
            raise TemplateError(f"{where}: {source!r} ist keine Liste mit 'items' im Datenvertrag.")
        return {**bindings, var: items}

    def block_ref(self, block_id: str, bindings: Bindings, where: str) -> None:
        """Check a referenced text block in the scope of its use."""
        block = self.blocks.get(block_id)
        if block is None:
            raise TemplateError(f"{where}: unbekannter Textbaustein {block_id!r}.")
        self.used.add(block_id)
        self.condition(block.condition, bindings, f"Textbaustein {block_id}")
        self.text(block.text, bindings, f"Textbaustein {block_id}")

    def finish(self) -> None:
        """Unreferenced blocks are checked at top level; Pflichtbausteine must be used."""
        for block_id, block in self.blocks.items():
            if block_id not in self.used:
                if block.required:
                    raise TemplateError(
                        f"Pflichtbaustein {block_id!r} wird in der Vorlage nicht verwendet."
                    )
                self.condition(block.condition, {}, f"Textbaustein {block_id}")
                self.text(block.text, {}, f"Textbaustein {block_id}")
