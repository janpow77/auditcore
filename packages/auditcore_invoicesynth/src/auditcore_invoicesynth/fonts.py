"""Freie Schriften aus Systempaketen oder geprüftem Download – nie eingebettet.

Zulässig sind nur Familien mit freier Lizenz (Katalog ``FONT_CATALOG``):
DejaVu (Bitstream-Vera-Lizenz), Liberation und Noto (SIL OFL 1.1). Die
Schriftdateien werden **nicht** mit dem Paket verteilt; der Generator sucht
sie in Systemverzeichnissen (``fonts-dejavu-core``, ``fonts-liberation2``,
``fonts-noto-core``) oder lädt sie über einen injizierten Abruf mit fester
SHA-256-Prüfsumme. Name, Datei, Lizenz und SHA-256 jeder verwendeten Datei
stehen im Datensatz-Manifest; optionale Prüfsummen-Pins verhindern stille
Schriftwechsel.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_FONT_DIRS: tuple[Path, ...] = (
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
    Path.home() / ".local/share/fonts",
)


@dataclass(frozen=True)
class FontFamilySpec:
    license: str
    debian_packages: tuple[str, ...]
    regular: tuple[str, ...]
    bold: tuple[str, ...]


FONT_CATALOG: dict[str, FontFamilySpec] = {
    "DejaVu Sans": FontFamilySpec(
        "Bitstream-Vera", ("fonts-dejavu-core",), ("DejaVuSans.ttf",), ("DejaVuSans-Bold.ttf",)
    ),
    "DejaVu Serif": FontFamilySpec(
        "Bitstream-Vera", ("fonts-dejavu-core",), ("DejaVuSerif.ttf",), ("DejaVuSerif-Bold.ttf",)
    ),
    "DejaVu Sans Mono": FontFamilySpec(
        "Bitstream-Vera",
        ("fonts-dejavu-core",),
        ("DejaVuSansMono.ttf",),
        ("DejaVuSansMono-Bold.ttf",),
    ),
    "Liberation Sans": FontFamilySpec(
        "OFL-1.1",
        ("fonts-liberation2", "fonts-liberation"),
        ("LiberationSans-Regular.ttf",),
        ("LiberationSans-Bold.ttf",),
    ),
    "Liberation Serif": FontFamilySpec(
        "OFL-1.1",
        ("fonts-liberation2", "fonts-liberation"),
        ("LiberationSerif-Regular.ttf",),
        ("LiberationSerif-Bold.ttf",),
    ),
    "Liberation Mono": FontFamilySpec(
        "OFL-1.1",
        ("fonts-liberation2", "fonts-liberation"),
        ("LiberationMono-Regular.ttf",),
        ("LiberationMono-Bold.ttf",),
    ),
    "Noto Sans": FontFamilySpec(
        "OFL-1.1", ("fonts-noto-core",), ("NotoSans-Regular.ttf",), ("NotoSans-Bold.ttf",)
    ),
    "Noto Serif": FontFamilySpec(
        "OFL-1.1", ("fonts-noto-core",), ("NotoSerif-Regular.ttf",), ("NotoSerif-Bold.ttf",)
    ),
}


class FontError(ValueError):
    """Schrift fehlt, ist nicht frei lizenziert oder weicht von der Prüfsumme ab."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ResolvedFont:
    family: str
    style: str
    path: Path
    sha256: str
    license: str

    def describe(self) -> dict[str, str]:
        """Manifestzeile ohne rechnerspezifischen Pfad."""
        return {
            "family": self.family,
            "style": self.style,
            "file": self.path.name,
            "sha256": self.sha256,
            "license": self.license,
            "debian_packages": ", ".join(FONT_CATALOG[self.family].debian_packages),
        }


@dataclass(frozen=True)
class FontSet:
    """Gefundene Familien mit normaler und fetter Datei."""

    fonts: tuple[ResolvedFont, ...]

    @property
    def families(self) -> tuple[str, ...]:
        regular = {f.family for f in self.fonts if f.style == "regular"}
        bold = {f.family for f in self.fonts if f.style == "bold"}
        return tuple(name for name in FONT_CATALOG if name in regular & bold)

    def path(self, family: str, style: str) -> Path:
        for font in self.fonts:
            if font.family == family and font.style == style:
                return font.path
        raise FontError(f"Schrift nicht verfügbar: {family} ({style})")

    def describe(self, families: Iterable[str] | None = None) -> list[dict[str, str]]:
        wanted = set(self.families if families is None else families)
        return [f.describe() for f in self.fonts if f.family in wanted]


def discover_fonts(
    search_dirs: Iterable[Path] = DEFAULT_FONT_DIRS,
    *,
    pins: Mapping[str, str] | None = None,
    families: Iterable[str] | None = None,
) -> FontSet:
    """Katalogschriften in den Verzeichnissen suchen (erste Fundstelle in Pfadordnung).

    ``pins`` ordnet Dateinamen eine erwartete SHA-256 zu; Abweichung → ``FontError``.
    """
    wanted = list(FONT_CATALOG if families is None else families)
    unknown = [name for name in wanted if name not in FONT_CATALOG]
    if unknown:
        raise FontError(f"Nicht im Katalog freier Schriften: {unknown}")
    found: dict[str, Path] = {}
    names = {
        file_name
        for name in wanted
        for file_name in (*FONT_CATALOG[name].regular, *FONT_CATALOG[name].bold)
    }
    for directory in search_dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.ttf")):
            if path.name in names and path.name not in found and path.is_file():
                found[path.name] = path
    resolved: list[ResolvedFont] = []
    for name in wanted:
        spec = FONT_CATALOG[name]
        for style, candidates in (("regular", spec.regular), ("bold", spec.bold)):
            for candidate in candidates:
                if candidate in found:
                    digest = sha256_file(found[candidate])
                    expected = (pins or {}).get(candidate)
                    if expected is not None and expected != digest:
                        raise FontError(f"Prüfsumme weicht ab: {candidate}")
                    resolved.append(
                        ResolvedFont(name, style, found[candidate], digest, spec.license)
                    )
                    break
    return FontSet(tuple(resolved))


def fetch_font(
    url: str,
    expected_sha256: str,
    destination: Path,
    fetch: Callable[[str], bytes],
) -> Path:
    """Schrift über den injizierten Abruf laden; nur bei passender SHA-256 speichern."""
    if destination.name not in {
        n for spec in FONT_CATALOG.values() for n in (*spec.regular, *spec.bold)
    }:
        raise FontError(f"Dateiname nicht im Katalog freier Schriften: {destination.name}")
    data = fetch(url)
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise FontError(f"Prüfsumme des Downloads weicht ab: {destination.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".font-")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.replace(temporary, destination)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return destination


def font_report(fonts: FontSet) -> dict[str, Any]:
    """Übersicht für CLI und Manifest."""
    return {
        "families": list(fonts.families),
        "missing": [name for name in FONT_CATALOG if name not in fonts.families],
        "files": fonts.describe(),
    }
