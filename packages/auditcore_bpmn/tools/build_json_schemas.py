"""Erzeugt die JSON-Schemata des Pakets aus den Datenklassen (``src/auditcore_bpmn/schemas``).

    python tools/build_json_schemas.py src/auditcore_bpmn/schemas

``tests/test_schemas.py`` prüft, dass die Dateien aktuell sind.
"""

from __future__ import annotations

import argparse
import json
import sys
import typing
from dataclasses import fields
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auditcore_bpmn import extensions  # noqa: E402
from auditcore_bpmn.collection.serialization import COLLECTION_SCHEMA  # noqa: E402
from auditcore_bpmn.profiles.loader import PROFILE_SCHEMA  # noqa: E402
from auditcore_bpmn.validation.issues import REPORT_SCHEMA  # noqa: E402
from auditcore_bpmn.validation.messages import SEVERITIES  # noqa: E402

BASE = "https://flowaudit.de/schemas/auditcore-bpmn/"
TYPES = [
    extensions.LegalBasis,
    extensions.Marker,
    extensions.AuditReference,
    extensions.Actor,
    extensions.Control,
    extensions.Risk,
    extensions.Evidence,
    extensions.AuditStep,
    extensions.AuditFinding,
    extensions.Source,
    extensions.CrossReference,
    extensions.Deadline,
    extensions.EsiRequirement,
    extensions.EsiRequirements,
    extensions.DiagramInfo,
]


def _property(cls: type, name: str, metadata: typing.Mapping[str, Any]) -> dict[str, Any]:
    kind = metadata.get("kind")
    if kind == "elements":
        return {"type": "array", "items": {"$ref": f"#/$defs/{metadata['item_type'].__name__}"}}
    if kind in ("texts", "tokens"):
        return {"type": "array", "items": {"type": "string"}}
    if metadata.get("bool"):
        return {"type": "boolean"}
    return {"type": "string"}


def dataclass_schema(cls: type) -> dict[str, Any]:
    properties = {
        item.name: {
            **_property(cls, item.name, item.metadata),
            "description": f"XML: {item.metadata.get('xml') or '(Textinhalt)'}",
        }
        for item in fields(cls)
        if item.metadata.get("kind") != "internal"
    }
    if cls is extensions.EsiRequirements:
        properties["origin"] = {"type": "string", "enum": ["flowaudit-1.1", "legacy-attribute"]}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "description": (cls.__doc__ or "").strip().splitlines()[0],
    }


def definitions() -> dict[str, Any]:
    return {cls.__name__: dataclass_schema(cls) for cls in TYPES}


def collection_schema() -> dict[str, Any]:
    pairs = {"type": "array", "items": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 2}}
    identifier = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + "diagram-collection-1.schema.json",
        "title": "Diagrammsammlung",
        "type": "object",
        "required": ["schema", "id", "name", "folders", "tags", "diagrams"],
        "additionalProperties": False,
        "properties": {
            "schema": {"const": COLLECTION_SCHEMA},
            "id": {"type": "string"},
            "name": {"type": "string"},
            "folders": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "name"],
                    "additionalProperties": False,
                    "properties": {
                        "id": identifier,
                        "name": {"type": "string"},
                        "parent_id": identifier,
                        "position": {"type": "integer"},
                        "description": {"type": "string"},
                    },
                },
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "name"],
                    "additionalProperties": False,
                    "properties": {"id": identifier, "name": {"type": "string"}, "color": {"type": "string"}},
                },
            },
            "diagrams": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "name", "tags", "position", "excerpt", "approvals"],
                    "additionalProperties": False,
                    "properties": {
                        "id": identifier,
                        "name": {"type": "string"},
                        "folder_id": {"type": ["string", "null"]},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "position": {"type": "integer"},
                        "info": {"$ref": "#/$defs/DiagramInfo"},
                        "excerpt": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "process_ids": {"type": "array", "items": {"type": "string"}},
                                "calls": pairs,
                                "link_throws": pairs,
                                "link_catches": pairs,
                                "activities": {"type": "integer"},
                                "activities_with_legal_basis": {"type": "integer"},
                                "keys": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "type": "object",
                                        "additionalProperties": {"type": "array", "items": {"type": "string"}},
                                    },
                                },
                            },
                        },
                        "approvals": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["version", "sha256"],
                                "additionalProperties": False,
                                "properties": {
                                    "version": {"type": "string"},
                                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                    "cutoff_date": {"type": "string"},
                                    "approved_on": {"type": "string"},
                                    "approved_by": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
        "$defs": definitions(),
    }


