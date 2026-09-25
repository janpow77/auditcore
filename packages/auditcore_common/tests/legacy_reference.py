"""Verbatim copies of the helpers merged into auditcore_common (differential oracle).

Copied from janpow77/auditcore@40ce8f710785b6ca8608512a2e335c14ec9d924f; each block
names its source file and symbol, ``docs/provenance`` in ``provenance.json`` lists the
git blobs. Only lines marked ``[adapted]`` differ: the resource package of the
profile loaders is a parameter (``RESOURCE_PACKAGE``), a method became a function
and the recommended loader calls its local copy. Package-specific error classes and
``profile_from_dict`` are replaced by the minimal stand-ins below.
"""
# ruff: noqa: E501, UP038, SIM103

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from html.parser import HTMLParser
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Any, TypeVar
from xml.etree.ElementTree import Element

K = TypeVar("K")
JSON = Any
_BLOCK = 128
PROFILE_VERSION = "2026.09.1"
RESOURCE_PACKAGE = "legacy_profiles"


class ProfileError(ValueError):
    """Stand-in for the ProfileError of each package."""


class ParserError(ValueError):
    """legal_sources.ParserError."""


class FormatError(ValueError):
    """registry_sources.FormatError."""


class DependencyError(ImportError):
    """Stand-in for the DependencyError of each package."""


class ExportDependencyError(ImportError):
    """dataprotection.ExportDependencyError."""


class OptionalDependencyError(ImportError):
    """funding_sources.OptionalDependencyError."""


class KoordinatenFehler(ValueError):
    """geo.KoordinatenFehler."""


class IndicatorInputError(ValueError):
    """market_indicators.IndicatorInputError."""


@dataclass(frozen=True)
class LegacyProfile:
    """Stand-in for the parsed profile dataclasses (identity only)."""

    id: object
    version: object
    raw: object


def profile_from_dict(data: Any) -> LegacyProfile:
    """Stand-in: parsing that keeps id and version like the originals."""
    return LegacyProfile(data["id"], data["version"], data)


def fingerprint(data: object) -> str:
    """funding_sources.profiles.fingerprint (identical to entity_fingerprint)."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_sha256(data: Mapping[str, object]) -> str:
    """Used by dataprotection_plain's module (not called here)."""
    return fingerprint(data)


RuleProfile = Profile = SourceProfile = IndicatorProfile = PrecheckProfile = RegistryProfile = LegacyProfile


