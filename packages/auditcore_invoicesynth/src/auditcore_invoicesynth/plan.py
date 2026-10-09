"""Deterministischer Variantenplan und Aufteilung in Trainings-/Testsätze.

Aus Seed und Konfiguration entsteht eine vollständige Liste von
``SampleSpec``; derselbe Seed ergibt denselben Plan. Zwei Vorlagen und die
Holdout-Schriften kommen ausschließlich im Satz ``test_layout_holdout`` vor
(Layout-Holdout, Testsatz T2).
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from random import Random
from typing import Any

from auditcore_invoicesynth.fonts import (
    DIAGNOSTIC_FONT_FAMILIES,
    V2_FONT_FAMILIES,
    V4_FONT_FAMILIES,
)
from auditcore_invoicesynth.formats import AMOUNT_STYLES, CURRENCY_STYLES, DATE_STYLES
from auditcore_invoicesynth.layouts import HOLDOUT_LAYOUTS, LAYOUTS, V2_LAYOUTS, available_layouts
from auditcore_invoicesynth.variety import VARIETIES

SPLITS = ("train", "validation", "test_synthetic", "test_layout_holdout")
DE_SCHEMES = ("de_19", "de_19", "de_19", "de_7", "de_mixed", "de_mixed", "de_reverse_charge")
AT_SCHEMES = ("at_20", "at_20", "at_13", "at_10", "at_mixed")


@dataclass(frozen=True)
class AugmentSpec:
    """Scanrauschen; alle Werte vorab gezogen, damit der Plan vollständig ist."""

    rotation_deg: float
    perspective: float
    blur_radius: float
    jpeg_quality: int | None
    salt_pepper: float
    mode: str
    stamp: bool
    pen_strokes: int
    punch_holes: bool
    fold: bool


@dataclass(frozen=True)
class DegradeSpec:
    """Seltene starke Verschlechterung (Variante ``v2``): niedrige Auflösung, Unschärfe, JPEG.

    ``scale`` verkleinert das Seitenbild und vergrößert es wieder (bei 300 dpi
    und ``scale=0.5`` entspricht das einem 150-dpi-Scan).
    """

    scale: float
    blur_radius: float
    jpeg_quality: int | None


@dataclass(frozen=True)
class SampleSpec:
    sample_id: str
    split: str
    index: int
    country: str
    layout: str
    language: str
    font_family: str
    font_size_pt: float
    amount_style: str
    currency_style: str
    date_style: str
    rate_variant: int
    vat_scheme: str
    kind: str
    errors: tuple[str, ...]
    iban_grouped: bool
    dpi: int
    augment: AugmentSpec | None
    seed: int
    variety: str = "v1"
    degrade: DegradeSpec | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["errors"] = list(self.errors)
        if self.variety == "v1":
            # Planprüfsummen der Variante v1 bleiben wie vor Einführung von v2.
            del data["variety"], data["degrade"]
        return data


@dataclass(frozen=True)
class SynthConfig:
    seed: int = 42
    base_date: date = date(2026, 1, 15)
    counts: dict[str, int] = field(
        default_factory=lambda: {
            "train": 1600,
            "validation": 150,
            "test_synthetic": 150,
            "test_layout_holdout": 100,
        }
    )
    dpi_choices: tuple[int, ...] = (150, 200, 300)
    english_share: float = 0.10
    austria_share: float = 0.20
    error_share: float = 0.10
    augment_share: float = 0.85
    holdout_layouts: tuple[str, ...] = HOLDOUT_LAYOUTS
    holdout_font_families: tuple[str, ...] = ("DejaVu Serif",)
    variety: str = "v1"
    degrade_share: float = 0.12
    v2_layout_share: float = 0.18

    def validate(self) -> None:
        if self.variety not in VARIETIES:
            raise ValueError(f"Generatorvariante nur {VARIETIES}")
        if set(self.counts) - set(SPLITS) or any(v < 0 for v in self.counts.values()):
            raise ValueError(f"Aufteilung nur für {SPLITS} mit nichtnegativer Anzahl")
        if not set(self.holdout_layouts) <= set(LAYOUTS) or len(self.holdout_layouts) < 1:
            raise ValueError("Holdout-Vorlagen müssen bekannte Vorlagen sein")
        if len(set(LAYOUTS) - set(self.holdout_layouts)) < 1:
            raise ValueError("Mindestens eine Trainingsvorlage erforderlich")
        if not self.dpi_choices or any(d < 50 or d > 600 for d in self.dpi_choices):
            raise ValueError("Auflösung zwischen 50 und 600 dpi")
        shares = (self.english_share, self.austria_share, self.error_share, self.augment_share)
        for share in (*shares, self.degrade_share, self.v2_layout_share):
            if not 0.0 <= share <= 1.0:
                raise ValueError("Anteile zwischen 0 und 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["base_date"] = self.base_date.isoformat()
        return data


def sample_seed(seed: int, sample_id: str) -> int:
    """Stabiler Einzelseed je Beleg, unabhängig von der Planreihenfolge."""
    digest = hashlib.sha256(f"{seed}:{sample_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _augment(rng: Random) -> AugmentSpec:
    return AugmentSpec(
        rotation_deg=round(rng.uniform(-3.0, 3.0), 2),
        perspective=round(rng.uniform(0.0, 0.015), 4) if rng.random() < 0.3 else 0.0,
        blur_radius=round(rng.uniform(0.3, 1.2), 2) if rng.random() < 0.4 else 0.0,
        jpeg_quality=rng.randint(35, 85) if rng.random() < 0.4 else None,
        salt_pepper=round(rng.uniform(0.0005, 0.004), 5) if rng.random() < 0.35 else 0.0,
        mode=rng.choice(("rgb", "gray", "gray", "binary")),
        stamp=rng.random() < 0.2,
        pen_strokes=rng.choice((0, 0, 0, 1, 2)),
        punch_holes=rng.random() < 0.2,
        fold=rng.random() < 0.15,
    )


DEGRADE_SALT = 0xDE6_0B02
# Vorlagen mit eigener Fachlogik im Plan (Land/Steuerschema bzw. Belegart) bleiben stehen.
FIXED_LAYOUTS = ("kleinunternehmer", "gutschrift")


def _degrade(rng: Random) -> DegradeSpec:
    return DegradeSpec(
        scale=round(rng.uniform(0.4, 0.7), 3),
        blur_radius=round(rng.uniform(0.3, 0.9), 2) if rng.random() < 0.6 else 0.0,
        jpeg_quality=rng.randint(30, 60) if rng.random() < 0.6 else None,
    )


V4_FONT_SALT = 0xF0_0B04
#: Anteil der ``v4``-Belege mit einer der zusätzlichen Ziffernschriften.
V4_FONT_SHARE = 0.30


def _v4_font(spec: SampleSpec, v4_fonts: tuple[str, ...]) -> str:
    """Schrift eines ``v4``-Belegs: eigene Zufallsfolge, sonst Schrift aus dem Plan."""
    rng = Random(spec.seed ^ V4_FONT_SALT)
    if v4_fonts and rng.random() < V4_FONT_SHARE:
        return rng.choice(v4_fonts)
    return spec.font_family


def _v4_pool(config: SynthConfig, font_families: tuple[str, ...]) -> tuple[str, ...]:
    """Verfügbare Zusatzschriften der Variante ``v4`` (nie eine Holdout-Schrift)."""
    return tuple(
        f for f in font_families if f in V4_FONT_FAMILIES and f not in config.holdout_font_families
    )


def _with_variety(
    spec: SampleSpec, config: SynthConfig, v4_fonts: tuple[str, ...] = ()
) -> SampleSpec:
    """Variante v2 außer im Layout-Holdout; dort bleibt T2 identisch zu v1."""
    if config.variety == "v1" or spec.split == "test_layout_holdout":
        return spec
    rng = Random(spec.seed ^ DEGRADE_SALT)
    degrade = _degrade(rng) if rng.random() < config.degrade_share else None
    layout = spec.layout
    if layout not in FIXED_LAYOUTS and rng.random() < config.v2_layout_share:
        layout = rng.choice(V2_LAYOUTS)
    font = _v4_font(spec, v4_fonts) if config.variety == "v4" else spec.font_family
    return replace(spec, layout=layout, variety=config.variety, degrade=degrade, font_family=font)


def _font_pools(
    config: SynthConfig, font_families: tuple[str, ...]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Schriften für Training und Layout-Holdout; v1 ohne die Familien aus v2.

    Diagnoseschriften (T2b) nur, wenn sie ausdrücklich Holdout-Schrift sind.
    """
    font_families = tuple(
        f
        for f in font_families
        if (f not in DIAGNOSTIC_FONT_FAMILIES or f in config.holdout_font_families)
        and f not in V4_FONT_FAMILIES
    )
    if config.variety == "v1":
        font_families = tuple(f for f in font_families if f not in V2_FONT_FAMILIES)
    if not font_families:
        raise ValueError("Keine freie Schrift verfügbar")
    holdout_fonts = tuple(f for f in config.holdout_font_families if f in font_families)
    train_fonts = tuple(f for f in font_families if f not in holdout_fonts) or font_families
    if not tuple(f for f in font_families if f not in holdout_fonts):
        holdout_fonts = ()
    return train_fonts, holdout_fonts


