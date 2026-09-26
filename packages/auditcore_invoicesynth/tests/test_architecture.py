"""Kern nur Standardbibliothek + eigene Pakete; Pillow nur verzögert in Render-Modulen."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import auditcore_invoicesynth

PACKAGE = Path(auditcore_invoicesynth.__file__).parent
ALLOWED = {"auditcore_invoicesynth", "auditcore_invoicegenerator"}
TORCH_ADAPTERS = {"torch_backend.py", "torch_predict.py"}
LAZY_PIL = {"render.py", "augment.py", "dataset.py", *TORCH_ADAPTERS}
#: Extra ``train``: nur verzögert und nur in den Torch-Adaptern.
TRAIN_ONLY = {"torch", "transformers", "tokenizers", "safetensors", "bitsandbytes"}


def test_imports() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = {id(n) for n in tree.body}
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            for name in names:
                root = name.split(".")[0]
                if root in TRAIN_ONLY:
                    assert path.name in TORCH_ADAPTERS, path.name
                    assert id(node) not in top_level, f"{path.name}: {root} nur verzögert"
                elif root == "PIL":
                    assert path.name in LAZY_PIL, path.name
                    assert id(node) not in top_level, f"{path.name}: PIL nur verzögert"
                else:
                    assert root in stdlib or root in ALLOWED, f"{path.name}: {name}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}


def test_no_fonts_or_images_are_distributed() -> None:
    for pattern in ("*.ttf", "*.otf", "*.png", "*.jpg"):
        assert not list(PACKAGE.rglob(pattern)), pattern


def test_provenance_copies_match_and_carry_the_rights_block() -> None:
    packaged = json.loads((PACKAGE / "provenance.json").read_text(encoding="utf-8"))
    top = PACKAGE.parents[1] / "provenance.json"
    if top.is_file():
        assert json.loads(top.read_text(encoding="utf-8")) == packaged
    authorization = packaged["rights"]["authorization"]
    assert authorization["status"] == "USER_AUTHORIZED_MIT"
    assert authorization["date"] == "2026-09-22"
    assert packaged["sources"] == []
    assert packaged["decisions"]["confirmation"] == "Donut alle Empfehlungen"