# packages/auditcore_dataprotection/src/auditcore_dataprotection/report_data.py :: plain
def dataprotection_plain(value: object) -> Any:
    """Convert records, enums, mappings and datetimes to JSON-compatible values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return dataprotection_plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): dataprotection_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [dataprotection_plain(v) for v in value]
        return sorted(items) if isinstance(value, (set, frozenset)) else items
    return value


# packages/auditcore_risk/src/auditcore_risk/results.py :: plain
def risk_plain(value: object) -> object:
    """JSON-compatible copy: mappings → dicts, sequences → lists, dates → ISO text."""
    if isinstance(value, Mapping):
        return {str(k): risk_plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [risk_plain(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    return value


# packages/auditcore_funding_sources/src/auditcore_funding_sources/_jsonsafe.py :: json_safe
def funding_json_safe(value: object) -> object:
    """JSON-safe copy (Decimal/date as text, NaN as ``None``).

    Values of other types are passed on unchanged, as in the source.
    """
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, Mapping):
        return funding_json_safe_mapping(value)  # [adapted]
    if isinstance(value, (list, tuple)):
        return [funding_json_safe(v) for v in value]
    return value


# packages/auditcore_funding_sources/src/auditcore_funding_sources/_jsonsafe.py :: json_safe_mapping
def funding_json_safe_mapping(value: Mapping[K, object]) -> dict[str, object]:
    """:func:`json_safe` of a mapping; keys become text."""
    return {str(k): funding_json_safe(v) for k, v in value.items()}  # [adapted]


# packages/auditcore_legal_sources/src/auditcore_legal_sources/_adapter_support.py :: _json
def legal_json(response_body: bytes, what: str) -> object:
    try:
        return json.loads(response_body)
    except ValueError as exc:
        raise ParserError(f"{what}: Antwort ist kein JSON.") from exc


# packages/auditcore_registry_sources/src/auditcore_registry_sources/chambers.py :: _json
def registry_json(data: bytes, what: str) -> Any:
    try:
        return json.loads(data)
    except ValueError as exc:
        raise FormatError(f"{what}: keine gültige JSON-Antwort ({exc}).") from exc


# packages/auditcore_dataprotection/src/auditcore_dataprotection/hashing.py :: canonical_sha256
def dataprotection_canonical_sha256(data: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON form (sorted keys, no whitespace, UTF-8)."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# packages/auditcore_entity_matching/src/auditcore_entity_matching/profiles.py :: fingerprint
def entity_fingerprint(data: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON profile document."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# packages/auditcore_harvest/src/auditcore_harvest/model.py :: canonical_hash
def harvest_canonical_hash(value: JSON) -> str:
    """SHA-256 over canonical JSON; the stable content hash of a record."""
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# packages/auditcore_documents/src/auditcore_documents/profiles.py :: fingerprint
def documents_profile_fingerprint(data: Mapping[str, object]) -> str:
    # [adapted] method body after ``asdict(self)`` and the legacy-default pruning
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# packages/auditcore_documents/src/auditcore_documents/pipeline/hashing.py :: hash_json
def documents_hash_json(obj: dict[str, Any] | list[Any]) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# packages/auditcore_documents/src/auditcore_documents/pipeline/hashing.py :: hash_string
def documents_hash_string(text: str, encoding: str = "utf-8") -> str:
    return hashlib.sha256(text.encode(encoding)).hexdigest()


# packages/auditcore_documents/src/auditcore_documents/compare.py :: sha256_file
def documents_sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


# packages/auditcore_documents/src/auditcore_documents/pipeline/hashing.py :: hash_file
def documents_hash_file(file_path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


# packages/auditcore_invoicesynth/src/auditcore_invoicesynth/fonts.py :: sha256_file
def invoicesynth_sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


# packages/auditcore_invoicesynth/src/auditcore_invoicesynth/dataset.py :: _sha256
def invoicesynth_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# packages/auditcore_dataprotection/src/auditcore_dataprotection/profile_loader.py :: available_profiles
def dataprotection_available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs, sorted; no profile is a hidden default."""
    found = []
    for entry in resources.files(RESOURCE_PACKAGE).iterdir():  # [adapted]
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found.append((str(data["id"]), str(data["version"])))
    return tuple(sorted(found))


# packages/auditcore_dataprotection/src/auditcore_dataprotection/profile_loader.py :: load_profile
def dataprotection_load_profile(profile_id: str, version: str) -> RuleProfile:
    """Load an explicitly named packaged profile version.

    Raises:
        ProfileError: the id/version pair is not packaged.
    """
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    entry = resources.files(RESOURCE_PACKAGE).joinpath(name)  # [adapted]
    if "/" in name or "\\" in name or not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    data = json.loads(entry.read_text(encoding="utf-8"))
    profile = profile_from_dict(data)
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


# packages/auditcore_entity_matching/src/auditcore_entity_matching/profiles.py :: load_profile
def entity_load_profile(profile_id: str, version: str) -> Profile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    entry = resources.files(RESOURCE_PACKAGE).joinpath(name)  # [adapted]
    if "/" in name or "\\" in name or not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


# packages/auditcore_entity_matching/src/auditcore_entity_matching/profiles.py :: recommended_profile
def entity_recommended_profile(purpose: str) -> Profile:
    """The profile marked as recommended for ``purpose`` (user decisions of 23.09.2026).

    Purposes: ``entity_normalization``, ``sanctions_screening``,
    ``pep_screening``, ``payee``. Exactly one packaged profile carries each
    purpose; the recommendation never changes a result of a named profile.
    """
    found = []
    for entry in resources.files(RESOURCE_PACKAGE).iterdir():  # [adapted]
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            if purpose in data.get("recommended_for", []):
                found.append((str(data["id"]), str(data["version"])))
    if len(found) != 1:
        raise ProfileError(f"Für '{purpose}' ist kein eindeutiges empfohlenes Profil hinterlegt.")
    return entity_load_profile(*found[0])  # [adapted]


