"""Diagrammsammlung: Ordner, Tags, Reihenfolge, Verweise, Übersichten, Freigaben, Speicher."""

from .approvals import approve, check_approval
from .checks import validate_collection
from .collection import DiagramCollection
from .excerpt import excerpt_from_document
from .model import (
    KEY_KINDS,
    Approval,
    DiagramEntry,
    DiagramExcerpt,
    DiagramReference,
    Folder,
    FolderNode,
    GroupOverview,
    Tag,
    sha256_xml,
)
from .queries import elements_by_key, overview, references, search, target_actual_pairs
from .serialization import COLLECTION_SCHEMA, collection_from_dict, collection_to_dict
from .storage import FileStorage, Storage

__all__ = [
    "COLLECTION_SCHEMA",
    "KEY_KINDS",
    "Approval",
    "DiagramCollection",
    "DiagramEntry",
    "DiagramExcerpt",
    "DiagramReference",
    "FileStorage",
    "Folder",
    "FolderNode",
    "GroupOverview",
    "Storage",
    "Tag",
    "approve",
    "check_approval",
    "collection_from_dict",
    "collection_to_dict",
    "elements_by_key",
    "excerpt_from_document",
    "overview",
    "references",
    "search",
    "sha256_xml",
    "target_actual_pairs",
    "validate_collection",
]
