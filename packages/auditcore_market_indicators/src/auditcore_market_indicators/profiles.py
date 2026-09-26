"""Versioned, source-bound indicator profiles.

A profile fixes every choice in which the characterized krypto functions
differ: start value and gap handling of the EMA, smoothing (Wilder, EMA or
SMA) and flat-market value of the RSI, smoothing of the ATR, gap handling of
RSI/ADX, the summation order of start values and, optionally, the
recommended minimum lookback (``warmup.min_lookback``). Indicators without variants
(returns, SMA, z-score …) take no profile.

Nothing here picks a variant: every packaged profile reproduces one source
module, and a profile section that is absent means the source does not define
that indicator. ``profile_from_dict`` accepts own profiles with the same
schema; values are never defaulted silently.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any, Literal, cast

from .errors import ProfileError

SCHEMA = "auditcore_market_indicators.profile/1"

Summation = Literal["neumaier", "numpy_pairwise"]
EmaSeed = Literal["sma", "first_value"]
EmaGaps = Literal["skip", "hold", "error"]
RsiSmoothing = Literal["wilder", "ema", "sma"]
MoveGaps = Literal["zero_move", "error"]
AtrSmoothing = Literal["sma", "wilder", "ema"]

_SUMMATION = ("neumaier", "numpy_pairwise")
_EMA_SEED = ("sma", "first_value")
_EMA_GAPS = ("skip", "hold", "error")
_RSI_SMOOTHING = ("wilder", "ema", "sma")
_MOVE_GAPS = ("zero_move", "error")
_ATR_SMOOTHING = ("sma", "wilder", "ema")


@dataclass(frozen=True)
class EmaRule:
    """EMA with α = 2/(n+1); ``seed`` and ``gaps`` as characterized."""

    seed: EmaSeed
    gaps: EmaGaps


@dataclass(frozen=True)
class RsiRule:
    """RSI smoothing, value for a window without any movement, gap handling."""

    smoothing: RsiSmoothing
    flat_value: float
    gaps: MoveGaps


@dataclass(frozen=True)
class AtrRule:
    """Smoothing of the true range."""

    smoothing: AtrSmoothing


@dataclass(frozen=True)
class AdxRule:
    """Gap handling of the directional movement (Wilder smoothing is fixed)."""

    gaps: MoveGaps


@dataclass(frozen=True)
class IndicatorProfile:
    """Immutable profile with identity, source and fingerprint."""

    id: str
    version: str
    status: str
    legal_status: str
    source: Mapping[str, Any]
    fingerprint: str
    summation: Summation
    ema: EmaRule | None
    rsi: RsiRule | None
    atr: AtrRule | None
    adx: AdxRule | None
    macd: bool
    min_lookback: int | None = None

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded with every result that used this profile."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}

    def require_ema(self) -> EmaRule:
        """EMA-Regel oder ProfileError, wenn das Profil keine EMA festlegt."""
        if self.ema is None:
            raise ProfileError(f"Profil {self.id} legt keine EMA fest.")
        return self.ema

    def require_rsi(self) -> RsiRule:
        """RSI-Regel oder ProfileError."""
        if self.rsi is None:
            raise ProfileError(f"Profil {self.id} legt keinen RSI fest.")
        return self.rsi

    def require_atr(self) -> AtrRule:
        """ATR-Regel oder ProfileError."""
        if self.atr is None:
            raise ProfileError(f"Profil {self.id} legt keine ATR fest.")
        return self.atr

    def require_adx(self) -> AdxRule:
        """ADX-Regel oder ProfileError."""
        if self.adx is None:
            raise ProfileError(f"Profil {self.id} legt keinen ADX fest.")
        return self.adx

    def require_macd(self) -> EmaRule:
        """EMA-Regel für den MACD oder ProfileError, wenn kein MACD festgelegt ist."""
        if not self.macd:
            raise ProfileError(f"Profil {self.id} legt keinen MACD fest.")
        return self.require_ema()


def fingerprint(data: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON profile document."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _choice(value: object, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise ProfileError(f"{label}: {value!r} ist keine zulässige Variante {allowed}.")
    return str(value)


def _section(data: Mapping[str, object], key: str) -> Mapping[str, object] | None:
    if key not in data:
        raise ProfileError(f"Abschnitt {key!r} fehlt (null angeben, wenn nicht festgelegt).")
    value = data[key]
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ProfileError(f"Abschnitt {key!r} muss ein Objekt oder null sein.")
    return value


def _check_header(data: Mapping[str, object]) -> None:
    if data["schema"] != SCHEMA:
        raise ProfileError("Unbekanntes Profilschema.")
    for key in ("id", "version", "status", "legal_status"):
        if not isinstance(data[key], str) or not data[key]:
            raise ProfileError(f"{key} muss ein nicht leerer Text sein.")
    if not isinstance(data["source"], Mapping):
        raise ProfileError("source muss ein Objekt sein.")


def _ema_rule(section: Mapping[str, object] | None) -> EmaRule | None:
    if section is None:
        return None
    return EmaRule(
        seed=cast(EmaSeed, _choice(section["seed"], _EMA_SEED, "ema.seed")),
        gaps=cast(EmaGaps, _choice(section["gaps"], _EMA_GAPS, "ema.gaps")),
    )


def _rsi_rule(section: Mapping[str, object] | None) -> RsiRule | None:
    if section is None:
        return None
    flat = section["flat_value"]
    if isinstance(flat, bool) or not isinstance(flat, (int, float)):
        raise ProfileError("rsi.flat_value muss eine Zahl sein.")
    if not 0.0 <= float(flat) <= 100.0:
        raise ProfileError("rsi.flat_value muss zwischen 0 und 100 liegen.")
    return RsiRule(
        smoothing=cast(
            RsiSmoothing, _choice(section["smoothing"], _RSI_SMOOTHING, "rsi.smoothing")
        ),
        flat_value=float(flat),
        gaps=cast(MoveGaps, _choice(section["gaps"], _MOVE_GAPS, "rsi.gaps")),
    )


def _atr_rule(section: Mapping[str, object] | None) -> AtrRule | None:
    if section is None:
        return None
    return AtrRule(
        smoothing=cast(AtrSmoothing, _choice(section["smoothing"], _ATR_SMOOTHING, "atr.smoothing"))
    )


def _adx_rule(section: Mapping[str, object] | None) -> AdxRule | None:
    if section is None:
        return None
    return AdxRule(gaps=cast(MoveGaps, _choice(section["gaps"], _MOVE_GAPS, "adx.gaps")))


def _min_lookback(data: Mapping[str, object]) -> int | None:
    """Optional ``warmup.min_lookback``; characterized legacy profiles do not define it."""
    if "warmup" not in data:
        return None
    warmup = data["warmup"]
    if not isinstance(warmup, Mapping):
        raise ProfileError("warmup muss ein Objekt sein.")
    value = warmup["min_lookback"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ProfileError("warmup.min_lookback muss eine positive ganze Zahl sein.")
    return value


def _profile(data: Mapping[str, object]) -> IndicatorProfile:
    _check_header(data)
    ema = _ema_rule(_section(data, "ema"))
    rsi = _rsi_rule(_section(data, "rsi"))
    atr = _atr_rule(_section(data, "atr"))
    adx = _adx_rule(_section(data, "adx"))
    macd_section = _section(data, "macd")
    if macd_section is not None and ema is None:
        raise ProfileError("macd setzt einen ema-Abschnitt voraus.")
    if ema is None and rsi is None and atr is None and adx is None:
        raise ProfileError("Profil legt keinen Indikator fest.")
    min_lookback = _min_lookback(data)
    return IndicatorProfile(
        # _check_header guarantees non-empty texts and a source mapping.
        id=cast(str, data["id"]),
        version=cast(str, data["version"]),
        status=cast(str, data["status"]),
        legal_status=cast(str, data["legal_status"]),
        source=MappingProxyType(dict(cast(Mapping[str, object], data["source"]))),
        fingerprint=fingerprint(data),
        summation=cast(Summation, _choice(data["summation"], _SUMMATION, "summation")),
        ema=ema,
        rsi=rsi,
        atr=atr,
        adx=adx,
        macd=macd_section is not None,
        min_lookback=min_lookback,
    )


def profile_from_dict(data: Mapping[str, Any]) -> IndicatorProfile:
    """Validate a profile document; nothing is defaulted silently."""
    try:
        return _profile(data)
    except (KeyError, TypeError) as exc:
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


#: Nutzerentscheidung vom 23.09.2026 („6 ja wilder, rsi“; „5. 250 kerzen“):
#: empfohlenes Profil für den krypto-Consumer. Die charakterisierten Profile
#: bleiben für den bitgenauen Legacy-Replay unverändert.
RECOMMENDED_PROFILE = ("krypto.entschieden", "2026.09.1")


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; no profile is an implicit default."""
    found = []
    for entry in resources.files("auditcore_market_indicators.profile_data").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found.append((str(data["id"]), str(data["version"])))
    return tuple(sorted(found))


def load_profile(profile_id: str, version: str) -> IndicatorProfile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name:
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files("auditcore_market_indicators.profile_data").joinpath(name)
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


def profile_document(profile: IndicatorProfile) -> dict[str, Any]:
    """Canonical dictionary of a profile's rules (for result metadata)."""
    return {
        "reference": profile.reference,
        "summation": profile.summation,
        "ema": None if profile.ema is None else dict(vars(profile.ema)),
        "rsi": None if profile.rsi is None else dict(vars(profile.rsi)),
        "atr": None if profile.atr is None else dict(vars(profile.atr)),
        "adx": None if profile.adx is None else dict(vars(profile.adx)),
        "macd": profile.macd,
        "min_lookback": profile.min_lookback,
        "source": dict(profile.source),
    }


__all__ = [
    "RECOMMENDED_PROFILE",
    "SCHEMA",
    "AdxRule",
    "AtrRule",
    "EmaRule",
    "IndicatorProfile",
    "RsiRule",
    "available_profiles",
    "fingerprint",
    "load_profile",
    "profile_document",
    "profile_from_dict",
]