# packages/auditcore_funding_sources/src/auditcore_funding_sources/profiles.py :: load_profile
def funding_load_profile(profile_id: str, version: str = PROFILE_VERSION) -> dict[str, Any]:
    """Load an explicitly named profile; adds ``fingerprint``.

    Raises:
        ProfileError: unknown id/version or mismatching content.
    """
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name or name.startswith("."):
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files(RESOURCE_PACKAGE).joinpath(name)  # [adapted]
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    data = json.loads(entry.read_text(encoding="utf-8"))
    if (data.get("id"), data.get("version")) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return {**data, "fingerprint": fingerprint(data)}


# packages/auditcore_legal_sources/src/auditcore_legal_sources/profile.py :: load_profile
def legal_load_profile(profile_id: str, version: str) -> SourceProfile:
    """Load an explicitly named packaged profile version."""
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name or name.startswith("."):
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files(RESOURCE_PACKAGE).joinpath(name)  # [adapted]
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


# packages/auditcore_market_indicators/src/auditcore_market_indicators/profiles.py :: load_profile
def market_load_profile(profile_id: str, version: str) -> IndicatorProfile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name:
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files(RESOURCE_PACKAGE).joinpath(name)  # [adapted]
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


# packages/auditcore_procurement/src/auditcore_procurement/precheck_profile.py :: load_profile
def procurement_load_profile(profile_id: str, version: str) -> PrecheckProfile:
    """Load an explicitly named packaged profile version."""
    name = f"{profile_id}-{version}.json"
    entry = resources.files(RESOURCE_PACKAGE).joinpath(name)  # [adapted]
    if "/" in name or "\\" in name or not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


# packages/auditcore_registry_sources/src/auditcore_registry_sources/profiles.py :: load_profile
def registry_load_profile(profile_id: str, version: str) -> RegistryProfile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name:
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files(RESOURCE_PACKAGE).joinpath(name)  # [adapted]
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


# packages/auditcore_risk/src/auditcore_risk/profiles.py :: _packaged
def risk_packaged() -> dict[tuple[str, str], Traversable]:
    found = {}
    for entry in resources.files(RESOURCE_PACKAGE).iterdir():  # [adapted]
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found[(str(data["id"]), str(data["version"]))] = entry
    return found


