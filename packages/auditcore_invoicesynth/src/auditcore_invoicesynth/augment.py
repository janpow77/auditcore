"""Prozedurales Scanrauschen mit Pillow (Extra ``render``), vollständig seed-bestimmt.

Drehung ±3°, leichte Perspektive, Unschärfe, JPEG-Artefakte, Salz-und-Pfeffer,
Graustufe/Binarisierung, Stempel, Kugelschreiber-Striche, Lochung und
Faltkante. Keine fremden Foto- oder Texturdaten; nur Zufallszahlen aus dem
übergebenen Seed (``random.Random``), keine globalen Zufallsquellen.
"""

from __future__ import annotations

import io
from random import Random
from types import ModuleType
from typing import TYPE_CHECKING, Any

from auditcore_invoicesynth.plan import AugmentSpec
from auditcore_invoicesynth.render import _pil

if TYPE_CHECKING:  # pragma: no cover
    from PIL.Image import Image

STAMP_TEXTS = ("EINGEGANGEN", "GEBUCHT", "GEPRÜFT", "BEZAHLT", "KOPIE")


def _stamp(image: Image, rng: Random, image_draw: ModuleType, font: Any) -> None:
    width, height = image.size
    draw = image_draw.Draw(image)
    cx = rng.randint(int(width * 0.55), int(width * 0.85))
    cy = rng.randint(int(height * 0.08), int(height * 0.3))
    w, h = int(width * 0.18), int(height * 0.035)
    color = rng.choice(((180, 30, 30), (30, 60, 170), (30, 120, 60)))
    draw.rectangle([cx - w, cy - h, cx + w, cy + h], outline=color, width=max(2, width // 400))
    draw.text((cx, cy), rng.choice(STAMP_TEXTS), fill=color, font=font, anchor="mm")


def _strokes(image: Image, rng: Random, count: int, image_draw: ModuleType) -> None:
    width, height = image.size
    draw = image_draw.Draw(image)
    for _ in range(count):
        x, y = rng.randint(0, width), rng.randint(int(height * 0.3), height)
        points = [(x, y)]
        for _ in range(rng.randint(3, 7)):
            x += rng.randint(-width // 12, width // 12)
            y += rng.randint(-height // 60, height // 60)
            points.append((x, y))
        draw.line(points, fill=(20, 40, 150), width=max(1, width // 500), joint="curve")


def _holes(image: Image, rng: Random, image_draw: ModuleType) -> None:
    width, height = image.size
    draw = image_draw.Draw(image)
    radius = max(3, width // 80)
    x = int(width * 0.04)
    for y in (int(height * 0.35), int(height * 0.65)):
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(70, 70, 70))


def _fold(image: Image, rng: Random, image_draw: ModuleType) -> None:
    width, height = image.size
    draw = image_draw.Draw(image)
    y = int(height * rng.choice((0.333, 0.5, 0.667)))
    draw.line([(0, y), (width, y + rng.randint(-3, 3))], fill=(200, 200, 200), width=2)


def _salt_pepper(image: Any, rng: Random, share: float) -> None:
    width, height = image.size
    pixels = image.load()
    black = (0,) * len(image.getbands())
    white = (255,) * len(image.getbands())
    for _ in range(int(width * height * share)):
        x, y = rng.randrange(width), rng.randrange(height)
        value = black if rng.random() < 0.5 else white
        pixels[x, y] = value if len(value) > 1 else value[0]


def augment_page(image: Image, spec: AugmentSpec, seed: int, *, stamp_font: Any = None) -> Image:
    """Seitenbild verrauschen; gleiche Eingabe + Seed → gleiches Bild."""
    image_mod, image_draw, _ = _pil()
    from PIL import ImageFilter

    rng = Random(seed)
    result = image.convert("RGB")
    _paper_marks(result, rng, spec, image_draw, stamp_font)
    if spec.perspective:
        result = _perspective(result, rng, spec.perspective, image_mod)
    if spec.rotation_deg:
        result = result.rotate(
            spec.rotation_deg,
            resample=image_mod.Resampling.BICUBIC,
            expand=False,
            fillcolor=(255, 255, 255),
        )
    if spec.blur_radius:
        result = result.filter(ImageFilter.GaussianBlur(spec.blur_radius))
    if spec.mode in {"gray", "binary"}:
        result = _gray(result, rng, binary=spec.mode == "binary")
    if spec.salt_pepper:
        _salt_pepper(result, rng, spec.salt_pepper)
    if spec.jpeg_quality is not None:
        result = _jpeg(result, spec.jpeg_quality, image_mod)
    return result


def _paper_marks(
    image: Image, rng: Random, spec: AugmentSpec, image_draw: ModuleType, stamp_font: Any
) -> None:
    """Stempel, Striche, Lochung und Faltkante in fester Reihenfolge (Zufallsfolge!)."""
    if spec.stamp and stamp_font is not None:
        _stamp(image, rng, image_draw, stamp_font)
    if spec.pen_strokes:
        _strokes(image, rng, spec.pen_strokes, image_draw)
    if spec.punch_holes:
        _holes(image, rng, image_draw)
    if spec.fold:
        _fold(image, rng, image_draw)


def _perspective(image: Image, rng: Random, strength: float, image_mod: ModuleType) -> Image:
    width, height = image.size
    g = strength / width * rng.choice((1, -1))
    h = strength / height * rng.choice((1, -1))
    return image.transform(
        image.size,
        image_mod.Transform.PERSPECTIVE,
        (1, 0, 0, 0, 1, 0, g, h),
        resample=image_mod.Resampling.BILINEAR,
        fillcolor=(255, 255, 255),
    )


def _gray(image: Image, rng: Random, *, binary: bool) -> Image:
    result = image.convert("L")
    if binary:
        threshold = rng.randint(150, 200)
        result = result.point(lambda v: 255 if v > threshold else 0)
    return result


def _jpeg(image: Image, quality: int, image_mod: ModuleType) -> Image:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    result: Image = image_mod.open(buffer)
    result.load()
    return result
