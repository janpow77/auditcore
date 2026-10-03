"""Tests für Paket-Export, Normalisierung, Validierung und Import."""

from __future__ import annotations

import pytest

from auditcore_checklists import (
    FORMAT_VERSION,
    PACKAGE_FORMAT,
    CategoryDefinition,
    ChecklistTree,
    PackageFormatError,
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


def test_export_without_discussions_with_history(
    sample_project: ProjectMetadata,
    populated_tree: tuple[ChecklistTree, dict[str, str]],
) -> None:
    tree, node_map = populated_tree
    qid = node_map["question_general"]
    raw = tree.to_dict()
    nodes = raw["nodes"]
    assert isinstance(nodes, dict)
    q_raw = nodes[qid]
    assert isinstance(q_raw, dict)
    internal = q_raw["internal"]
    assert isinstance(internal, dict)
    internal["team_notes"] = [
        {
            "id": "n1",
            "user_id": 7,
            "username": "pruefer_1",
            "message": "Bitte Vergabevermerk nachfordern.",
            "timestamp": "2026-10-01T09:00:00+00:00",
        }
    ]
    tree_with_notes = ChecklistTree.from_dict(raw)
    assert len(tree_with_notes.get_node(qid).internal.team_notes) == 1

    pkg = export_package(
        project=sample_project,
        tree=tree_with_notes,
        include_discussions=False,
        include_history=True,
    )

    # Ohne Kategorien bleibt das Kategorienobjekt leer
    assert pkg["categories"] == {}
    assert pkg["options"] == {"history": True, "discussions": False}
    versions = pkg["versions"]
    assert isinstance(versions, list)
    v0 = versions[0]
    assert isinstance(v0, dict)
    assert v0["history"] == []

    # Diskussionsbeiträge werden entfernt, der Quellbaum bleibt unverändert
    _, imported, _ = import_package(pkg)
    assert imported.get_node(qid).internal.team_notes == ()
    assert len(tree_with_notes.get_node(qid).internal.team_notes) == 1


def test_normalize_rejects_invalid_payloads() -> None:
    with pytest.raises(PackageFormatError, match="kein gültiges JSON-Objekt"):
        normalize_package_payload(["kein", "Objekt"])
    with pytest.raises(PackageFormatError, match="Unbekanntes Checklisten-Format"):
        normalize_package_payload({"titel": "Irgendwas"})
    with pytest.raises(PackageFormatError, match="neuer als unterstützt"):
        normalize_package_payload(
            {
                "format": PACKAGE_FORMAT,
                "format_version": FORMAT_VERSION + 1,
                "project": {"name": "Zukunft"},
                "versions": [],
            }
        )


def test_normalize_native_uses_fallback_name() -> None:
    normalized = normalize_package_payload(
        {
            "project": {"description": "Ohne Namen"},
            "versions": [{"tree_data": {"root_id": "r", "nodes": {}}}, "ungültig"],
        },
        fallback_name="Ersatzname",
    )
    project = normalized["project"]
    assert isinstance(project, dict)
    assert project["name"] == "Ersatzname"
    # Ungültige Versionseinträge werden verworfen
    versions = normalized["versions"]
    assert isinstance(versions, list)
    assert len(versions) == 1


def test_validate_package_reports_all_defects() -> None:
    assert validate_package("kein Paket") == ["Paket ist kein gültiges Wörterbuch-Objekt."]

    errors = validate_package(
        {
            "format": PACKAGE_FORMAT,
            "format_version": FORMAT_VERSION + 1,
            "project": {"name": "  "},
            "versions": [{"notes": "ohne Baum"}, "keine Zuordnung"],
        }
    )
    assert f"Format-Version {FORMAT_VERSION + 1} wird nicht unterstützt." in errors
    assert "Paket enthält keine gültigen Projektdaten mit Namen." in errors
    assert "Version 0 enthält kein 'tree_data'." in errors
    assert "Version 1 enthält kein 'tree_data'." in errors


def test_import_package_rejects_invalid_package() -> None:
    with pytest.raises(PackageFormatError, match="Paketvalidierung fehlgeschlagen") as exc:
        import_package({"format": PACKAGE_FORMAT, "project": {}, "versions": []})
    assert exc.value.code == "INVALID_PACKAGE"