# packages/auditcore_documents/src/auditcore_documents/pipeline/audit.py :: _freeze
def documents_freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({k: documents_freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(documents_freeze(v) for v in value)
    return value


# packages/auditcore_documents/src/auditcore_documents/pipeline/audit.py :: thaw
def documents_thaw(value: object) -> object:
    if isinstance(value, MappingProxyType):
        return {k: documents_thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [documents_thaw(v) for v in value]
    return value


# packages/auditcore_registry_sources/src/auditcore_registry_sources/_xml_support.py :: _fromstring
def registry_fromstring(data: bytes) -> Element:
    try:
        from defusedxml.ElementTree import fromstring
    except ImportError as exc:  # pragma: no cover - exercised in the installed smoke test
        raise DependencyError(
            "Für XML-Sanktionslisten ist 'auditcore_registry_sources[xml]' zu installieren."
        ) from exc
    root: Element = fromstring(data)
    return root


# packages/auditcore_legal_sources/src/auditcore_legal_sources/feeds.py :: _Links
class LegalLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Start collecting the text of an anchor with ``href``."""
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href, self._text = href, []

    def handle_data(self, data: str) -> None:
        """Collect anchor text."""
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Finish the current anchor."""
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


# packages/auditcore_statistics/src/auditcore_statistics/numeric.py :: numpy_pairwise_sum
def statistics_pairwise_sum(values: Sequence[float]) -> float:
    """Sum in NumPy's pairwise order (blocks of 128, eight accumulators)."""
    count = len(values)
    if count < 8:
        result = 0.0
        for value in values:
            result += value
        return result
    if count <= _BLOCK:
        acc = [float(v) for v in values[:8]]
        index = 8
        limit = count - (count % 8)
        while index < limit:
            for lane in range(8):
                acc[lane] += values[index + lane]
            index += 8
        result = ((acc[0] + acc[1]) + (acc[2] + acc[3])) + ((acc[4] + acc[5]) + (acc[6] + acc[7]))
        while index < count:
            result += values[index]
            index += 1
        return result
    half = count // 2
    half -= half % 8
    return statistics_pairwise_sum(values[:half]) + statistics_pairwise_sum(values[half:])


# packages/auditcore_sampling/src/auditcore_sampling/_numeric.py :: pairwise_sum
def sampling_pairwise_sum(values: Sequence[float]) -> float:
    """NumPy ``add.reduce`` order for contiguous float64 data."""
    count = len(values)
    if count < 8:
        result = 0.0
        for value in values:
            result += value
        return result
    if count <= _BLOCK:
        acc = [float(v) for v in values[:8]]
        index = 8
        limit = count - (count % 8)
        while index < limit:
            for lane in range(8):
                acc[lane] += values[index + lane]
            index += 8
        result = ((acc[0] + acc[1]) + (acc[2] + acc[3])) + ((acc[4] + acc[5]) + (acc[6] + acc[7]))
        while index < count:
            result += values[index]
            index += 1
        return result
    half = count // 2
    half -= half % 8
    return sampling_pairwise_sum(values[:half]) + sampling_pairwise_sum(values[half:])


# packages/auditcore_market_indicators/src/auditcore_market_indicators/_numeric.py :: numpy_pairwise_sum
def market_pairwise_sum(values: Sequence[float]) -> float:
    """Sum in NumPy's pairwise order (blocks of 128, eight accumulators)."""
    count = len(values)
    if count < 8:
        result = 0.0
        for value in values:
            result += value
        return result
    if count <= _BLOCK:
        acc = [float(v) for v in values[:8]]
        index = 8
        limit = count - (count % 8)
        while index < limit:
            for lane in range(8):
                acc[lane] += values[index + lane]
            index += 8
        result = ((acc[0] + acc[1]) + (acc[2] + acc[3])) + ((acc[4] + acc[5]) + (acc[6] + acc[7]))
        while index < count:
            result += values[index]
            index += 1
        return result
    half = count // 2
    half -= half % 8
    return market_pairwise_sum(values[:half]) + market_pairwise_sum(values[half:])


# packages/auditcore_statistics/src/auditcore_statistics/numeric.py :: numpy_round
def statistics_numpy_round(value: float, decimals: int) -> float:
    """``numpy.round`` for float64: scale, round half to even, unscale."""
    factor = 10.0**decimals
    return round(value * factor) / factor


# packages/auditcore_sampling/src/auditcore_sampling/_numeric.py :: numpy_round
def sampling_numpy_round(value: float, decimals: int) -> float:
    """``numpy.round`` for float64."""
    factor = 10.0**decimals
    return round(value * factor) / factor


# packages/auditcore_geo/src/auditcore_geo/koordinaten.py :: _endlich
def geo_endlich(wert: float, name: str) -> float:
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise KoordinatenFehler(f"{name} ist keine Zahl: {wert!r}")
    zahl = float(wert)
    if not math.isfinite(zahl):
        raise KoordinatenFehler(f"{name} ist nicht endlich: {wert!r}")
    return zahl


# packages/auditcore_market_indicators/src/auditcore_market_indicators/indicators.py :: _finite
def market_finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IndicatorInputError(f"{name} muss eine Zahl sein.")
    number = float(value)
    if not math.isfinite(number):
        raise IndicatorInputError(f"{name} muss endlich sein.")
    return number


# packages/auditcore_documents/src/auditcore_documents/pipeline/stages/donut_values.py :: rate
def documents_rate(raw: str) -> Decimal | None:
    match = re.fullmatch(r"(\d{1,2})(?:[.,](\d))?\s*%?", raw.strip())
    if not match:
        return None
    value = Decimal(match[1] + ("." + match[2] if match[2] else ""))
    return value.quantize(Decimal(1)) if value == value.to_integral() else value


# packages/auditcore_invoicesynth/src/auditcore_invoicesynth/formats.py :: parse_rate
def invoicesynth_parse_rate(text: str) -> Decimal | None:
    """``19 %``/``19%``/``19,0 %`` → ``Decimal('19')``."""
    match = re.fullmatch(r"(\d{1,2})(?:[.,](\d))?\s*%?", text.strip())
    if not match:
        return None
    value = Decimal(match[1] + ("." + match[2] if match[2] else ""))
    return value.quantize(Decimal(1)) if value == value.to_integral() else value


# packages/auditcore_documents/src/auditcore_documents/pipeline/stages/donut_values.py :: compact
def documents_compact(raw: str) -> str:
    return "".join(raw.split()).upper()


# packages/auditcore_invoicesynth/src/auditcore_invoicesynth/formats.py :: normalize_identifier
def invoicesynth_normalize_identifier(text: str) -> str:
    """IBAN/USt-IdNr./BIC: Großbuchstaben ohne Leerzeichen."""
    return "".join(text.split()).upper()


# packages/auditcore_harvest/src/auditcore_harvest/model.py :: iso
def harvest_iso(moment: datetime) -> str:
    """Timezone-aware ISO timestamp; naive datetimes are rejected."""
    if moment.tzinfo is None:
        raise ValueError("Zeitangaben müssen eine Zeitzone tragen.")
    return moment.isoformat()


# packages/auditcore_property_sources/src/auditcore_property_sources/zvg_lifecycle.py :: _aware
def property_aware(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("Zeitangaben müssen eine Zeitzone tragen.")
    return now


# packages/auditcore_dataprotection/src/auditcore_dataprotection/prefill.py :: _number
def dataprotection_number(value: int) -> str:
    return f"{value:,}".replace(",", ".")


# packages/auditcore_registry_sources/src/auditcore_registry_sources/_legacy_osint.py :: _count
def registry_count(n: int) -> str:
    return f"{n:,}".replace(",", ".")


# packages/auditcore_dataprotection/src/auditcore_dataprotection/excel.py :: _openpyxl
def dataprotection_openpyxl() -> Any:
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise ExportDependencyError(
            "Excel-Ausgabe benötigt openpyxl: pip install 'auditcore_dataprotection[excel]'"
        ) from exc
    return openpyxl


# packages/auditcore_funding_sources/src/auditcore_funding_sources/tables.py :: _openpyxl
def funding_openpyxl() -> Any:
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise OptionalDependencyError(
            "XLSX-Dateien benötigen das Extra auditcore_funding_sources[xlsx] (openpyxl)."
        ) from exc
    return openpyxl


# packages/auditcore_entity_matching/src/auditcore_entity_matching/matching.py :: _rapidfuzz
def entity_rapidfuzz() -> tuple[ModuleType, ModuleType]:
    """``rapidfuzz.fuzz`` and ``rapidfuzz.process``, imported only when a score is needed."""
    try:
        from rapidfuzz import fuzz, process
    except ImportError as exc:  # pragma: no cover - exercised in the installed smoke test
        raise DependencyError(
            "Für unscharfe Vergleiche ist 'auditcore_entity_matching[fuzzy]' zu installieren."
        ) from exc
    return fuzz, process

# packages/auditcore_price_sources/src/auditcore_price_sources/snapshots.py :: canonical_json_bytes
def price_sources_canonical_json_bytes(body: bytes) -> bytes:
    """``json.dumps(payload, sort_keys=True)`` of a JSON body (regulierung's package bytes).

    Raises ``ValueError`` if the body is not JSON.
    """
    return json.dumps(json.loads(body), sort_keys=True).encode()

