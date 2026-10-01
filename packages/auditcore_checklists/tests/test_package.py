"""Tests für Paket-Export, Normalisierung, Validierung und Import."""

from __future__ import annotations

from auditcore_checklists import (
    FORMAT_VERSION,
    PACKAGE_FORMAT,
    CategoryDefinition,
    ChecklistTree,
    ProjectMetadata,
    export_package,
    import_package,
    normalize_package_payload,
    validate_package,
)


def test_export_package(
    sample_project: ProjectMetadata,
    populated_tree: tuple[ChecklistTree, dict[str, str]],
    sample_categories: dict[str, CategoryDefinition],
) -> None:
    tree, _ = populated_tree
    pkg = export_package(
        project=sample_project,
        tree=tree,
        categories=sample_categories,
        version_number="1.0",
        notes="Erstfassung Prüfkatalog",
    )

    assert pkg["format"] == PACKAGE_FORMAT
    assert pkg["format_version"] == FORMAT_VERSION
    assert str(pkg["checksum"]).startswith("sha256:")
    assert isinstance(pkg["project"], dict)
    assert pkg["project"]["name"] == sample_project.name
    assert isinstance(pkg["categories"], dict)
    assert "cat_1" in pkg["categories"]
    assert isinstance(pkg["versions"], list)
    assert len(pkg["versions"]) == 1
    v0 = pkg["versions"][0]
    assert isinstance(v0, dict)
    assert v0["version_number"] == "1.0"


def test_validate_package_rules() -> None:
    # Gültiges Minimal-Paket
    valid_pkg = {
        "format": PACKAGE_FORMAT,
        "format_version": FORMAT_VERSION,
        "project": {"name": "Test"},
        "versions": [{"tree_data": {"root_id": "r", "nodes": {}}}],
    }
    assert len(validate_package(valid_pkg)) == 0

    # Falsches Format
    assert len(validate_package({"format": "wrong"})) > 0

    # Fehlende Versionen
    invalid_pkg = {
        "format": PACKAGE_FORMAT,
        "format_version": 1,
        "project": {"name": "T"},
    }
    assert len(validate_package(invalid_pkg)) > 0


def test_normalize_legacy_full_backup(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, _ = populated_tree
    legacy_payload = {
        "export_type": "full_backup",
        "project": {
            "name": "Altsicherung 2025",
            "current_version": "0.9",
        },
        "tree_data": tree.to_dict(),
    }
    normalized = normalize_package_payload(legacy_payload)

    assert normalized["format"] == PACKAGE_FORMAT
    assert isinstance(normalized["project"], dict)
    assert normalized["project"]["name"] == "Altsicherung 2025"
    assert isinstance(normalized["versions"], list)
    assert len(normalized["versions"]) == 1
    v0 = normalized["versions"][0]
    assert isinstance(v0, dict)
    assert v0["version_number"] == "0.9"


def test_normalize_raw_tree(
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, _ = populated_tree
    raw_payload = tree.to_dict()

    normalized = normalize_package_payload(raw_payload, fallback_name="Aus Rohem Baum")

    assert normalized["format"] == PACKAGE_FORMAT
    assert isinstance(normalized["project"], dict)
    assert normalized["project"]["name"] == "Aus Rohem Baum"
    assert isinstance(normalized["versions"], list)
    assert len(normalized["versions"]) == 1


def test_import_package_roundtrip(
    sample_project: ProjectMetadata,
    populated_tree: tuple[ChecklistTree, dict[str, str]],
    sample_categories: dict[str, CategoryDefinition],
) -> None:
    tree, _ = populated_tree
    pkg = export_package(
        project=sample_project,
        tree=tree,
        categories=sample_categories,
        version_number="1.0",
    )

    project, imported_tree, categories = import_package(pkg)

    assert project.name == sample_project.name
    assert project.aktenzeichen == sample_project.aktenzeichen
    assert project.tags == sample_project.tags
    assert imported_tree.root_id == tree.root_id
    assert len(imported_tree.nodes) == len(tree.nodes)
    assert "cat_1" in categories
    assert categories["cat_1"].name == "Verfahrensart"
    assert len(categories["cat_1"].items) == 3
