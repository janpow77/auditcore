"""Artifact-grounded SBOM generation and schema validation."""

from __future__ import annotations

import email.parser
import json
import zipfile
from pathlib import Path
from typing import Any

from auditcore.tools.common import digest, write_json


def validate_schema(document: dict[str, Any]) -> dict[str, str]:
    """Validate CycloneDX 1.6 against the validator's bundled official schema."""
    try:
        from cyclonedx.schema import SchemaVersion
        from cyclonedx.validation.json import JsonStrictValidator
    except ImportError:
        return {
            "status": "NOT_EXECUTED",
            "reason": "Install auditcore[quality] for JSON validation",
        }
    validator = JsonStrictValidator(SchemaVersion.V1_6)
    errors = validator.validate_str(json.dumps(document))
    return {
        "status": "PASS" if errors is None else "FAIL",
        "schema": "CycloneDX 1.6",
        "validator": "cyclonedx-python-lib",
    }


def wheel_sbom(wheel: Path, output: Path) -> dict[str, Any]:
    """Create a BOM from wheel metadata and actual packaged file bytes."""
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_path = next(n for n in names if n.endswith(".dist-info/METADATA"))
        metadata = email.parser.Parser().parsestr(archive.read(metadata_path).decode())
        components = [
            {
                "type": "file",
                "name": name,
                "hashes": [{"alg": "SHA-256", "content": digest(archive.read(name))}],
            }
            for name in sorted(names)
            if not name.endswith("/")
        ]
    document = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "component": {
                "type": "library",
                "name": metadata["Name"],
                "version": metadata["Version"],
                "hashes": [{"alg": "SHA-256", "content": digest(wheel.read_bytes())}],
            }
        },
        "components": components,
        "properties": [
            {
                "name": "auditcore:declared-requirements",
                "value": json.dumps(metadata.get_all("Requires-Dist", [])),
            },
            {
                "name": "auditcore:scope",
                "value": "Wheel payload; optional extras are declared, not bundled",
            },
        ],
    }
    validation = validate_schema(document)
    write_json(output, document)
    return {
        "status": validation["status"],
        "artifact_sha256": digest(wheel.read_bytes()),
        "sbom_sha256": digest(output.read_bytes()),
        "validation": validation,
        "artifact": wheel.name,
        "sbom": output.name,
    }