def plan_dataset(config: SynthConfig, font_families: tuple[str, ...]) -> list[SampleSpec]:
    """Vollständiger Plan; ``font_families`` sind die tatsächlich verfügbaren Familien."""
    config.validate()
    train_fonts, holdout_fonts = _font_pools(config, font_families)
    # Die Vorlagen aus v2 zieht erst ``_with_variety`` mit eigener Zufallsfolge, damit
    # Land, Generatorzähler und damit der Layout-Holdout gleich bleiben.
    train_layouts = tuple(
        name for name in available_layouts("v1") if name not in config.holdout_layouts
    )
    specs: list[SampleSpec] = []
    for split in SPLITS:
        for number in range(1, config.counts.get(split, 0) + 1):
            sample_id = f"{split}-{number:06d}"
            rng = Random(sample_seed(config.seed, sample_id))
            holdout = split == "test_layout_holdout"
            layout = rng.choice(config.holdout_layouts if holdout else train_layouts)
            country = "AT" if rng.random() < config.austria_share else "DE"
            language = "en" if rng.random() < config.english_share else "de"
            vat_scheme = rng.choice(AT_SCHEMES if country == "AT" else DE_SCHEMES)
            kind = "invoice"
            if layout == "kleinunternehmer":
                country, vat_scheme = "DE", "de_kleinunternehmer"
            elif layout == "gutschrift":
                kind = "credit_note"
            errors: tuple[str, ...] = ()
            if rng.random() < config.error_share:
                errors = (rng.choice(("wrong_total", "missing_vat_id", "missing_iban")),)
            families = holdout_fonts if holdout and holdout_fonts else train_fonts
            specs.append(
                SampleSpec(
                    sample_id=sample_id,
                    split=split,
                    index=len(specs) + 1,
                    country=country,
                    layout=layout,
                    language=language,
                    font_family=rng.choice(families),
                    font_size_pt=rng.choice((8.0, 9.0, 9.5, 10.0, 11.0, 12.0)),
                    amount_style=(
                        "en_grouped" if language == "en" else rng.choice(AMOUNT_STYLES[:3])
                    ),
                    currency_style=rng.choice(CURRENCY_STYLES),
                    date_style=(
                        rng.choice(("iso", "en_long"))
                        if language == "en"
                        else rng.choice(DATE_STYLES[:4])
                    ),
                    rate_variant=rng.randrange(3),
                    vat_scheme=vat_scheme,
                    kind=kind,
                    errors=errors,
                    iban_grouped=rng.random() < 0.7,
                    dpi=rng.choice(config.dpi_choices),
                    augment=_augment(rng) if rng.random() < config.augment_share else None,
                    seed=rng.getrandbits(63),
                )
            )
    v4_fonts = _v4_pool(config, font_families)
    return [_with_variety(spec, config, v4_fonts) for spec in specs]