def report_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + "validation-report-1.schema.json",
        "title": "Prüfbericht der Regeln",
        "type": "object",
        "required": ["schema", "ruleset_version", "profile", "valid", "counts", "issues"],
        "additionalProperties": False,
        "properties": {
            "schema": {"const": REPORT_SCHEMA},
            "ruleset_version": {"type": "string"},
            "profile": {"type": "string"},
            "profile_origin": {"type": "string"},
            "reference_date": {"type": ["string", "null"]},
            "valid": {"type": "boolean"},
            "counts": {"type": "object", "additionalProperties": {"type": "integer"}},
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["rule_id", "severity", "message", "params"],
                    "additionalProperties": False,
                    "properties": {
                        "rule_id": {"type": "string", "pattern": "^BPMN-[A-Z]+[0-9A-Z-]*$"},
                        "severity": {"enum": list(SEVERITIES)},
                        "severity_label": {"type": "string"},
                        "message": {"type": "string"},
                        "params": {"type": "object"},
                        "element_id": {"type": "string"},
                        "diagram_id": {"type": "string"},
                    },
                },
            },
        },
    }


def profile_schema() -> dict[str, Any]:
    labels = {"type": "object", "additionalProperties": {"type": "string"}, "required": ["de"]}
    selection = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "markers": {"type": "array", "items": {"type": "string"}},
            "audit_types": {"type": "array", "items": {"type": "string"}},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + "profile-1.schema.json",
        "title": "Förderperioden-Profil",
        "type": "object",
        "required": ["schema", "id", "version", "title", "roles", "funds", "key_requirements"],
        "properties": {
            "schema": {"const": PROFILE_SCHEMA},
            "id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
            "version": {"type": "string", "pattern": "^\\d{4}\\.\\d{2}\\.\\d+$"},
            "title": labels,
            "programming_period": {"type": "string", "pattern": "^\\d{4}-\\d{4}$"},
            "roles": {"type": "array", "items": {"type": "string"}},
            "custom_roles": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "required": ["labels"],
                    "properties": {
                        "labels": labels,
                        "from_year": {"type": "integer"},
                        "until_year": {"type": "integer"},
                    },
                },
            },
            "role_aliases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["pattern", "role"],
                    "properties": {"pattern": {"type": "string"}, "role": {"type": "string"}},
                },
            },
            "funds": {"type": "array", "items": {"type": "string"}},
            "key_requirements": {
                "type": "object",
                "required": ["entries"],
                "properties": {
                    "source": {"type": "object"},
                    "assessment_criteria_note": labels,
                    "entries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["number", "title"],
                            "properties": {
                                "number": {"type": "integer", "minimum": 1},
                                "title": labels,
                                "bodies": labels,
                                "scope": labels,
                                "footnote": labels,
                                "assessment_criteria": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["code"],
                                        "properties": {"code": {"type": "string"}, "title": labels},
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "legal_bases": {
                "type": "object",
                "properties": {
                    "source": {"type": "object"},
                    "entries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["act", "short_title"],
                            "properties": {
                                "act": {"type": "string"},
                                "article": {"type": "string"},
                                "annex": {"type": "string"},
                                "short_title": labels,
                                "celex": {"type": "string"},
                                "eli": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "segregation_rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "kind", "title"],
                    "properties": {
                        "id": {"type": "string"},
                        "kind": {"enum": ["separate_bodies", "excluded_role", "four_eyes"]},
                        "severity": {"enum": list(SEVERITIES)},
                        "title": labels,
                        "a": selection,
                        "b": selection,
                        "selection": selection,
                        "roles": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "templates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "title", "file"],
                    "properties": {
                        "id": {"type": "string"},
                        "title": labels,
                        "file": {"type": "string"},
                        "origin": {"type": "string"},
                    },
                },
            },
        },
    }


SCHEMAS = {
    "diagram-collection-1.schema.json": collection_schema,
    "validation-report-1.schema.json": report_schema,
    "profile-1.schema.json": profile_schema,
}


def render(name: str) -> str:
    return json.dumps(SCHEMAS[name](), ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for name in SCHEMAS:
        (args.output / name).write_text(render(name), encoding="utf-8")
        print(args.output / name)


if __name__ == "__main__":
    main()
